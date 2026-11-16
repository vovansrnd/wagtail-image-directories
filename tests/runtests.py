#!/usr/bin/env python
"""Д67-А: интеграционные тесты wagtail-image-directories против WHEEL-установки.

Гарантирует, что пакет импортируется из site-packages, а не из исходников:
runtests падает, если wagtail_image_directories импортирован из каталога
репозитория.

    python tests/runtests.py
"""
import os
import sys

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_tests_dir = os.path.dirname(os.path.abspath(__file__))
for _p in (_tests_dir, _repo_root):
    if _p not in sys.path:
        sys.path.append(_p)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

import django  # noqa: E402

django.setup()

import wagtail_image_directories  # noqa: E402

_pkg = wagtail_image_directories.__file__.replace(os.sep, "/")
if "site-packages" not in _pkg:
    sys.exit(f"ОШИБКА: импортирован НЕ wheel: {_pkg}")
print("проверяемый пакет (wheel):", _pkg)

import django.conf  # noqa: E402
from django.test.utils import get_runner  # noqa: E402

runner = get_runner(django.conf.settings)(interactive=False, verbosity=1)
# Оба набора: интеграционные операции + unit-тесты сканера
failures = runner.run_tests(["tests.test_safety", "tests.test_references_utils"])
sys.exit(bool(failures))
