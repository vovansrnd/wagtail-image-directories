"""Настройки интеграционных тестов wagtail-image-directories (sqlite, tmp media)."""
import tempfile

import os

SECRET_KEY = "d67-release-audit"
DEBUG = True
USE_TZ = True
ALLOWED_HOSTS = ["*"]
MEDIA_ROOT = tempfile.mkdtemp(prefix="wid-audit-media-")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "taggit",
    "wagtail",
    "wagtail.admin",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.contrib.forms",
    "tests.testapp",
    "wagtail_image_directories",
]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
# Тестовая БД: PostgreSQL по умолчанию (на sqlite in-memory Wagtail 6.4/8.1
# демонстрировал исчезновение строки rendition из shared-memory таблицы —
# anomaly задокументирована в досье Д68-Т/D67-А); переопределяется TEST_DB_* env.
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("TEST_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("TEST_DB_NAME", "d67imgtest"),
        "USER": os.environ.get("TEST_DB_USER", "a1020391_django_radio"),
        "PASSWORD": os.environ.get("TEST_DB_PASSWORD", ""),
        "HOST": os.environ.get("TEST_DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("TEST_DB_PORT", "5432"),
    }
}
ROOT_URLCONF = "tests.urls"
STATIC_URL = "static/"
WAGTAILIMAGES_IMAGE_MODEL = "testapp.DirectoryTestImage"
WAGTAIL_IMAGE_DIRECTORIES_MOVE_FILES = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
