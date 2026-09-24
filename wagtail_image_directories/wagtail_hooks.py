# wagtail_image_directories/wagtail_hooks.py
from django.templatetags.static import static
from django.urls import include, path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from . import urls as media_urls


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path("image-directories/", include(media_urls, namespace="wagtail_image_directories")),
    ]


@hooks.register("register_admin_menu_item")
def register_image_navigator_menu_item():
    return MenuItem(
        _("Image Navigator"),
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
    """Присваивает год и слаг картинке перед сохранением, если они переданы."""
    year = request.POST.get("year") or request.GET.get("year")
    slug = request.POST.get("slug") or request.GET.get("slug")

    if year:
        image.year = str(year).strip()
    if slug is not None:
        image.slug = str(slug).strip()
