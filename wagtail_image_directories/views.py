import logging
from django.contrib.auth.decorators import permission_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Max, OuterRef, Subquery, Sum, Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from wagtail.images import get_image_model
from django.db import transaction



from .models import ImageDirectory

logger = logging.getLogger(__name__)


@method_decorator(permission_required("wagtailimages.add_image"), name="dispatch")
class ImageNavigatorView(TemplateView):
    template_name = "wagtail_image_directories/directory_browser.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        Image = get_image_model()
        PLACEHOLDER_TITLE = "__placeholder__"

        years = ImageDirectory.objects.values_list("year", flat=True).distinct().order_by("-year")

        tree = []
        for year_str in years:
            stats = Image.objects.filter(year=year_str).exclude(title=PLACEHOLDER_TITLE).aggregate(
                total_count=Count("id"),
                total_size=Sum("file_size")
            )
            tree.append({
                "year": year_str,
                "total": stats["total_count"] or 0,
                "total_size": stats["total_size"] or 0,
            })

        context.update({
            "directory_tree": tree,
            "total_images": Image.objects.exclude(title=PLACEHOLDER_TITLE).count(),
            "total_years": len(years),
            "total_directories": ImageDirectory.objects.count(),
        })
        return context


@permission_required("wagtailimages.add_image")
def year_directories_ajax(request, year):
    Image = get_image_model()
    PLACEHOLDER_TITLE = "__placeholder__"

    dirs = list(ImageDirectory.objects.filter(year=year).order_by("slug"))

    latest_image_subquery = (
        Image.objects.filter(year=year, slug=OuterRef("slug"))
        .exclude(title=PLACEHOLDER_TITLE)
        .order_by("-created_at")
        .values("id")[:1]
    )

    stats_qs = (
        Image.objects.filter(year=year)
        .exclude(title=PLACEHOLDER_TITLE)
        .values("slug")
        .annotate(
            count=Count("id"),
            total_size=Sum("file_size"),
            last_modified=Max("created_at"),
            sample_id=Subquery(latest_image_subquery),
        )
    )
    stats_map = {s["slug"] or "": s for s in stats_qs}
    sample_ids = [s["sample_id"] for s in stats_map.values() if s.get("sample_id")]
    samples_map = {img.id: img for img in Image.objects.filter(id__in=sample_ids)}

    result_dirs = []
    for d in dirs:
        slug = d.slug or ""
        s = stats_map.get(slug, {})
        result_dirs.append({
            "slug": slug,
            "display_slug": slug or "без-категории",
            "count": s.get("count", 0),
            "sample": samples_map.get(s.get("sample_id")),
            "total_size": s.get("total_size", 0),
            "last_modified": s.get("last_modified"),
        })

    return render(
        request,
        "wagtail_image_directories/_directories_list.html",
        {"dirs": result_dirs, "year": year},
    )


@permission_required("wagtailimages.add_image")
def admin_filtered_images(request):
    year = request.GET.get("year")
    slug = request.GET.get("slug", "")

    if not year:
        return HttpResponseBadRequest("Missing required 'year' parameter.")

    Image = get_image_model()
    queryset = (
        Image.objects.filter(year=year, slug=slug)
        .select_related("collection")
        .order_by("-created_at")
    )

    paginator = Paginator(queryset, 50)
    page_number = request.GET.get("page")
    try:
        images_page = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        images_page = paginator.page(1)

    context = {
        "images": images_page,
        "year": year,
        "slug": slug,
        "total_count": queryset.count(),
        "paginator": paginator,
    }
    return render(request, "wagtail_image_directories/filtered_list.html", context)


@require_POST
@permission_required("wagtailimages.add_image")
def create_directory(request):
    year = (request.POST.get("year") or "").strip()
    slug = (request.POST.get("slug") or "").strip()

    if not year:
        return JsonResponse({"success": False, "error": "Корневая директория обязательна."}, status=400)

    ImageDirectory.objects.get_or_create(year=year, slug=slug)
    redirect_url = reverse("wagtail_image_directories:filtered_images") + f"?year={year}&slug={slug}"
    return JsonResponse({"success": True, "redirect_url": redirect_url})


@require_POST
@permission_required("wagtailimages.delete_image")
def delete_directory(request):
    year = (request.POST.get("year") or "").strip()
    slug = (request.POST.get("slug") or "").strip()

    Image = get_image_model()
    has_images = Image.objects.filter(year=year, slug=slug).exists()
    if has_images:
        return JsonResponse({"success": False, "error": "Директория не пуста."}, status=400)

    deleted, _ = ImageDirectory.objects.filter(year=year, slug=slug).delete()
    return JsonResponse({"success": bool(deleted)})


@require_POST
@permission_required("wagtailimages.add_image")
def ajax_upload_images(request):
    year = request.POST.get("year")
    slug = request.POST.get("slug")
    files = request.FILES.getlist("files[]")

    if not all([year, slug is not None, files]):
        return JsonResponse({"success": False, "error": "Неполные данные."}, status=400)

    ImageDirectory.objects.get_or_create(year=year, slug=slug)
    Image = get_image_model()
    created_images_html = []

    # Формируем правильный обратный URL текущей папки!
    folder_url = reverse("wagtail_image_directories:filtered_images") + f"?year={year}&slug={slug}"

    for f in files:
        image = Image(title=f.name, file=f, year=year, slug=slug)
        image.save()
        card_html = render_to_string(
            "wagtail_image_directories/_image_card.html",
            {
                "image": image,
                "request": request,
                "current_folder_url": folder_url, # <-- Передаем точный URL папки!
            },
        )
        created_images_html.append(card_html)

    return JsonResponse({"success": True, "cards": created_images_html})


# Вспомогательная функция переноса картинок между папками
def _move_images_between_dirs(src_year, src_slug, dst_year, dst_slug):
    Image = get_image_model()
    qs = Image.objects.filter(year=src_year, slug=src_slug)
    moved = 0
    for image in qs.iterator(chunk_size=200):
        image.year = dst_year
        image.slug = dst_slug
        if hasattr(image, "get_or_create_collection"):
            image.collection = image.get_or_create_collection()
        image.save()
        moved += 1
    return moved


@require_POST
@permission_required("wagtailimages.change_image")
def rename_directory(request):
    src_year = (request.POST.get("src_year") or "").strip()
    src_slug = (request.POST.get("src_slug") or "").strip()
    dst_year = (request.POST.get("dst_year") or "").strip()
    dst_slug = (request.POST.get("dst_slug") or "").strip()

    if not src_year or not dst_year:
        return JsonResponse({"success": False, "error": "Корневая директория обязательна."}, status=400)

    if src_year == dst_year and (src_slug or "") == (dst_slug or ""):
        return JsonResponse({"success": False, "error": "Новое имя совпадает со старым."}, status=400)

    if ImageDirectory.objects.filter(year=dst_year, slug=dst_slug).exists():
        return JsonResponse({"success": False, "error": 'Целевая директория уже существует. Используйте "Слить".'}, status=400)

    try:
        with transaction.atomic():
            moved = _move_images_between_dirs(src_year, src_slug, dst_year, dst_slug)
            ImageDirectory.objects.get_or_create(year=dst_year, slug=dst_slug)
            ImageDirectory.objects.filter(year=src_year, slug=src_slug).exclude(year=dst_year, slug=dst_slug).delete()

        redirect_url = reverse("wagtail_image_directories:filtered_images") + f"?year={dst_year}&slug={dst_slug}"
        return JsonResponse({
            "success": True,
            "moved": moved,
            "redirect_url": redirect_url,
            "message": f"Директория переименована. Перемещено: {moved}",
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
@permission_required("wagtailimages.change_image")
def merge_directories(request):
    src_year = (request.POST.get("src_year") or "").strip()
    src_slug = (request.POST.get("src_slug") or "").strip()
    dst_year = (request.POST.get("dst_year") or "").strip()
    dst_slug = (request.POST.get("dst_slug") or "").strip()

    if not src_year or not dst_year:
        return JsonResponse({"success": False, "error": "Корневая директория обязательна."}, status=400)

    if src_year == dst_year and (src_slug or "") == (dst_slug or ""):
        return JsonResponse({"success": False, "error": "Нельзя слить директорию саму с собой."}, status=400)

    try:
        with transaction.atomic():
            ImageDirectory.objects.get_or_create(year=dst_year, slug=dst_slug)
            moved = _move_images_between_dirs(src_year, src_slug, dst_year, dst_slug)
            ImageDirectory.objects.filter(year=src_year, slug=src_slug).delete()

        redirect_url = reverse("wagtail_image_directories:filtered_images") + f"?year={dst_year}&slug={dst_slug}"
        return JsonResponse({
            "success": True,
            "moved": moved,
            "redirect_url": redirect_url,
            "message": f"Директории слиты. Перемещено: {moved}",
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@permission_required("wagtailimages.add_image")
def directory_search(request):
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    results = []
    dirs = ImageDirectory.objects.filter(
        Q(slug__icontains=q) | Q(year__icontains=q)
    ).order_by("-year")[:15]

    for d in dirs:
        results.append({
            "label": f"{d.year}/{d.slug or 'без-категории'}",
            "url": reverse("wagtail_image_directories:filtered_images") + f"?year={d.year}&slug={d.slug}",
        })

    return JsonResponse({"results": results})


# wagtail_image_directories/views.py

@require_POST
@permission_required("wagtailimages.delete_image")
def bulk_delete_images(request):
    """Массовое удаление картинок с удалением файлов с диска."""
    image_ids = request.POST.getlist("ids[]")
    if not image_ids:
        return JsonResponse({"success": False, "error": "Изображения не выбраны"}, status=400)

    Image = get_image_model()
    images = Image.objects.filter(id__in=image_ids)
    count = images.count()

    for img in images.iterator(chunk_size=200):
        img.delete()

    return JsonResponse({"success": True, "message": f"Удалено изображений: {count}"})


@require_POST
@permission_required("wagtailimages.change_image")
def bulk_move_images(request):
    """Массовое перемещение картинок в другую директорию."""
    try:
        image_ids = request.POST.getlist("ids[]")
        new_slug = (request.POST.get("slug") or "").strip()
        new_year = (request.POST.get("year") or "").strip()

        if not image_ids or not new_year:
            return JsonResponse({"success": False, "error": "Неполные данные для перемещения"}, status=400)

        ImageDirectory.objects.get_or_create(year=new_year, slug=new_slug)

        Image = get_image_model()
        images = Image.objects.filter(id__in=image_ids)
        moved_count = 0
        for image in images:
            image.slug = new_slug
            image.year = new_year
            if hasattr(image, "get_or_create_collection"):
                image.collection = image.get_or_create_collection()
            image.save()
            moved_count += 1

        return JsonResponse({"success": True, "message": f"Перемещено изображений: {moved_count}"})
    except Exception as e:
        logger.exception("Ошибка при перемещении картинок")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@permission_required("wagtailimages.change_image")
def image_move_chooser(request):
    """HTML модального окна выбора папки для перемещения."""
    dirs = ImageDirectory.objects.order_by("-year", "slug").values_list("year", "slug")
    dir_tree = {}
    for year, slug in dirs:
        dir_tree.setdefault(year, []).append(slug or "")

    modal_html = render_to_string(
        "wagtail_image_directories/modals/image_move_chooser.html",
        {"dir_tree": dir_tree},
        request=request,
    )
    return JsonResponse({"html": modal_html, "step": "chooser"})
