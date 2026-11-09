# Changelog — wagtail-image-directories

All notable changes for this package are documented here. PyPI availability is tracked per release: entries below describe the package state at that version; publication happens separately once approved.

## [0.2.1] — 2026-11-09

- Lazy image permission policy: `policy_registry.get_by_type(get_image_model())`
  replaces the module-level `wagtail.images.permissions.permission_policy`
  import that Wagtail 8 deprecated (warning noise on worker start;
  forward-compatible with Wagtail 9).
- Version bumped because PyPI's 0.2.0 predates the fix (5170ece); the
  old wheel still works on Wagtail 8.1, this is prevention rather than
  a breakage fix.
- Rollback: `pip install wagtail-image-directories==0.2.0` (PyPI).
- Tested with: Wagtail 8.0.1/8.1, Django 6.0.9, Python 3.14.

## [0.2.0] — 2026-10-29

- Correct the real upload_to path for new originals; add a concrete storage-path migration; strengthen Collection permission checks and indexing; document rendition quotas and file-move risk.
- Expanded installation, security, troubleshooting, storage/integration and multi-language documentation.
- Added translated README files for English, Russian, German, Spanish, French, Italian, Brazilian Portuguese, Dutch, Polish, Turkish, Simplified Chinese, Japanese and Korean.
- Static syntax/packaging checks are included in the release bundle. Complete Django/Wagtail integration tests and live storage/permission checks remain a release gate.

## Previous releases

See the package's release history on PyPI and its source repository, where available.

## 2026-10-29 — follow-up audit

- Replaced large in-memory directory-pair/OR filters with correlated `Exists` queries.
- Aggregated image counts and sizes by year in one query, added pagination, and used database `file_size` plus bounded thumbnails in cards.
- Aligned upload path generation and Unicode slug validation; widened stored path length to 1024 characters with migrations.
- Added migration `0004_allow_unicode_directory_slug`. Existing files and renditions are not relocated or deleted automatically.
