"""Read-only discovery of Wagtail image references in content and revisions.

The helper deliberately does not delete, move, or rewrite anything. It maps
stored image/rendition URLs to their owning image IDs and scans current Page
content, common rich-text fields on other installed models, saved Wagtail
revisions, and concrete image relations for exact URL-path matches.
"""
from __future__ import annotations

from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlsplit
import posixpath
import re


_STYLE_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)


class _MediaURLCollector(HTMLParser):
    """Collect URL-bearing attributes without interpreting arbitrary text."""

    URL_ATTRIBUTES = {
        "src", "href", "poster", "data-src", "data-original",
        "data-image-url", "data-url",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []

    def _add(self, value):
        if value:
            value = str(value).strip()
            if value:
                self.urls.append(value)

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            name = (name or "").lower()
            if name in self.URL_ATTRIBUTES:
                self._add(value)
            elif name == "srcset" and value:
                # A srcset candidate is "URL [descriptor]". Split each
                # candidate once; data URLs are not expected for Wagtail media.
                for candidate in value.split(","):
                    candidate = candidate.strip()
                    if candidate:
                        self._add(candidate.split()[0])
            elif name == "style" and value:
                self.urls.extend(match.group(2).strip() for match in _STYLE_URL_RE.finditer(value))

    handle_startendtag = handle_starttag


def normalize_url_path(value):
    """Normalize a stored URL/path for exact matching; query/fragment ignored."""
    if value is None:
        return None
    raw = str(value).strip().strip("\"'")
    if not raw:
        return None
    try:
        path = unquote(urlsplit(raw).path or "")
    except ValueError:
        return None
    if not path:
        return None
    # Storage file names are usually relative; URL paths usually begin with /.
    path = "/" + path.lstrip("/")
    normalized = posixpath.normpath(path)
    if normalized in ("/", "/."):
        return None
    return normalized


def extract_url_paths(content):
    """Return normalized URL paths found in HTML/string content."""
    if content is None:
        return set()
    text = str(content)
    parser = _MediaURLCollector()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        # HTMLParser is intentionally tolerant, but a malformed legacy body
        # must not abort an audit. Valid URL attributes collected so far remain.
        pass
    result = set()
    for raw_url in parser.urls:
        path = normalize_url_path(raw_url)
        if path:
            result.add(path)
    return result


def _iter_string_values(value, prefix=""):
    """Yield textual leaves from JSON-backed Wagtail revision content."""
    if isinstance(value, str):
        yield prefix, value
    elif isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _iter_string_values(child, child_prefix)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _iter_string_values(child, f"{prefix}[{index}]")


def file_path_aliases(file_name, file_url=None, media_url=None):
    """Build URL-path aliases for a storage name and its public URL."""
    aliases = set()
    for value in (file_name, file_url):
        path = normalize_url_path(value)
        if path:
            aliases.add(path)
    if file_name and media_url:
        try:
            media_base = str(media_url)
            if not media_base.endswith("/"):
                media_base += "/"
            path = normalize_url_path(urljoin(media_base, str(file_name).lstrip("/")))
            if path:
                aliases.add(path)
        except (TypeError, ValueError):
            pass
    return aliases


def build_image_file_target_index(image_ids=None, *, include_originals=True, include_renditions=True):
    """Map normalized storage URL paths to image/rendition descriptors."""
    from django.conf import settings
    from wagtail.images import get_image_model

    Image = get_image_model()
    wanted_ids = None if image_ids is None else {int(value) for value in image_ids}
    targets = defaultdict(list)
    media_url = getattr(settings, "MEDIA_URL", "/media/")

    def register(file_field, descriptor):
        if not file_field:
            return
        try:
            file_name = file_field.name
        except (AttributeError, ValueError):
            return
        if not file_name:
            return
        try:
            file_url = file_field.url
        except Exception:
            file_url = None
        for alias in file_path_aliases(file_name, file_url, media_url):
            if descriptor not in targets[alias]:
                targets[alias].append(dict(descriptor))

    if include_originals:
        images = Image.objects.all()
        if wanted_ids is not None:
            images = images.filter(pk__in=wanted_ids)
        for image in images.only("pk", "file").iterator(chunk_size=500):
            register(image.file, {
                "kind": "original",
                "image_id": image.pk,
                "file_name": image.file.name if image.file else "",
            })

    if include_renditions:
        Rendition = Image.get_rendition_model()
        renditions = Rendition.objects.all()
        if wanted_ids is not None:
            renditions = renditions.filter(image_id__in=wanted_ids)
        for rendition in renditions.only("pk", "image_id", "filter_spec", "file").iterator(chunk_size=500):
            register(rendition.file, {
                "kind": "rendition",
                "image_id": rendition.image_id,
                "rendition_id": rendition.pk,
                "filter_spec": rendition.filter_spec,
                "file_name": rendition.file.name if rendition.file else "",
            })

    return dict(targets)


def content_field_names_for_model(model, page_model):
    """Return relevant text fields for a model without querying the database.

    Page subclasses are scanned across every textual/JSON field because
    project-specific page models often use custom field names. For other
    models, only conventional rich-text/content names are included. This
    deliberately covers ForumPost.content and MPTT Comment.content/response.
    """
    content_field_names = {
        "body", "content", "intro", "description", "html", "text",
        "message", "comment", "caption", "quote", "summary", "post",
        "signature", "details", "excerpt", "response", "answer",
    }
    text_field_types = {"TextField", "CharField", "JSONField"}
    try:
        is_page_model = model is not page_model and issubclass(model, page_model)
    except TypeError:
        is_page_model = False

    selected = []
    for field in model._meta.get_fields():
        if not getattr(field, "concrete", False) or getattr(field, "is_relation", False):
            continue
        if field.get_internal_type() not in text_field_types:
            continue
        if not is_page_model and field.name not in content_field_names:
            continue
        selected.append(field.name)
    return selected, is_page_model


def _iter_current_content_sources():
    """Yield current textual content likely to contain embedded media URLs.

    All text/JSON fields on Wagtail Page subclasses are scanned because custom
    page models use many different field names. For non-Page models, conventional
    content field names cover rich-text records such as ForumPost and MPTT
    Comment, which do not necessarily have Wagtail revisions.
    """
    from django.apps import apps
    from wagtail.models import Page

    for model in apps.get_models():
        if model._meta.abstract or model._meta.proxy:
            continue
        fields, is_page_model = content_field_names_for_model(model, Page)
        if not fields:
            continue

        for row in model._default_manager.values_list("pk", *fields).iterator(chunk_size=250):
            object_id = row[0]
            for field_name, value in zip(fields, row[1:]):
                source_count = 0
                for json_path, text in _iter_string_values(value, field_name):
                    source_count += 1
                    yield {
                        "kind": "page" if is_page_model else "model_content",
                        "model": model._meta.label,
                        "object_id": object_id,
                        "field": json_path,
                    }, text
                if not source_count:
                    yield {
                        "kind": "page" if is_page_model else "model_content",
                        "model": model._meta.label,
                        "object_id": object_id,
                        "field": field_name,
                    }, ""


def _iter_revision_content_sources():
    """Yield textual leaves from every stored Wagtail revision."""
    from django.apps import apps

    try:
        Revision = apps.get_model("wagtailcore", "Revision")
    except LookupError:
        return
    qs = Revision.objects.all().only("pk", "content_type_id", "object_id", "content")
    for revision in qs.iterator(chunk_size=250):
        source_count = 0
        for json_path, text in _iter_string_values(revision.content, "content"):
            source_count += 1
            yield {
                "kind": "revision",
                "revision_id": revision.pk,
                "content_type_id": revision.content_type_id,
                "object_id": revision.object_id,
                "field": json_path,
            }, text
        if not source_count:
            yield {
                "kind": "revision",
                "revision_id": revision.pk,
                "content_type_id": revision.content_type_id,
                "object_id": revision.object_id,
                "field": "content",
            }, ""


def scan_content_and_revision_references(target_index):
    """Scan current content fields and every revision for exact media URL matches.

    Includes Page content, common rich-text fields on other installed models,
    and all saved Wagtail revision content.

    Returns counters, matched URL paths and source descriptors.
    No database or storage writes are performed.
    """
    matched = []
    current_content_rows = 0
    revision_rows_seen = set()

    for source, text in _iter_current_content_sources():
        current_content_rows += 1
        for path in extract_url_paths(text):
            for target in target_index.get(path, ()):
                matched.append({"path": path, "target": target, "source": source})

    for source, text in _iter_revision_content_sources():
        revision_rows_seen.add(source["revision_id"])
        for path in extract_url_paths(text):
            for target in target_index.get(path, ()):
                matched.append({"path": path, "target": target, "source": source})

    if current_content_rows == 0 and not revision_rows_seen:
        raise RuntimeError(
            "Не обнаружено ни одного текущего контентного поля и ни одной Wagtail revision; "
            "полнота сканирования не подтверждена."
        )

    # Deduplicate identical matches when a path appears more than once in one
    # source block or aliases resolve to the same stored object.
    unique = []
    seen = set()
    for row in matched:
        target = row["target"]
        source = row["source"]
        key = (
            row["path"], target.get("kind"), target.get("image_id"),
            target.get("rendition_id"), source.get("kind"),
            source.get("model"), source.get("object_id"),
            source.get("revision_id"), source.get("field"),
        )
        if key not in seen:
            seen.add(key)
            unique.append(row)

    return {
        "current_content_values_scanned": current_content_rows,
        "revision_records_scanned": len(revision_rows_seen),
        "matches": unique,
        "referenced_image_ids": sorted({
            int(row["target"]["image_id"]) for row in unique
            if row["target"].get("image_id") is not None
        }),
        "referenced_rendition_specs": sorted({
            row["target"]["filter_spec"] for row in unique
            if row["target"].get("filter_spec")
        }),
    }


# Private compatibility alias for any local management command developed
# against the earlier name during this repair batch.
scan_page_and_revision_references = scan_content_and_revision_references


def find_live_image_relation_references(image_ids):
    """Find live model relations (FK/O2O/M2M) from installed models to images.

    The Wagtail rendition model is excluded because each rendition necessarily
    points to its source image and is not an independent content reference.
    """
    from django.apps import apps
    from wagtail.images import get_image_model

    Image = get_image_model()
    Rendition = Image.get_rendition_model()
    wanted = {int(value) for value in image_ids}
    if not wanted:
        return []

    references = []
    for model in apps.get_models():
        if model in (Image, Rendition) or model._meta.abstract or model._meta.proxy:
            continue
        for field in model._meta.get_fields():
            if not getattr(field, "concrete", False) or not getattr(field, "is_relation", False):
                continue
            if getattr(field, "related_model", None) is not Image:
                continue
            try:
                if getattr(field, "many_to_many", False):
                    qs = model._default_manager.filter(**{f"{field.name}__pk__in": wanted})
                    rows = qs.values_list("pk", f"{field.name}__pk").distinct().iterator(chunk_size=250)
                else:
                    qs = model._default_manager.filter(**{f"{field.attname}__in": wanted})
                    rows = qs.values_list("pk", field.attname).iterator(chunk_size=250)
                for object_id, image_id in rows:
                    references.append({
                        "kind": "relation",
                        "model": model._meta.label,
                        "object_id": object_id,
                        "field": field.name,
                        "image_id": int(image_id),
                    })
            except Exception:
                # Fail closed at the caller: an incomplete relation scan must
                # not be interpreted as evidence that deletion is safe.
                raise
    return references



def find_revision_image_relation_references(image_ids):
    """Find image FK/O2O/M2M values preserved in historical revisions."""
    from django.apps import apps
    from django.contrib.contenttypes.models import ContentType
    from wagtail.images import get_image_model

    Image = get_image_model()
    Rendition = Image.get_rendition_model()
    wanted = {int(value) for value in image_ids}
    if not wanted:
        return []

    model_fields = {}
    for model in apps.get_models():
        if model in (Image, Rendition) or model._meta.abstract or model._meta.proxy:
            continue
        names = []
        for field in model._meta.get_fields():
            if not getattr(field, "concrete", False) or not getattr(field, "is_relation", False):
                continue
            if getattr(field, "related_model", None) is not Image:
                continue
            names.append((field.name, field.attname if not field.many_to_many else None))
        if names:
            model_fields[(model._meta.app_label, model._meta.model_name)] = (model, names)

    if not model_fields:
        return []

    # Query existing ContentTypes only. get_for_model() can create rows, which
    # would violate this scanner's strict read-only contract.
    content_type_map = {}
    for content_type in ContentType.objects.all().only("pk", "app_label", "model"):
        key = (content_type.app_label, content_type.model)
        if key in model_fields:
            content_type_map[content_type.pk] = model_fields[key]
    if not content_type_map:
        return []

    Revision = apps.get_model("wagtailcore", "Revision")
    refs = []
    qs = Revision.objects.filter(content_type_id__in=content_type_map).only(
        "pk", "content_type_id", "object_id", "content"
    )
    for revision in qs.iterator(chunk_size=250):
        model, fields = content_type_map[revision.content_type_id]
        content = revision.content if isinstance(revision.content, dict) else {}
        for field_name, attname in fields:
            candidates = [field_name]
            if attname and attname != field_name:
                candidates.append(attname)
            for key in candidates:
                raw_value = content.get(key)
                values = raw_value if isinstance(raw_value, (list, tuple)) else [raw_value]
                for value in values:
                    try:
                        image_id = int(value) if value not in (None, "") else None
                    except (TypeError, ValueError):
                        image_id = None
                    if image_id in wanted:
                        refs.append({
                            "kind": "revision_relation",
                            "model": model._meta.label,
                            "object_id": revision.object_id,
                            "revision_id": revision.pk,
                            "field": key,
                            "image_id": image_id,
                        })
    return refs

def find_referenced_images(image_ids):
    """Return URL/revision and live-relation references keyed by image ID."""
    wanted = {int(value) for value in image_ids}
    if not wanted:
        return {}
    target_index = build_image_file_target_index(wanted)
    content_scan = scan_page_and_revision_references(target_index)
    relation_refs = find_live_image_relation_references(wanted)
    revision_relation_refs = find_revision_image_relation_references(wanted)
    result = defaultdict(list)
    for row in content_scan["matches"]:
        image_id = row["target"].get("image_id")
        if image_id is not None:
            result[int(image_id)].append({
                "kind": row["source"]["kind"],
                "model": row["source"].get("model"),
                "object_id": row["source"].get("object_id"),
                "revision_id": row["source"].get("revision_id"),
                "field": row["source"].get("field"),
                "file_kind": row["target"].get("kind"),
                "filter_spec": row["target"].get("filter_spec"),
                "path": row["path"],
            })
    for row in relation_refs + revision_relation_refs:
        result[int(row["image_id"])].append(row)
    return dict(result)
