# Changelog — wagtail-image-directories

All notable changes for this package are documented here. Version numbers below are **prepared release candidates** in this audit bundle; they are not a claim that those versions have already been uploaded to PyPI.

## [0.2.0] — 2026-10-29 — prepared, not yet published

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
