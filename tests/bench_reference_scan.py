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

import tracemalloc  # noqa: E402

from PIL import Image as PILImage  # noqa: E402

from tests.testapp.models import DirectoryTestImage, ScannerPage  # noqa: E402
from wagtail.models import Page  # noqa: E402
from wagtail_image_directories.references import (  # noqa: E402
    build_image_file_target_index,
    find_referenced_images,
    scan_content_and_revision_references)

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

# Масштаб: 10 000 страниц (половина со ссылкой на rendition),
# 2 000 страниц с дополнительными ревизиями.
PAGES = int(os.environ.get("BENCH_PAGES", "10000"))
REVISION_PAGES = int(os.environ.get("BENCH_REVISION_PAGES", "2000"))
t0 = time.perf_counter()
for i in range(PAGES):
    body = (f'<p><img src="{rendition.url}"></p>' if i % 2 == 0
            else f"<p>страница {i}</p>")
    root.add_child(instance=ScannerPage(
        title=f"Bench {i}", slug=f"bench-{i}", body=body))
    if i % 1000 == 0:
        print(f"  страниц создано: {i}", flush=True)
for i, p in enumerate(ScannerPage.objects.filter(slug__startswith="bench-")
                      .order_by("pk")[:REVISION_PAGES]):
    p.body = f'<p><img src="{rendition.url}"></p><p>rev {i}</p>'
    p.save_revision()
create_s = time.perf_counter() - t0
print(f"создано {PAGES} страниц + {REVISION_PAGES} ревизий за {create_s:.1f}s",
      flush=True)

tracemalloc.start()
t0 = time.perf_counter()
counters = scan_content_and_revision_references(
    build_image_file_target_index({image.id}))
scan_s = time.perf_counter() - t0
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"СКАН (текущий контент + все ревизии): {scan_s:.2f}s; "
      f"просмотрено записей: {counters}; память: текущая {current / 1e6:.1f} MB, "
      f"пик {peak / 1e6:.1f} MB", flush=True)

t0 = time.perf_counter()
refs = find_referenced_images({image.id})
find_s = time.perf_counter() - t0
print(f"find_referenced_images: {find_s * 1000:.1f} ms; "
      f"ссылок на bench-изображение: {len(refs.get(image.id, []))}", flush=True)
print(f"ИТОГ: {PAGES} страниц, {REVISION_PAGES} ревизий: скан {scan_s:.2f}s, "
      f"память пик {peak / 1e6:.1f} MB", flush=True)
runner.teardown_databases(old_config)
