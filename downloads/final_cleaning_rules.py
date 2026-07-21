#!/usr/bin/env python3
"""Final conservative cleanup rules for Apple Daily ninjs records.

Intentionally out of scope: ``genres``, ``infoSources`` and image creators.
This module contains decisions only; it does not modify the source dataset.
"""

from __future__ import annotations

import re
import html
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import unquote

import ftfy

from credit_rules import CreditResult, parse_credit

IGNORED_FIELDS = frozenset({"genres", "infoSources", "imageCreator"})
EXACT_DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
WEAK_CAPTIONS = frozenset({"banner", "image", "photo", "圖片", "照片"})
TAIWAN_TZ = timezone(timedelta(hours=8))
NORMALIZED_SPACE_CHARS = {
    "\u00a0": " ",
    "\u2028": "\n",
    "\u2029": "\n\n",
}
REMOVED_FORMAT_CHARS = {
    "\ufeff",
    "\u00ad",
    "\u180e",
    "\u200b",
    "\u200c",
    "\u200d",
    "\u2060",
}


def is_exact_datetime(value: Any) -> bool:
    """Accept only ISO 8601 date-times that explicitly include a timezone."""
    if not isinstance(value, str) or not EXACT_DATETIME.fullmatch(value.strip()):
        return False
    try:
        datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def choose_exact_datetime(candidates: list[dict]) -> str | None:
    """Return the first exact evidenced value; never manufacture midnight."""
    for candidate in candidates:
        value = candidate.get("value")
        if is_exact_datetime(value):
            return value.strip()
    return None


def taiwan_now_iso() -> str:
    """Return the JSON creation time in Taiwan's UTC+08:00 offset."""
    return datetime.now(TAIWAN_TZ).replace(microsecond=0).isoformat()


def to_taiwan_time(value: str | None) -> str | None:
    """Normalize an evidenced ISO 8601 date-time to UTC+08:00."""
    if not is_exact_datetime(value):
        return None
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    return parsed.astimezone(TAIWAN_TZ).replace(microsecond=0).isoformat()


def repair_mojibake(value: str) -> str:
    """Repair likely UTF-8 text that was decoded as Latin-1/CP1252."""
    return ftfy.fix_encoding(value)


def clean_text_value(value: str) -> str:
    """Remove machine-visible artifacts without rewriting article wording."""
    value = repair_mojibake(value)
    value = html.unescape(value)
    output = []
    for char in value:
        if char in NORMALIZED_SPACE_CHARS:
            output.append(NORMALIZED_SPACE_CHARS[char])
            continue
        if char in REMOVED_FORMAT_CHARS:
            continue
        if unicodedata.category(char) == "Cc" and char not in ("\t", "\n", "\r"):
            continue
        output.append(char)
    return "".join(output).strip()


def final_dates(
    published_candidates: list[dict],
    modified_candidates: list[dict],
    warc_date: str | None,
) -> dict[str, str]:
    """Map evidenced dates to official ninjs camelCase fields."""
    result: dict[str, str] = {}
    first_created = choose_exact_datetime(published_candidates)
    if first_created:
        result["firstCreated"] = to_taiwan_time(first_created)
    version_created = to_taiwan_time(warc_date)
    if version_created:
        result["versionCreated"] = version_created
    result["contentCreated"] = taiwan_now_iso()
    return result


def image_source_flags(sources: list[str]) -> dict[str, bool]:
    return {
        "in_og_image": any("og:image" in source for source in sources),
        "in_json_ld": any(source.startswith("json-ld[") for source in sources),
    }


def should_keep_image(image_url: str, article_id: str, sources: list[str]) -> bool:
    """Keep an ID-owned image or an image supported by OG/JSON-LD metadata."""
    flags = image_source_flags(sources)
    contains_article_id = article_id.lower() in unquote(image_url).lower()
    return contains_article_id or flags["in_og_image"] or flags["in_json_ld"]


def clean_caption(captions: list[dict]) -> str | None:
    """Choose the first non-empty, non-placeholder caption."""
    for caption in captions:
        value = clean_text_value(str(caption.get("value", "")))
        if not value:
            continue
        lowered = value.casefold()
        if lowered in WEAK_CAPTIONS or value.isdigit():
            continue
        return value
    return None


def build_picture_association(
    *,
    index: int,
    image_url: str,
    captions: list[dict],
) -> dict:
    """Build one picture association in the project's canonical ninjs form."""
    association = {
        "name": f"picture{index}",
        "uri": image_url,
        "type": "picture",
    }
    caption = clean_caption(captions)
    if caption:
        association["headlines"] = [{"value": caption}]
    return association


def build_associations(article_id: str, images: list[dict]) -> list[dict]:
    """Filter audited images and build associations without creator metadata."""
    associations = []
    for image in images:
        image_url = image["url"]
        sources = image.get("sources", [])
        if not should_keep_image(image_url, article_id, sources):
            continue
        associations.append(
            build_picture_association(
                index=len(associations),
                image_url=image_url,
                captions=image.get("captions", []),
            )
        )
    return associations


def parse_by_and_location(raw_credit: str) -> dict[str, str]:
    """Expose only final ninjs fields from the detailed credit parser."""
    parsed: CreditResult = parse_credit(raw_credit)
    if not parsed.matched:
        return {"by": "", "located": ""}
    return {"by": clean_text_value(parsed.by), "located": clean_text_value(parsed.located)}


def remove_ignored_fields(record: dict) -> dict:
    """Return a shallow copy without intentionally unsupported fields."""
    return {key: value for key, value in record.items() if key not in IGNORED_FIELDS}


if __name__ == "__main__":
    sample_images = [
        {
            "url": "https://static.example/20210101/ARTICLE123/img/photo.jpg",
            "sources": ["img[0].src"],
            "captions": [{"value": "新聞圖片說明", "source": "img[alt]"}],
        },
        {
            "url": "https://img.example/banner.png",
            "sources": ["img[1].src"],
            "captions": [{"value": "Banner", "source": "img[alt]"}],
        },
    ]
    print(build_associations("ARTICLE123", sample_images))
    print(parse_by_and_location("劉智維╱高雄"))
