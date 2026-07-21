"""Image discovery, filtering and file naming for the revised pipeline."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from final_cleaning_rules import clean_caption, should_keep_image


CAPTION_CLASS = re.compile(
    r"caption|image[_-]?text|photo[_-]?text|credit|text_greyish-brown",
    re.I,
)
APPLEDAILY_IMAGE_CONTAINER_CLASS = re.compile(
    r"promoItem|promo-image-box|tw-promo-image|inline-image",
    re.I,
)
APPLEDAILY_PROMO_CONTAINER_CLASS = re.compile(r"promoItem|promo-image-box|tw-promo-image", re.I)
WAYBACK_REPLAY_PATH = re.compile(r"^/web/\d+(?:[a-z_]+)?/(https?://.+)$", re.I)


def iter_json_objects(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_json_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_json_objects(child)


def json_ld_objects(soup: BeautifulSoup) -> list[dict[str, Any]]:
    objects = []
    for script in soup.find_all("script", type=re.compile(r"ld\+json", re.I)):
        raw = script.string or script.get_text()
        if not raw.strip():
            continue
        try:
            objects.extend(iter_json_objects(json.loads(raw)))
        except (json.JSONDecodeError, TypeError):
            continue
    return objects


def srcset_urls(value: str) -> list[str]:
    return [part.strip().split()[0] for part in value.split(",") if part.strip()]


def normalize_url(value: str | None, base_uri: str) -> str | None:
    if not value or not value.strip():
        return None
    url = urljoin(base_uri, value.strip())
    url = unwrap_wayback_replay_url(url)
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"}:
        return None
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))


def unwrap_wayback_replay_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.netloc.lower() not in {"web.archive.org", "archive.org"}:
        return url
    match = WAYBACK_REPLAY_PATH.match(parts.path)
    if not match:
        return url
    return unquote(match.group(1))


def url_keys(url: str) -> set[str]:
    """Keys used to match minor query-string differences in WARC targets."""
    keys = set()
    for candidate in {url, unwrap_wayback_replay_url(url)}:
        parts = urlsplit(candidate)
        if parts.scheme not in {"http", "https"}:
            continue
        exact = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))
        queryless = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, "", ""))
        keys.update({exact, queryless})
    return keys


def add_candidate(candidates: dict, url: str | None, source: str) -> dict | None:
    if not url:
        return None
    entry = candidates.setdefault(url, {"url": url, "sources": [], "captions": []})
    if source not in entry["sources"]:
        entry["sources"].append(source)
    return entry


def caption_for_img(img) -> tuple[str | None, str | None]:
    figure = img.find_parent("figure")
    if figure:
        tag = figure.find("figcaption")
        if tag and tag.get_text(strip=True):
            return tag.get_text(" ", strip=True), "figcaption"
    promo_container = img.find_parent(class_=APPLEDAILY_PROMO_CONTAINER_CLASS)
    if promo_container:
        tag = promo_container.find(["figcaption", "div", "span", "p"], class_=CAPTION_CLASS)
        if tag and tag.get_text(strip=True):
            return tag.get_text(" ", strip=True), "appledaily-promo-container"
    apple_container = img.find_parent(class_=APPLEDAILY_IMAGE_CONTAINER_CLASS)
    if apple_container:
        tag = apple_container.find(["figcaption", "div", "span", "p"], class_=CAPTION_CLASS)
        if tag and tag.get_text(strip=True):
            return tag.get_text(" ", strip=True), "appledaily-caption-class"
    parent = img.find_parent(["figure", "div", "p"])
    if parent:
        tag = parent.find(["figcaption", "div", "span", "p"], class_=CAPTION_CLASS)
        if tag and tag.get_text(strip=True):
            return tag.get_text(" ", strip=True), "nearby-caption-class"
    for attribute in ("alt", "title"):
        if img.get(attribute) and img[attribute].strip():
            return img[attribute].strip(), f"img[{attribute}]"
    return None, None


def extract_image_info(html: str, article_uri: str, article_id: str) -> dict[str, dict]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: dict[str, dict] = {}

    for index, img in enumerate(soup.find_all("img")):
        urls = []
        for attribute in ("data-src", "data-original", "src"):
            if img.get(attribute):
                urls.append((img[attribute], f"img[{index}].{attribute}"))
        for attribute in ("data-srcset", "srcset"):
            if img.get(attribute):
                urls.extend((url, f"img[{index}].{attribute}") for url in srcset_urls(img[attribute]))

        entries = []
        for value, source in urls:
            entry = add_candidate(candidates, normalize_url(value, article_uri), source)
            if entry:
                entries.append(entry)
        caption, caption_source = caption_for_img(img)
        if caption:
            evidence = {"value": caption, "source": caption_source}
            for entry in entries:
                if evidence not in entry["captions"]:
                    entry["captions"].append(evidence)

    for attribute, key in (("property", "og:image"), ("name", "twitter:image")):
        for tag in soup.find_all("meta", attrs={attribute: key}):
            add_candidate(
                candidates,
                normalize_url(tag.get("content"), article_uri),
                f"meta[{attribute}={key}]",
            )

    for index, obj in enumerate(json_ld_objects(soup)):
        image_value = obj.get("image")
        values = image_value if isinstance(image_value, list) else [image_value]
        for value in values:
            caption = None
            if isinstance(value, str):
                url = normalize_url(value, article_uri)
            elif isinstance(value, dict):
                url = normalize_url(value.get("url") or value.get("contentUrl"), article_uri)
                caption = value.get("caption") or value.get("description")
            else:
                continue
            entry = add_candidate(candidates, url, f"json-ld[{index}].image")
            if entry and isinstance(caption, str) and caption.strip():
                evidence = {"value": caption.strip(), "source": f"json-ld[{index}].image.caption"}
                if evidence not in entry["captions"]:
                    entry["captions"].append(evidence)

    return {
        url: candidate
        for url, candidate in candidates.items()
        if should_keep_image(url, article_id, candidate["sources"])
    }


def safe_image_filename(uri: str, content_type: str | None = None) -> str:
    basename = Path(unquote(urlsplit(uri).path)).name
    basename = re.sub(r"[^A-Za-z0-9._-]", "_", basename)
    if not basename or basename in {".", ".."}:
        basename = hashlib.sha256(uri.encode("utf-8")).hexdigest()[:24]
    if not Path(basename).suffix:
        extension = mimetypes.guess_extension((content_type or "").split(";", 1)[0].strip()) or ".bin"
        basename += extension
    return basename


def image_output_path(article_dir: str, uri: str, content_type: str | None = None) -> str:
    path = os.path.join(article_dir, "img", safe_image_filename(uri, content_type))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path
