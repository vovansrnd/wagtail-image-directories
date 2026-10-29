from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wagtail_image_directories", "0003_reconcile_slug_index"),
    ]

    operations = [
        migrations.AlterField(
            model_name="imagedirectory",
            name="slug",
            field=models.SlugField(
                allow_unicode=True,
                blank=True,
                db_index=True,
                max_length=255,
                verbose_name="Sub-directory (slug)",
            ),
        ),
    ]
