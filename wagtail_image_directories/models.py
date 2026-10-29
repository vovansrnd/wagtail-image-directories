import posixpath
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from wagtail.images.models import AbstractImage, Image, WagtailImageField
from wagtail.models import Collection


def directory_image_upload_to(instance, filename):
    """Return the on-disk path for an image using its year/slug metadata.

    This function is wired to the inherited image ``file`` field below. Keeping
    it at module scope also makes it importable by Django migrations.
    """
    root = slugify(str(getattr(instance, "year", "") or "misc"), allow_unicode=True) or "misc"
    raw_slug = getattr(instance, "slug", "") or ""
    sub = slugify(str(raw_slug), allow_unicode=True) if raw_slug else ""
    parts = ["images", root] + ([sub] if sub else [])
    basename = posixpath.basename(str(filename).replace("\\", "/"))
    return posixpath.join(*parts, basename)


class ImageDirectory(models.Model):
    year = models.CharField(max_length=50, db_index=True, verbose_name=_("Root directory"))
    slug = models.SlugField(blank=True, max_length=255, db_index=True, allow_unicode=True, verbose_name=_("Sub-directory (slug)"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["year", "slug"], name="unique_image_directory"),
        ]
        ordering = ["-year", "slug"]
        verbose_name = _("Image directory")
        verbose_name_plural = _("Image directories")

    def __str__(self):
        return f"{self.year}/{self.slug}" if self.slug else str(self.year)


class AbstractDirectoryImage(AbstractImage):
    # Override Wagtail's default ``original_images/`` upload path. Without this
    # field override, ``get_upload_to`` below would only affect later moves from
    # the Image Navigator; uploads through other Wagtail endpoints would remain
    # in the default flat folder.
    file = WagtailImageField(
        upload_to=directory_image_upload_to,
        width_field="width",
        height_field="height",
        max_length=1024,
    )

    year = models.CharField(max_length=50, default="misc", db_index=True, verbose_name=_("Root directory"))
    slug = models.SlugField(blank=True, max_length=255, db_index=True, allow_unicode=True, verbose_name=_("Sub-directory (slug)"))

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
        """Compatibility helper used when relocating existing stored files."""
        return directory_image_upload_to(self, filename)

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
