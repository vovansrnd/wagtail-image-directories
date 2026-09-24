# wagtail-image-directories

Organize your Wagtail CMS media files into structured `year/slug` directories on disk with an interactive visual Image Navigator and bulk-action file manager in the Wagtail admin.

## Features
- **Structured Storage**: Images are physically organized on disk as `media/images/{year}/{slug}/filename.ext`.
- **Image Navigator**: A dashboard grouped by root directories (years) with real-time statistics (file count, total size, last updated).
- **In-place Drag & Drop Upload**: Upload images directly into the targeted folder without page reloads.
- **Bulk Operations**: Select multiple images to move or delete with automatic disk cleanup.
- **Directory Management**: Create, rename, and merge directories right from the admin UI.

## Installation

```bash
pip install wagtail-image-directories
```

Add to `INSTALLED_APPS` in your `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "wagtail_image_directories",
    ...
]
```

### Configure your Custom Image Model

In your models file:

```python
from wagtail_image_directories.models import AbstractDirectoryImage
from wagtail.images.models import AbstractRendition

class CustomImage(AbstractDirectoryImage):
    pass

class CustomRendition(AbstractRendition):
    image = models.ForeignKey(CustomImage, on_delete=models.CASCADE, related_name="renditions")
    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)
```

Point Wagtail to your custom model in `settings.py`:

```python
WAGTAILIMAGES_IMAGE_MODEL = 'your_app.CustomImage'
```

Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Case Study & Background
Read the full story behind the migration and architecture on our blog: [Vs-Svet.ru](https://vs-svet.ru/) / [ZenWay.ru](https://zenway.ru/).

## Recommended Complementary Package
To enable seamless native image uploads directly inside your rich text editor with full directory awareness, check out our companion plugin:
👉 **[wagtail-prose-editor-images](https://github.com/vovansrnd/wagtail-prose-editor-images)**
