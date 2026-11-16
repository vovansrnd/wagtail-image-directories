#!/usr/bin/env python
"""Д67-А: замер стоимости полного сканирования ссылок на объёме ревизий.

Создаёт страницу и N ревизий с rendition-URL в теле, затем измеряет
find_referenced_images (скан текущего контента + ВСЕХ сохранённых ревизий).

    python tests/bench_reference_scan.py [N_ревизий]

Результаты записываются в stdout (для релизного отчёта).
"""
import os
import sys
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

N = int(sys.argv[1]) if len(sys.argv) > 1 else 150

from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402
from django.test.runner import DiscoverRunner  # noqa: E402

setup_test_environment()
runner = DiscoverRunner(interactive=False, verbosity=0)
old_config = runner.setup_databases()

from io import BytesIO  # noqa: E402

from PIL import Image as PILImage  # noqa: E402

from tests.testapp.models import DirectoryTestImage, ScannerPage  # noqa: E402
from wagtail.models import Page  # noqa: E402

buf = BytesIO()
PILImage.new("RGB", (32, 32), (5, 25, 45)).save(buf, format="JPEG")
image = DirectoryTestImage(
    title="Bench image",
    file=SimpleUploadedFile("bench.jpg", buf.getvalue(), content_type="image/jpeg"),
    year="2026", slug="bench")
image.save()
rendition = image.get_rendition("width-800")

root = Page.get_first_root_node()
page = root.add_child(instance=ScannerPage(
    title="Bench page", slug="bench-page",
    body=f'<p><img src="{rendition.url}"></p>'))
page.save_revision()

t0 = time.perf_counter()
for i in range(N):
    page.body = f"<p><img src=\"{rendition.url}\"></p><p>ревизия {i}</p>"
    page.save_revision()
save_s = time.perf_counter() - t0
print(f"создано {N} ревизий за {save_s:.2f}s")

from wagtail_image_directories.references import find_referenced_images  # noqa: E402

times = []
for attempt in range(3):
    t0 = time.perf_counter()
    refs = find_referenced_images({image.id})
    dt = time.perf_counter() - t0
    times.append(dt)
    print(f"скан #{attempt + 1}: {dt * 1000:.1f} ms "
          f"(ссылок на изображение: {len(refs.get(image.id, []))})")
best = min(times)
print(f"ИТОГ: полный скан (текущий контент + {N} ревизий): {best * 1000:.1f} ms "
      f"(лучший из 3 прогонов)")
runner.teardown_databases(old_config)
