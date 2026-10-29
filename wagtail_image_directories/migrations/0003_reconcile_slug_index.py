# Reconcile the field index with the model and remove a duplicate composite index.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wagtail_image_directories", "0002_alter_imagedirectory_options_and_more"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="imagedirectory",
            name="wagtail_ima_year_4ee44a_idx",
        ),
        migrations.AlterField(
            model_name="imagedirectory",
            name="slug",
            field=models.SlugField(
                blank=True,
                db_index=True,
                max_length=255,
                verbose_name="Sub-directory (slug)",
            ),
        ),
    ]
