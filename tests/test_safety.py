"""Д67-А: интеграционные тесты ФАКТИЧЕСКИХ операций wagtail-image-directories.

Не уровень API сканера, а реальные операции через view-эндпоинты:
- массовое удаление (bulk-delete): 409 по текущему контенту, 409 по
  сохранённой ревизии, фактическое удаление файла при отсутствии ссылок,
  503 fail-closed при отказе сканера;
- физическое перемещение (MOVE_FILES=True): изображение, на которое
  ссылается страница, НЕ перемещается (старый путь сохранён), неподссылочное
  перемещается физически.

Эти тесты complementуют unit-тесты сканера (test_references_utils.py)
и идут вместе с ними в релизный набор пакета.
"""
import os
from io import BytesIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image as PILImage

from tests.testapp.models import DirectoryTestImage, ScannerPage
from wagtail.models import Page


def _jpeg_bytes(color=(10, 30, 50), size=(16, 16)):
    buf = BytesIO()
    PILImage.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


class SafetyTestBase(TestCase):
    """Общая обстановка: superuser, страница с rendition-URL, изображения."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = get_user_model().objects.create_superuser(
            "safety-admin", "safety@example.test", "safety-pw-12345")

    def setUp(self):
        self.client.force_login(self.superuser)
        self.root = Page.get_first_root_node()
        self.image = DirectoryTestImage(
            title="Referenced image",
            file=SimpleUploadedFile("referenced.jpg", _jpeg_bytes(),
                                    content_type="image/jpeg"),
            year="2026", slug="src")
        self.image.save()
        self.rendition = self.image.get_rendition("width-800")
        self.page = self.root.add_child(instance=ScannerPage(
            title="Scanner page", slug="scanner-page",
            body=f'<p><img src="{self.rendition.url}"></p>'))
        self.page.save_revision()

    def _unreferenced_image(self, year="2026", slug="src"):
        img = DirectoryTestImage(
            title="Unreferenced image",
            file=SimpleUploadedFile("unreferenced.jpg", _jpeg_bytes((80, 10, 10)),
                                    content_type="image/jpeg"),
            year=year, slug=slug)
        img.save()
        return img


class BulkDeleteTests(SafetyTestBase):
    def _post_delete(self, image):
        return self.client.post(
            reverse("wagtail_image_directories:bulk_delete_images"),
            {"ids[]": [str(image.id)]})

    def test_bulk_delete_blocked_by_current_content_409(self):
        """Ссылка в текущем контенте страницы: 409, изображение не удалено."""
        response = self._post_delete(self.image)
        self.assertEqual(response.status_code, 409, response.content)
        data = response.json()
        self.assertIn(self.image.id, data["referenced_image_ids"])
        self.assertTrue(DirectoryTestImage.objects.filter(id=self.image.id).exists())

    def test_bulk_delete_blocked_by_saved_revision_409(self):
        """Ссылка осталась только в сохранённой ревизии: 409."""
        self.page.body = "<p>ссылка убрана из текущего контента</p>"
        self.page.save_revision()
        response = self._post_delete(self.image)
        self.assertEqual(response.status_code, 409, response.content)
        self.assertTrue(DirectoryTestImage.objects.filter(id=self.image.id).exists())

    def test_bulk_delete_unreferenced_succeeds(self):
        """Без ссылок: 200, строка изображения удалена.

        Жизненный цикл физического файла принадлежит Wagtail
        (современный Wagtail оставляет файл на диске после удаления
        строки — assert делаем только по строке)."""
        img = self._unreferenced_image()
        response = self._post_delete(img)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(DirectoryTestImage.objects.filter(id=img.id).exists(),
                         "строка изображения должна быть удалена")

    def test_bulk_delete_fails_closed_503(self):
        """Отказ сканера: 503 fail-closed, изображение не тронуто."""
        img = self._unreferenced_image()
        with mock.patch("wagtail_image_directories.views.find_referenced_images",
                        side_effect=RuntimeError("scanner down")):
            response = self._post_delete(img)
        self.assertEqual(response.status_code, 503, response.content)
        self.assertTrue(DirectoryTestImage.objects.filter(id=img.id).exists())


class PhysicalMoveTests(SafetyTestBase):
    """MOVE_FILES=True: защита ссылочных изображений при реальном переносе."""

    def _rename(self, dst_slug="dst"):
        return self.client.post(
            reverse("wagtail_image_directories:rename_directory"),
            {"src_year": "2026", "src_slug": "src",
             "dst_year": "2026", "dst_slug": dst_slug})

    @override_settings(WAGTAIL_IMAGE_DIRECTORIES_MOVE_FILES=True)
    def test_rename_moves_unreferenced_file_and_preserves_referenced(self):
        """Ссылочное изображение: файл остаётся на старом пути. Неподссылочное:
        физически переносится в новую директорию."""
        unreferenced = self._unreferenced_image()
        old_referenced_path = os.path.join(self.image.file.storage.location,
                                           self.image.file.name)
        old_unreferenced_path = os.path.join(unreferenced.file.storage.location,
                                             unreferenced.file.name)
        self.assertTrue(os.path.exists(old_referenced_path))
        self.assertTrue(os.path.exists(old_unreferenced_path))
        # Исходные имена файлов — база для проверки «путь в БД сохранён»
        referenced_original_name = self.image.file.name
        unreferenced_original_name = unreferenced.file.name

        # Физические переносы планируются через transaction.on_commit —
        # в TestCase исполняем колбэки явно.
        with self.captureOnCommitCallbacks(execute=True):
            response = self._rename()
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data["physical_moves_enabled"], True)
        self.assertGreaterEqual(data["physical_moves_skipped"], 1)

        # Ссылочное: старый путь сохранён, файл не перемещён.
        self.assertTrue(os.path.exists(old_referenced_path),
                        "файл ссылочного изображения не должен перемещаться")
        self.image.refresh_from_db()
        self.assertEqual(self.image.file.name, referenced_original_name,
                         "имя файла ссылочного изображения в БД должно "
                         "сохраниться (защита от перемещения)")
        # Неподссылочное: имя файла в БД изменилось на новую директорию
        # (сравнение с сохранённым исходным именем, не tautology), файл
        # физически на новом пути и отсутствует на старом.
        unreferenced.refresh_from_db()
        self.assertNotEqual(unreferenced.file.name, unreferenced_original_name)
        self.assertIn("/2026/dst/", unreferenced.file.name)
        new_unreferenced_path = os.path.join(unreferenced.file.storage.location,
                                             unreferenced.file.name)
        self.assertTrue(os.path.exists(new_unreferenced_path))
        self.assertFalse(os.path.exists(old_unreferenced_path))

    @override_settings(WAGTAIL_IMAGE_DIRECTORIES_MOVE_FILES=True)
    def test_rename_fails_closed_on_scanner_error(self):
        """Fail-closed при отказе сканера перед физическим переносом:
        операция отменена (500), БД-состояние и физические файлы
        сохранены в прежнем виде."""
        unreferenced = self._unreferenced_image()
        old_name = unreferenced.file.name
        old_path = os.path.join(unreferenced.file.storage.location, old_name)
        self.assertTrue(os.path.exists(old_path))

        with mock.patch("wagtail_image_directories.views.find_referenced_images",
                        side_effect=RuntimeError("scanner down")):
            response = self._rename()

        self.assertEqual(response.status_code, 500, response.content)
        # БД-состояние не изменилось: изображение осталось в исходной директории
        unreferenced.refresh_from_db()
        self.assertEqual(unreferenced.year, "2026")
        self.assertEqual(unreferenced.slug, "src")
        self.assertEqual(unreferenced.file.name, old_name)
        # Физический файл на месте
        self.assertTrue(os.path.exists(old_path))

    def test_rename_without_move_files_keeps_files_in_place(self):
        """MOVE_FILES=False (по умолчанию): физически ничего не переносится."""
        unreferenced = self._unreferenced_image()
        old_path = os.path.join(unreferenced.file.storage.location,
                                unreferenced.file.name)
        response = self._rename()
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data["physical_moves_enabled"], False)
        self.assertEqual(data["physical_moves_skipped"], 0)
        self.assertTrue(os.path.exists(old_path))
