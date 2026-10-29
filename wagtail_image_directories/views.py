import logging
import os
import warnings

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Max, OuterRef, Subquery, Sum, Q, Exists
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from wagtail.images import get_image_model
from wagtail.images.permissions import permission_policy
from django.db import transaction



from .models import ImageDirectory

logger = logging.getLogger(__name__)


def _clean_year(value):
    """Keep the year folder filesystem- and URL-safe."""
    return slugify((value or "").strip(), allow_unicode=True) or "misc"


def _clean_slug(value):
    return slugify((value or "").strip(), allow_unicode=True)


def _folder_url(year, slug):
    base = reverse("wagtail_image_directories:filtered_images")
    return f"{base}?{urlencode({'year': year, 'slug': slug})}"


def _int_ids(raw_ids):
    ids = []
    for raw in raw_ids:
        try:
            ids.append(int(raw))
        except (TypeError, ValueError):
            continue
    return ids


def _images_user_can(user, action):
    """Queryset of images for which this user has the given Wagtail permission."""
    return permission_policy.instances_user_has_any_permission_for(user, [action])


def _visible_directories(user, year=None):
    """Directories containing images that the current user may choose.

    A correlated EXISTS stays in SQL, avoiding a Python materialization of all
    folder pairs and a potentially huge OR expression for large image libraries.
    """
    images = _images_user_can(user, "choose")
    if year is not None:
        images = images.filter(year=year)
    qs = ImageDirectory.objects.all()
    if year is not None:
        qs = qs.filter(year=year)
    return qs.filter(Exists(images.filter(year=OuterRef("year"), slug=OuterRef("slug"))))


def _validate_uploaded_images(files):
    """Reject oversized or invalid raster uploads before creating any Image rows."""
    max_size = int(getattr(settings, "WAGTAIL_IMAGE_DIRECTORIES_MAX_UPLOAD_SIZE", 50 * 1024 * 1024))
    max_count = int(getattr(settings, "WAGTAIL_IMAGE_DIRECTORIES_MAX_UPLOADS", 30))
    if len(files) > max_count:
        return f"За один раз можно загрузить не более {max_count} изображений."

    try:
        from PIL import Image as PILImage
        from PIL import UnidentifiedImageError
    except ImportError:
        logger.exception("Pillow is unavailable while validating image uploads")
        return "Проверка изображений недоступна на сервере."

    for upload in files:
        if upload.size > max_size:
            return f"Файл {upload.name!r} превышает лимит {max_size // (1024 * 1024)} МБ."
        try:
            upload.seek(0)
            with warnings.catch_warnings():
                # Pillow otherwise only warns about images with excessive pixel
                # counts; turning that warning into an error prevents bomb files
                # from proceeding to Wagtail's image processing pipeline.
                warnings.simplefilter("error", PILImage.DecompressionBombWarning)
                with PILImage.open(upload) as image:
                    max_pixels = int(getattr(
                        settings,
                        "WAGTAIL_IMAGE_DIRECTORIES_MAX_PIXELS",
                        PILImage.MAX_IMAGE_PIXELS or 89_478_485,
                    ))
                    if max_pixels > 0 and image.width * image.height > max_pixels:
                        upload.seek(0)
                        return f"Файл {upload.name!r} превышает лимит пикселей ({max_pixels:,})."
                    image.verify()
            upload.seek(0)
        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
            PILImage.DecompressionBombError,
            PILImage.DecompressionBombWarning,
        ):
            upload.seek(0)
            return f"Файл {upload.name!r} не является корректным поддерживаемым изображением."
        except Exception:
            upload.seek(0)
            logger.exception("Unexpected error validating uploaded image %s", upload.name)
            return f"Не удалось проверить файл {upload.name!r}."
    return None


@method_decorator(permission_required("wagtailimages.add_image"), name="dispatch")
class ImageNavigatorView(TemplateView):
    template_name = "wagtail_image_directories/directory_browser.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        Image = get_image_model()
        PLACEHOLDER_TITLE = "__placeholder__"

        visible_images = _images_user_can(self.request.user, "choose").exclude(title=PLACEHOLDER_TITLE)
        yearly_stats = list(
            visible_images.values("year")
            .annotate(total_count=Count("id"), total_size=Sum("file_size"))
            .order_by("-year")
        )
        years = [row["year"] for row in yearly_stats]
        tree = [
            {
                "year": row["year"],
                "total": row["total_count"] or 0,
                "total_size": row["total_size"] or 0,
            }
            for row in yearly_stats
        ]

        context.update({
            "directory_tree": tree,
            "total_images": visible_images.count(),
            "total_years": len(years),
            "total_directories": _visible_directories(self.request.user).count(),
        })
        return context


@permission_required("wagtailimages.add_image")
def year_directories_ajax(request, year):
    Image = get_image_model()
    PLACEHOLDER_TITLE = "__placeholder__"

    visible_images = _images_user_can(request.user, "choose")
    dirs = list(_visible_directories(request.user, year=year).order_by("slug"))

    latest_image_subquery = (
        visible_images.filter(year=year, slug=OuterRef("slug"))
        .exclude(title=PLACEHOLDER_TITLE)
        .order_by("-created_at")
        .values("id")[:1]
    )

    stats_qs = (
        visible_images.filter(year=year)
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
    samples_map = {img.id: img for img in visible_images.filter(id__in=sample_ids)}

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
        _images_user_can(request.user, "choose").filter(year=year, slug=slug)
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
        "total_count": paginator.count,
        "paginator": paginator,
    }
    return render(request, "wagtail_image_directories/filtered_list.html", context)


@require_POST
@permission_required("wagtailimages.add_image")
def create_directory(request):
    year = _clean_year(request.POST.get("year"))
    slug = _clean_slug(request.POST.get("slug"))

    if not year:
        return JsonResponse({"success": False, "error": "Корневая директория обязательна."}, status=400)

    ImageDirectory.objects.get_or_create(year=year, slug=slug)
    return JsonResponse({"success": True, "redirect_url": _folder_url(year, slug)})


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
    year = _clean_year(request.POST.get("year"))
    slug = _clean_slug(request.POST.get("slug"))
    files = request.FILES.getlist("files[]")

    if not all([year, slug is not None, files]):
        return JsonResponse({"success": False, "error": "Неполные данные."}, status=400)

    validation_error = _validate_uploaded_images(files)
    if validation_error:
        return JsonResponse({"success": False, "error": validation_error}, status=400)

    Image = get_image_model()
    probe = Image(title="__permission_check__", year=year, slug=slug)
    try:
        # Collection tree creation must roll back if this user is not permitted
        # to upload to the requested destination collection.
        with transaction.atomic():
            probe.collection = probe.get_or_create_collection()
            if not permission_policy.user_has_permission_for_instance(request.user, "add", probe):
                raise PermissionError
    except PermissionError:
        return JsonResponse({"success": False, "error": "Нет права загружать изображения в эту коллекцию."}, status=403)

    ImageDirectory.objects.get_or_create(year=year, slug=slug)
    created_images_html = []
    warnings = []

    # Формируем правильный обратный URL текущей папки!
    folder_url = _folder_url(year, slug)

    for f in files:
        image = Image(title=f.name, file=f, year=year, slug=slug)
        image.save()
        if not _physically_move_image_file(image) and getattr(settings, "WAGTAIL_IMAGE_DIRECTORIES_MOVE_FILES", True):
            warnings.append(f"Файл {f.name!r} сохранён, но физически переместить его в папку не удалось.")
        card_html = render_to_string(
            "wagtail_image_directories/_image_card.html",
            {
                "image": image,
                "request": request,
                "current_folder_url": folder_url, # <-- Передаем точный URL папки!
            },
        )
        created_images_html.append(card_html)

    return JsonResponse({"success": True, "cards": created_images_html, "warnings": warnings})


def _physically_move_image_file(image):
    """Move the original file without ever deleting the only valid copy first.

    The database field is updated to the new stored name before the old file is
    deleted. If the DB update fails, the new copy is cleaned up and the old
    path remains valid. A failure to delete the old copy after the DB commit
    leaves an orphan duplicate, not a broken image URL.
    """
    if not getattr(settings, "WAGTAIL_IMAGE_DIRECTORIES_MOVE_FILES", True):
        return False
    if not image.file:
        return False

    storage = image.file.storage
    old_name = image.file.name
    new_name = image.get_upload_to(os.path.basename(old_name))
    if old_name == new_name:
        return True

    stored_name = None
    try:
        with image.file.open("rb") as source:
            stored_name = storage.save(new_name, source)
        image.file = stored_name
        try:
            image.save(update_fields=["file"])
        except Exception:
            image.file = old_name
            try:
                storage.delete(stored_name)
            except Exception:
                logger.exception("Could not clean up failed image move target %s", stored_name)
            raise
        try:
            storage.delete(old_name)
        except Exception:
            # New DB reference is already valid; keep the duplicate rather than
            # reverting the database to a file that may already be gone.
            logger.exception("Could not delete old image after move: %s", old_name)
        return True
    except Exception:
        logger.exception("Could not physically move image file %s -> %s", old_name, new_name)
        return False


# Physical storage operations are deliberately scheduled only after the database
# transaction commits. Django cannot roll back a file move when a DB transaction
# fails, so performing it inline can leave a committed row pointing at a missing file.
def _schedule_physical_move(image):
    if not getattr(settings, "WAGTAIL_IMAGE_DIRECTORIES_MOVE_FILES", True):
        return
    Image = image.__class__
    image_id = image.pk

    def move_after_commit():
        try:
            current = Image.objects.get(pk=image_id)
        except Image.DoesNotExist:
            return
        _physically_move_image_file(current)

    transaction.on_commit(move_after_commit)


def _move_queryset_to_directory(images, dst_year, dst_slug, user):
    Image = get_image_model()
    probe = Image(title="__permission_check__", year=dst_year, slug=dst_slug)
    target_collection = probe.get_or_create_collection()
    probe.collection = target_collection
    if not permission_policy.user_has_permission_for_instance(user, "add", probe):
        raise PermissionError("Недостаточно прав для перемещения в целевую коллекцию.")

    moved = 0
    for image in images.iterator(chunk_size=200):
        image.year = dst_year
        image.slug = dst_slug
        image.collection = target_collection
        image.save()
        _schedule_physical_move(image)
        moved += 1
    return moved


def _move_images_between_dirs(src_year, src_slug, dst_year, dst_slug, user):
    Image = get_image_model()
    all_images = Image.objects.filter(year=src_year, slug=src_slug)
    allowed_images = _images_user_can(user, "change").filter(year=src_year, slug=src_slug)
    if all_images.count() != allowed_images.count():
        raise PermissionError("Недостаточно прав для всех изображений исходной папки.")
    return _move_queryset_to_directory(allowed_images, dst_year, dst_slug, user)


@require_POST
@permission_required("wagtailimages.change_image")
def rename_directory(request):
    src_year = _clean_year(request.POST.get("src_year"))
    src_slug = _clean_slug(request.POST.get("src_slug"))
    dst_year = _clean_year(request.POST.get("dst_year"))
    dst_slug = _clean_slug(request.POST.get("dst_slug"))

    if not src_year or not dst_year:
        return JsonResponse({"success": False, "error": "Корневая директория обязательна."}, status=400)

    if src_year == dst_year and (src_slug or "") == (dst_slug or ""):
        return JsonResponse({"success": False, "error": "Новое имя совпадает со старым."}, status=400)

    if ImageDirectory.objects.filter(year=dst_year, slug=dst_slug).exists():
        return JsonResponse({"success": False, "error": 'Целевая директория уже существует. Используйте "Слить".'}, status=400)

    try:
        with transaction.atomic():
            moved = _move_images_between_dirs(src_year, src_slug, dst_year, dst_slug, request.user)
            ImageDirectory.objects.get_or_create(year=dst_year, slug=dst_slug)
            ImageDirectory.objects.filter(year=src_year, slug=src_slug).exclude(year=dst_year, slug=dst_slug).delete()

        redirect_url = _folder_url(dst_year, dst_slug)
        return JsonResponse({
            "success": True,
            "moved": moved,
            "redirect_url": redirect_url,
            "message": f"Директория переименована. Перемещено: {moved}",
        })
    except PermissionError as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=403)
    except Exception:
        logger.exception("Error renaming directory %s/%s", src_year, src_slug)
        return JsonResponse(
            {"success": False, "error": "Внутренняя ошибка при переименовании."}, status=500
        )


@require_POST
@permission_required("wagtailimages.change_image")
def merge_directories(request):
    src_year = _clean_year(request.POST.get("src_year"))
    src_slug = _clean_slug(request.POST.get("src_slug"))
    dst_year = _clean_year(request.POST.get("dst_year"))
    dst_slug = _clean_slug(request.POST.get("dst_slug"))

    if not src_year or not dst_year:
        return JsonResponse({"success": False, "error": "Корневая директория обязательна."}, status=400)

    if src_year == dst_year and (src_slug or "") == (dst_slug or ""):
        return JsonResponse({"success": False, "error": "Нельзя слить директорию саму с собой."}, status=400)

    try:
        with transaction.atomic():
            ImageDirectory.objects.get_or_create(year=dst_year, slug=dst_slug)
            moved = _move_images_between_dirs(src_year, src_slug, dst_year, dst_slug, request.user)
            ImageDirectory.objects.filter(year=src_year, slug=src_slug).delete()

        redirect_url = _folder_url(dst_year, dst_slug)
        return JsonResponse({
            "success": True,
            "moved": moved,
            "redirect_url": redirect_url,
            "message": f"Директории слиты. Перемещено: {moved}",
        })
    except PermissionError as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=403)
    except Exception:
        logger.exception("Error merging directories %s/%s", src_year, src_slug)
        return JsonResponse(
            {"success": False, "error": "Внутренняя ошибка при слиянии."}, status=500
        )


@permission_required("wagtailimages.add_image")
def directory_search(request):
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    results = []
    dirs = _visible_directories(request.user).filter(
        Q(slug__icontains=q) | Q(year__icontains=q)
    ).order_by("-year")[:15]

    for d in dirs:
        results.append({
            "label": f"{d.year}/{d.slug or 'без-категории'}",
            "url": _folder_url(d.year, d.slug),
        })

    return JsonResponse({"results": results})


# wagtail_image_directories/views.py

@require_POST
@permission_required("wagtailimages.delete_image")
def bulk_delete_images(request):
    """Массовое удаление картинок с удалением файлов с диска."""
    image_ids = list(dict.fromkeys(_int_ids(request.POST.getlist("ids[]"))))
    if not image_ids:
        return JsonResponse({"success": False, "error": "Изображения не выбраны"}, status=400)

    Image = get_image_model()
    requested_ids = set(image_ids)
    images = _images_user_can(request.user, "delete").filter(id__in=requested_ids)
    authorized_ids = set(images.values_list("id", flat=True))
    if authorized_ids != requested_ids:
        return JsonResponse({"success": False, "error": "Недостаточно прав для одного или нескольких изображений."}, status=403)
    count = images.count()

    for img in images.iterator(chunk_size=200):
        img.delete()

    return JsonResponse({"success": True, "message": f"Удалено изображений: {count}"})


@require_POST
@permission_required("wagtailimages.change_image")
def bulk_move_images(request):
    """Move selected images only when source and destination permissions allow it."""
    try:
        image_ids = list(dict.fromkeys(_int_ids(request.POST.getlist("ids[]"))))
        new_slug = _clean_slug(request.POST.get("slug"))
        new_year = _clean_year(request.POST.get("year"))

        if not image_ids or not new_year:
            return JsonResponse({"success": False, "error": "Неполные данные для перемещения"}, status=400)

        Image = get_image_model()
        requested_ids = set(image_ids)
        all_selected = Image.objects.filter(id__in=requested_ids)
        images = _images_user_can(request.user, "change").filter(id__in=requested_ids)
        if set(images.values_list("id", flat=True)) != requested_ids or all_selected.count() != len(requested_ids):
            return JsonResponse({"success": False, "error": "Недостаточно прав для одного или нескольких изображений."}, status=403)

        with transaction.atomic():
            ImageDirectory.objects.get_or_create(year=new_year, slug=new_slug)
            moved_count = _move_queryset_to_directory(images, new_year, new_slug, request.user)

        return JsonResponse({"success": True, "message": f"Перемещено изображений: {moved_count}"})
    except PermissionError as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=403)
    except Exception:
        logger.exception("Ошибка при перемещении картинок")
        return JsonResponse(
            {"success": False, "error": "Внутренняя ошибка при перемещении."}, status=500
        )


@permission_required("wagtailimages.change_image")
def image_move_chooser(request):
    """HTML модального окна выбора папки для перемещения."""
    dirs = _visible_directories(request.user).order_by("-year", "slug").values_list("year", "slug")
    dir_tree = {}
    for year, slug in dirs:
        dir_tree.setdefault(year, []).append(slug or "")

    modal_html = render_to_string(
        "wagtail_image_directories/modals/image_move_chooser.html",
        {"dir_tree": dir_tree},
        request=request,
    )
    return JsonResponse({"html": modal_html, "step": "chooser"})
