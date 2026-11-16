"""Минимальные модели для интеграционных тестов wagtail-image-directories.

DirectoryTestImage — конкретная модель изображения (как требует README:
WAGTAILIMAGES_IMAGE_MODEL указывает на подкласс AbstractDirectoryImage).
ScannerPage — страница с RichTextField, по которой сканер ссылок находит
rendition-URL в текущем контенте и в сохранённых ревизиях.
"""
from django.db import models
from wagtail.models import Page

from wagtail_image_directories.models import AbstractDirectoryImage


class DirectoryTestImage(AbstractDirectoryImage):
    """Конкретное изображение для тестов (year/slug наследуются)."""

    class Meta:
        app_label = "testapp"


class ScannerPage(Page):
    """Страница с rich-text телом — источник rendition-URL для сканера."""

    body = models.TextField(verbose_name="Body (rich text source)")

    class Meta:
        app_label = "testapp"


from wagtail.images.models import AbstractRendition  # noqa: E402


class DirectoryTestRendition(AbstractRendition):
    """Конкретная модель рендишена: Wagtail 5.2+ требует её от хоста
    (AbstractImage.get_rendition_model() разрешает её через обратную
    связь renditions)."""

    image = models.ForeignKey(
        DirectoryTestImage, related_name="renditions", on_delete=models.CASCADE)

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)
