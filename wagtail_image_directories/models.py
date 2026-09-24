import os
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from wagtail.images.models import AbstractImage, Image
from wagtail.models import Collection


class ImageDirectory(models.Model):
    year = models.CharField(max_length=50, db_index=True, verbose_name=_("Root directory"))
    slug = models.SlugField(blank=True, max_length=255, db_index=True, verbose_name=_("Sub-directory (slug)"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["year", "slug"], name="unique_image_directory"),
        ]
        indexes = [models.Index(fields=["year", "slug"])]
        ordering = ["-year", "slug"]
        verbose_name = _("Image directory")
        verbose_name_plural = _("Image directories")

    def __str__(self):
        return f"{self.year}/{self.slug}" if self.slug else str(self.year)


class AbstractDirectoryImage(AbstractImage):
    year = models.CharField(max_length=50, default="misc", db_index=True, verbose_name=_("Root directory"))
    slug = models.SlugField(blank=True, max_length=255, db_index=True, verbose_name=_("Sub-directory (slug)"))

    admin_form_fields = Image.admin_form_fields + ("year", "slug")

    @property
    def directory_display(self):
        return f"{self.year}/{self.slug}" if self.slug else str(self.year)

    def get_or_create_collection(self):
        root_collection = Collection.get_first_root_node()
        year_name = str(self.year)
        year_collection = None

        for child in root_collection.get_children():
            if child.name == year_name:
                year_collection = child
                break

        if not year_collection:
            year_collection = root_collection.add_child(name=year_name)

        if self.slug:
            slug_collection = None
            for child in year_collection.get_children():
                if child.name == self.slug:
                    slug_collection = child
                    break
            if not slug_collection:
                slug_collection = year_collection.add_child(name=self.slug)
            return slug_collection

        return year_collection

    def get_file_size(self):
        if self.file:
            try:
                return self.file.size
            except (OSError, ValueError, FileNotFoundError):
                return 0
        return 0

    def _sanitize_folder(self, name):
        safe = slugify(str(name), allow_unicode=True)
        return safe or "misc"

    def get_upload_to(self, filename):
        root = self._sanitize_folder(self.year)
        sub = self._sanitize_folder(self.slug) if self.slug else ""
        parts = ["images", root] + ([sub] if sub else [])
        return os.path.join(*parts, filename)

    def save(self, *args, **kwargs):
        if not self.collection_id or self.collection == Collection.get_first_root_node():
            self.collection = self.get_or_create_collection()

        if self.file and not self.file_size:
            self.file_size = self.get_file_size()

        super().save(*args, **kwargs)
        ImageDirectory.objects.get_or_create(year=str(self.year), slug=self.slug or "")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["year", "slug"]),
            models.Index(fields=["year", "-created_at"]),
            models.Index(fields=["year", "slug", "-created_at"]),
        ]
