from django.templatetags.static import static
from django.urls import include, path, reverse
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.http import HttpResponseRedirect

from .views import CustomImageCreateView
from . import urls as media_urls
from .models import AbstractDirectoryImage


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path("image-directories/", include(media_urls, namespace="wagtail_image_directories")),
    ]


@hooks.register("register_admin_menu_item")
def register_image_navigator_menu_item():
    return MenuItem(
        _("Image Navigator"), # Английский по умолчанию, переводится в gettext
        reverse("wagtail_image_directories:navigator"),
        icon_name="folder-open-inverse",
        order=250,
    )


@hooks.register("insert_global_admin_js")
def insert_navigator_js():
    return format_html(
        '<script src="{}" defer></script>\n'
        '<script src="{}" defer></script>\n'
        '<script src="{}" defer></script>',
        static("wagtail_image_directories/js/admin_images.js"),
        static("wagtail_image_directories/js/directory_search.js"),
        static("wagtail_image_directories/js/image_navigator.js"),
    )


@hooks.register("before_create_image")
def process_new_directory_image(request, image):
    # Берём параметры из GET или POST запроса
    year = request.POST.get("year") or request.GET.get("year")
    slug = request.POST.get("slug") or request.GET.get("slug")

    if year:
        image.year = str(year).strip()
    if slug is not None:
        image.slug = str(slug).strip()


@hooks.register("after_create_image")
def redirect_to_directory_after_add(request, image):
    # Если в URL был передан параметр next — возвращаемся по нему
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url:
        return HttpResponseRedirect(next_url)

    # Иначе возвращаемся в текущую папку
    if hasattr(image, "year") and image.year:
        return HttpResponseRedirect(
            reverse("wagtail_image_directories:filtered_images") + f"?year={image.year}&slug={image.slug}"
        )


@hooks.register("register_admin_urls")
def register_custom_add_image_url():
    return [
        # Подменяем роут добавления картинок Wagtail на наш умный класс
        path("images/add/", CustomImageCreateView.as_view(), name="wagtailimages_add_override"),
    ]


@hooks.register("before_delete_image")
def redirect_to_folder_on_delete(request, image):
    # Срабатывает только при подтверждении удаления (когда отправлен POST-запрос)
    if request.method == "POST":
        year = getattr(image, "year", None)
        slug = getattr(image, "slug", "") or ""

        # Удаляем объект вручную
        image.delete()

        # Формируем возврат в родную папку картинки
        if year:
            target_url = (
                reverse("wagtail_image_directories:filtered_images")
                + f"?year={year}&slug={slug}"
            )
            return HttpResponseRedirect(target_url)
