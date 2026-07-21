#!/usr/bin/env python3
"""Audit recoverable metadata in Apple Daily WARC HTML responses.

This script does not invent values or modify source data. It scans WARC files
364--370 by default, writes one compact evidence record per eligible HTML
response, and reports existence percentages at both response and unique-article
levels.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import logging
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from fastwarc.warc import ArchiveIterator


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_WARC_DIR = Path("/mnt/data/venv/codes/downloads/files_current364")
DEFAULT_OUTPUT = BASE_DIR / "warc_recoverable_fields.jsonl"
DEFAULT_REPORT = BASE_DIR / "warc_recoverable_fields_report.json"
DEFAULT_ERROR_LOG = BASE_DIR / "warc_recoverable_fields.errors.log"

FIELD_NAMES = (
    "exactFirstCreated",
    "exactContentCreated",
    "originalImageUrl",
    "imageCaption",
    "genres",
    "infoSources",
)
FIELD_BITS = {name: 1 << index for index, name in enumerate(FIELD_NAMES)}

ALLOWED_HOSTS = {"appledaily.com.tw", "www.appledaily.com.tw", "tw.appledaily.com.tw"}
ARTICLE_PATH = re.compile(r"^/[^/]+/\d{8}/(?P<id>[A-Za-z0-9]+)/*$")
EXACT_DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)

PUBLISHED_META_KEYS = (
    ("property", "article:published_time"),
    ("name", "published_time"),
    ("property", "og:article:published_time"),
    ("name", "datePublished"),
)
MODIFIED_META_KEYS = (
    ("property", "article:modified_time"),
    ("name", "modified_time"),
    ("property", "og:article:modified_time"),
    ("name", "dateModified"),
)

GENRE_TERMS = (
    "外電報導",
    "連線報導",
    "人物專訪",
    "專訪",
    "分析",
    "評論",
    "社論",
    "特稿",
)
INFO_SOURCE_PATTERNS = {
    "Reuters": re.compile(r"(?i)(?<![A-Za-z])Reuters(?![A-Za-z])|路透社|路透"),
    "Associated Press": re.compile(r"(?i)(?<![A-Za-z])Associated Press(?![A-Za-z])|美聯社"),
    "AFP": re.compile(r"(?i)(?<![A-Za-z])AFP(?![A-Za-z])|法新社"),
    "Central News Agency": re.compile(r"中央社"),
    "Bloomberg": re.compile(r"(?i)(?<![A-Za-z])Bloomberg(?![A-Za-z])|彭博"),
    "BBC": re.compile(r"(?i)(?<![A-Za-z])BBC(?![A-Za-z])|英國廣播公司"),
    "CNN": re.compile(r"(?i)(?<![A-Za-z])CNN(?![A-Za-z])"),
    "NHK": re.compile(r"(?i)(?<![A-Za-z])NHK(?![A-Za-z])|日本放送協會"),
    "Xinhua": re.compile(r"新華社"),
    "Kyodo": re.compile(r"共同社"),
    "Yonhap": re.compile(r"韓聯社"),
}
CAPTION_CLASS = re.compile(r"caption|image[_-]?text|photo[_-]?text|credit", re.I)


def configure_logging(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=path,
        filemode="w",
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        force=True,
    )


def dechunk(data: bytes) -> bytes:
    source = io.BytesIO(data)
    output = io.BytesIO()
    while True:
        size_line = source.readline()
        if not size_line:
            raise ValueError("missing terminating zero-size chunk")
        try:
            size = int(size_line.split(b";", 1)[0].strip(), 16)
        except ValueError as exc:
            raise ValueError(f"invalid chunk size: {size_line[:80]!r}") from exc
        if size == 0:
            return output.getvalue()
        chunk = source.read(size)
        if len(chunk) != size:
            raise ValueError(f"short chunk: expected {size}, got {len(chunk)}")
        output.write(chunk)
        if source.read(2) != b"\r\n":
            raise ValueError("chunk missing CRLF terminator")


def decode_record(record) -> str:
    raw = record.reader.read()
    headers = {str(k).lower(): str(v) for k, v in record.http_headers.items()}
    if "chunked" in headers.get("transfer-encoding", "").lower():
        raw = dechunk(raw)
    if headers.get("content-encoding", "").lower() == "gzip":
        raw = gzip.decompress(raw)

    content_type = headers.get("content-type", "")
    match = re.search(r"charset=([^;\s]+)", content_type, re.I)
    charset = match.group(1).strip("\"'") if match else (record.http_charset or "utf-8")
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def article_id(uri: str) -> str | None:
    parts = urlsplit(uri)
    if parts.scheme not in {"http", "https"}:
        return None
    if (parts.hostname or "").lower() not in ALLOWED_HOSTS:
        return None
    match = ARTICLE_PATH.fullmatch(parts.path)
    return match.group("id") if match else None


def valid_exact_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not EXACT_DATETIME.fullmatch(value.strip()):
        return False
    try:
        datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def iter_json_objects(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_json_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_json_objects(child)


def json_ld_objects(soup: BeautifulSoup) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    for script in soup.find_all("script", type=re.compile(r"ld\+json", re.I)):
        raw = script.string or script.get_text()
        if not raw.strip():
            continue
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        objects.extend(iter_json_objects(parsed))
    return objects


def first_meta_content(soup: BeautifulSoup, keys) -> tuple[str | None, str | None]:
    for attribute, value in keys:
        tag = soup.find("meta", attrs={attribute: re.compile(f"^{re.escape(value)}$", re.I)})
        if tag and tag.get("content"):
            return tag["content"].strip(), f"meta[{attribute}={value}]"
    return None, None


def exact_date_evidence(
    soup: BeautifulSoup,
    ld_objects: list[dict[str, Any]],
    meta_keys,
    ld_key: str,
) -> tuple[dict | None, list[dict]]:
    candidates: list[dict] = []
    value, source = first_meta_content(soup, meta_keys)
    if value:
        candidates.append({"value": value, "source": source, "exact": valid_exact_datetime(value)})
    for index, obj in enumerate(ld_objects):
        value = obj.get(ld_key)
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, str) and item.strip():
                candidates.append(
                    {
                        "value": item.strip(),
                        "source": f"json-ld[{index}].{ld_key}",
                        "exact": valid_exact_datetime(item),
                    }
                )
    exact = next((candidate for candidate in candidates if candidate["exact"]), None)
    return exact, candidates


def srcset_urls(value: str) -> list[str]:
    urls = []
    for candidate in value.split(","):
        token = candidate.strip().split()
        if token:
            urls.append(token[0])
    return urls


def clean_url(value: Any, base_uri: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    url = urljoin(base_uri, value.strip())
    if urlsplit(url).scheme not in {"http", "https"}:
        return None
    return url


def add_image_url(images: dict[str, dict], url: str | None, source: str) -> None:
    if url:
        images.setdefault(url, {"url": url, "sources": [], "captions": []})
        if source not in images[url]["sources"]:
            images[url]["sources"].append(source)


def caption_for_img(img) -> tuple[str | None, str | None]:
    figure = img.find_parent("figure")
    if figure:
        tag = figure.find("figcaption")
        if tag and tag.get_text(strip=True):
            return tag.get_text(" ", strip=True), "figcaption"
    parent = img.find_parent(["figure", "div", "p"])
    if parent:
        tag = parent.find(["figcaption", "div", "span", "p"], class_=CAPTION_CLASS)
        if tag and tag.get_text(strip=True):
            return tag.get_text(" ", strip=True), "nearby-caption-class"
    for attribute in ("alt", "title"):
        if img.get(attribute) and img[attribute].strip():
            return img[attribute].strip(), f"img[{attribute}]"
    return None, None


def extract_images(
    soup: BeautifulSoup,
    ld_objects: list[dict[str, Any]],
    base_uri: str,
) -> list[dict]:
    images: dict[str, dict] = {}
    scope = soup.find("article") or soup.find(id="articleBody") or soup

    for index, img in enumerate(scope.find_all("img")):
        urls: list[tuple[str, str]] = []
        for attribute in ("data-src", "data-original", "src"):
            if img.get(attribute):
                urls.append((img[attribute], f"img[{index}].{attribute}"))
        for attribute in ("data-srcset", "srcset"):
            if img.get(attribute):
                urls.extend(
                    (url, f"img[{index}].{attribute}") for url in srcset_urls(img[attribute])
                )
        normalized_urls = []
        for value, source in urls:
            url = clean_url(value, base_uri)
            add_image_url(images, url, source)
            if url:
                normalized_urls.append(url)

        caption, caption_source = caption_for_img(img)
        if caption:
            for url in normalized_urls:
                entry = images[url]
                evidence = {"value": caption, "source": caption_source}
                if evidence not in entry["captions"]:
                    entry["captions"].append(evidence)

    for property_name in ("og:image", "twitter:image"):
        for tag in soup.find_all("meta", attrs={"property": property_name}):
            add_image_url(images, clean_url(tag.get("content"), base_uri), f"meta[property={property_name}]")
        for tag in soup.find_all("meta", attrs={"name": property_name}):
            add_image_url(images, clean_url(tag.get("content"), base_uri), f"meta[name={property_name}]")

    for index, obj in enumerate(ld_objects):
        image_value = obj.get("image")
        values = image_value if isinstance(image_value, list) else [image_value]
        for value in values:
            if isinstance(value, str):
                add_image_url(images, clean_url(value, base_uri), f"json-ld[{index}].image")
            elif isinstance(value, dict):
                url = clean_url(value.get("url") or value.get("contentUrl"), base_uri)
                add_image_url(images, url, f"json-ld[{index}].image")
                if not url:
                    continue
                caption = value.get("caption") or value.get("description")
                if isinstance(caption, str) and caption.strip():
                    images[url]["captions"].append(
                        {"value": caption.strip(), "source": f"json-ld[{index}].image.caption"}
                    )
    return list(images.values())


def article_text(soup: BeautifulSoup) -> str:
    scope = soup.find("article") or soup.find(id="articleBody")
    if scope:
        return scope.get_text("\n", strip=True)
    description = soup.find("meta", property="og:description") or soup.find(
        "meta", attrs={"name": "description"}
    )
    return description.get("content", "") if description else ""


def audit_html(html: str, uri: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    ld_objects = json_ld_objects(soup)
    first_exact, first_candidates = exact_date_evidence(
        soup, ld_objects, PUBLISHED_META_KEYS, "datePublished"
    )
    content_exact, content_candidates = exact_date_evidence(
        soup, ld_objects, MODIFIED_META_KEYS, "dateModified"
    )
    images = extract_images(soup, ld_objects, uri)

    text = article_text(soup)
    title = soup.title.get_text(strip=True) if soup.title else ""
    searchable = f"{title}\n{text}"
    genres = [term for term in GENRE_TERMS if term in searchable]
    info_sources = [name for name, pattern in INFO_SOURCE_PATTERNS.items() if pattern.search(searchable)]

    return {
        "exactFirstCreated": first_exact,
        "exactFirstCreatedCandidates": first_candidates,
        "exactContentCreated": content_exact,
        "exactContentCreatedCandidates": content_candidates,
        "images": images,
        "genres": genres,
        "infoSources": info_sources,
    }


def existence(audit: dict) -> dict[str, bool]:
    images = audit["images"]
    return {
        "exactFirstCreated": audit["exactFirstCreated"] is not None,
        "exactContentCreated": audit["exactContentCreated"] is not None,
        "originalImageUrl": bool(images),
        "imageCaption": any(image["captions"] for image in images),
        "genres": bool(audit["genres"]),
        "infoSources": bool(audit["infoSources"]),
    }


def percentages(counts: Counter, denominator: int) -> dict[str, dict]:
    return {
        field: {
            "exists": counts[field],
            "total": denominator,
            "percentage": round(counts[field] * 100 / denominator, 4) if denominator else 0.0,
        }
        for field in FIELD_NAMES
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warc-dir", type=Path, default=DEFAULT_WARC_DIR)
    parser.add_argument("--first", type=int, default=364)
    parser.add_argument("--last", type=int, default=370)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--error-log", type=Path, default=DEFAULT_ERROR_LOG)
    parser.add_argument("--progress-every", type=int, default=10_000)
    parser.add_argument("--limit", type=int, help="Stop after this many analyzed responses (testing).")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.error_log)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    counters: Counter[str] = Counter()
    response_fields: Counter[str] = Counter()
    unique_masks: dict[str, int] = {}
    stopped = False

    with args.output.open("w", encoding="utf-8") as output:
        for number in range(args.first, args.last + 1):
            if stopped:
                break
            warc_path = args.warc_dir / f"file{number}.warc"
            if not warc_path.is_file():
                counters["missing_warc_files"] += 1
                logging.error("Missing WARC file: %s", warc_path)
                continue
            print(f"Scanning {warc_path}", file=sys.stderr)
            try:
                with warc_path.open("rb") as stream:
                    for record_number, record in enumerate(
                        ArchiveIterator(stream, parse_http=True), start=1
                    ):
                        counters["warc_records"] += 1
                        if record.headers.get("WARC-Type") != "response":
                            continue
                        if not record.is_http or not record.http_headers:
                            continue
                        if "200 OK" not in (record.http_headers.status_line or ""):
                            continue
                        uri = record.headers.get("WARC-Target-URI", "")
                        aid = article_id(uri)
                        if not aid:
                            continue
                        content_type = record.http_headers.get("Content-Type", "").lower()
                        if not content_type.startswith("text/html"):
                            continue
                        counters["eligible_responses"] += 1

                        try:
                            html = decode_record(record)
                            audit = audit_html(html, uri)
                            fields = existence(audit)
                            for field, present in fields.items():
                                if present:
                                    response_fields[field] += 1
                            mask = sum(FIELD_BITS[field] for field, present in fields.items() if present)
                            unique_masks[aid] = unique_masks.get(aid, 0) | mask

                            output.write(
                                json.dumps(
                                    {
                                        "source_warc": str(warc_path),
                                        "record_number": record_number,
                                        "warc_date": record.headers.get("WARC-Date"),
                                        "uri": uri,
                                        "article_id": aid,
                                        "exists": fields,
                                        "evidence": audit,
                                    },
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )
                            counters["analyzed_responses"] += 1
                        except Exception:
                            counters["analysis_errors"] += 1
                            logging.exception(
                                "Response analysis failed: warc=%s record=%d uri=%s",
                                warc_path,
                                record_number,
                                uri,
                            )
                            if args.strict:
                                raise

                        if (
                            args.progress_every
                            and counters["analyzed_responses"]
                            and counters["analyzed_responses"] % args.progress_every == 0
                        ):
                            print(
                                f"analyzed={counters['analyzed_responses']:,} "
                                f"errors={counters['analysis_errors']:,}",
                                file=sys.stderr,
                            )
                        if args.limit and counters["analyzed_responses"] >= args.limit:
                            stopped = True
                            break
            except Exception:
                counters["warc_file_errors"] += 1
                logging.exception("WARC scan failed: %s", warc_path)
                if args.strict:
                    raise

    unique_counts: Counter[str] = Counter()
    for mask in unique_masks.values():
        for field, bit in FIELD_BITS.items():
            if mask & bit:
                unique_counts[field] += 1

    report = {
        "scope": {
            "warc_directory": str(args.warc_dir),
            "first_file": args.first,
            "last_file": args.last,
            "limited_test_run": args.limit is not None,
        },
        "counts": dict(counters),
        "response_level": percentages(response_fields, counters["analyzed_responses"]),
        "unique_article_level": percentages(unique_counts, len(unique_masks)),
        "unique_articles": len(unique_masks),
        "definitions": {
            "exactFirstCreated": "Valid timezone-bearing datePublished from meta or JSON-LD.",
            "exactContentCreated": "Valid timezone-bearing dateModified from meta or JSON-LD.",
            "originalImageUrl": "At least one HTTP(S) URL in article img/src/srcset, image meta, or JSON-LD.",
            "imageCaption": "Non-empty figcaption, caption-class text, img alt/title, or JSON-LD image caption.",
            "genres": "At least one explicitly configured genre term in title/article text.",
            "infoSources": "At least one explicitly configured news-source name in title/article text.",
        },
        "output": str(args.output),
        "error_log": str(args.error_log),
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
    return 2 if counters["analysis_errors"] or counters["warc_file_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
