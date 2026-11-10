import unittest

from wagtail_image_directories.references import (
    extract_url_paths,
    file_path_aliases,
    normalize_url_path,
    content_field_names_for_model,
)


class _FakeField:
    def __init__(self, name, internal_type="TextField", *, concrete=True, is_relation=False):
        self.name = name
        self._internal_type = internal_type
        self.concrete = concrete
        self.is_relation = is_relation

    def get_internal_type(self):
        return self._internal_type


class _FakeMeta:
    abstract = False
    proxy = False

    def __init__(self, fields):
        self.fields = fields

    def get_fields(self):
        return self.fields


class _FakePage:
    pass


class _FakeBlogPage(_FakePage):
    _meta = _FakeMeta([
        _FakeField("body"),
        _FakeField("hero_caption"),
        _FakeField("image_fk", "ForeignKey", is_relation=True),
        _FakeField("created_at", "DateTimeField"),
    ])


class _FakeForumPost:
    _meta = _FakeMeta([
        _FakeField("content"),
        _FakeField("author_name", "CharField"),
        _FakeField("updated_at", "DateTimeField"),
    ])


class _FakeComment:
    _meta = _FakeMeta([
        _FakeField("response"),
        _FakeField("moderator_note"),
    ])


class MediaReferenceUtilsTests(unittest.TestCase):
    def test_normalizes_absolute_url_and_ignores_query_and_fragment(self):
        self.assertEqual(
            normalize_url_path("https://cdn.example.test/media/images/2026/a.jpg?width=1200#x"),
            "/media/images/2026/a.jpg",
        )

    def test_relative_storage_name_gets_leading_slash(self):
        self.assertEqual(normalize_url_path("images/2026/a.jpg"), "/images/2026/a.jpg")

    def test_extracts_img_and_anchor_urls(self):
        html = (
            '<p><img src="/media/images/2026/a.width-1200.jpg?x=1" '
            'srcset="/media/images/2026/a.width-600.jpg 600w, '
            '/media/images/2026/a.width-1200.jpg 1200w"></p>'
            '<a href="https://cdn.example.test/media/images/2026/b.jpg">image</a>'
        )
        self.assertEqual(
            extract_url_paths(html),
            {
                "/media/images/2026/a.width-1200.jpg",
                "/media/images/2026/a.width-600.jpg",
                "/media/images/2026/b.jpg",
            },
        )

    def test_extracts_css_background_url(self):
        html = '<div style="background-image:url(\'/media/images/2026/a.jpg\')"></div>'
        self.assertEqual(extract_url_paths(html), {"/media/images/2026/a.jpg"})

    def test_builds_media_url_alias_for_storage_name(self):
        aliases = file_path_aliases(
            "images/2026/posts/a.jpg",
            file_url="https://cdn.example.test/media/images/2026/posts/a.jpg?sig=secret",
            media_url="https://cdn.example.test/media/",
        )
        self.assertIn("/media/images/2026/posts/a.jpg", aliases)
        self.assertIn("/images/2026/posts/a.jpg", aliases)

    def test_does_not_accept_empty_values(self):
        self.assertIsNone(normalize_url_path(None))
        self.assertIsNone(normalize_url_path(""))
        self.assertEqual(extract_url_paths(None), set())

    def test_all_text_fields_on_page_models_are_scanned(self):
        names, is_page = content_field_names_for_model(_FakeBlogPage, _FakePage)
        self.assertTrue(is_page)
        self.assertEqual(names, ["body", "hero_caption"])

    def test_non_page_rich_text_models_include_forum_and_comment_fields(self):
        forum_names, is_forum_page = content_field_names_for_model(_FakeForumPost, _FakePage)
        comment_names, is_comment_page = content_field_names_for_model(_FakeComment, _FakePage)
        self.assertFalse(is_forum_page)
        self.assertFalse(is_comment_page)
        self.assertEqual(forum_names, ["content"])
        self.assertEqual(comment_names, ["response"])


if __name__ == "__main__":
    unittest.main()
