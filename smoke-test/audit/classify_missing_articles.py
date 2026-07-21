#!/usr/bin/env python3
"""Classify missing Apple Daily IDs using old JSON and available WARC files.

The report distinguishes static URL-filter causes from evidence in the WARC
files actually supplied.  "not_found_in_available_warcs" never claims that an
article is absent from the complete 803-file collection.
"""

from __future__ import annotations

import argparse
import csv
import json
import multiprocessing
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from fastwarc import ArchiveIterator


DEFAULT_MISSING_REPORT = Path(
    "/mnt/data/working3/appledaily_diff/missing_canonical_articles.json"
)
DEFAULT_LEFT_ONLY = Path(
    "/mnt/data/working3/appledaily_diff/appledaily2_only.csv"
)
DEFAULT_APPLEDAILY2 = Path("/mnt/data/appledaily2")
DEFAULT_OUTPUT = Path(
    "/mnt/data/working3/appledaily_diff/missing_articles_classified.json"
)
DEFAULT_PIPELINE = Path("/home/jimmywu/sinica/venv/codes/downloads_new2")
DEFAULT_WARCS = (
    Path("/mnt/data/working3/files_current801/file801.warc"),
    Path("/mnt/data/working3/files_current801/file802.warc"),
)
ARTICLE_ID = re.compile(r"^[A-Za-z0-9]+$")
ARTICLE_PATH = re.compile(r"^/[^/]+/\d{8}/(?P<id>[A-Za-z0-9]+)/?$")
DOMAIN_ROOTS = ("appledaily.com", "appledaily.com.tw")


def log(message: str) -> None:
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S%z")
    print(f"[{stamp}] {message}", flush=True)


def normalize_id(raw: str) -> str | None:
    value = unquote((raw or "").strip())
    value = value.split("?", 1)[0].split("#", 1)[0].strip().rstrip("/")
    return value if ARTICLE_ID.fullmatch(value) else None


def apple_host(hostname: str | None) -> bool:
    hostname = (hostname or "").lower().rstrip(".")
    return any(hostname == root or hostname.endswith(f".{root}") for root in DOMAIN_ROOTS)


def fixed_url_category(uri: str) -> str:
    parts = urlsplit(uri)
    if parts.scheme not in {"http", "https"}:
        return "excluded_scheme"
    if not apple_host(parts.hostname):
        return "excluded_host"
    if not ARTICLE_PATH.fullmatch(parts.path):
        return "excluded_article_path"
    return "passes_fixed_url_filter"


def uri_article_id(uri: str) -> str | None:
    parts = urlsplit(uri)
    match = ARTICLE_PATH.fullmatch(parts.path)
    if match:
        return match.group("id")
    path_parts = [part for part in parts.path.rstrip("/").split("/") if part]
    return path_parts[-1] if path_parts and ARTICLE_ID.fullmatch(path_parts[-1]) else None


def load_missing(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    values = data.get("genuinely_missing_ids")
    if not isinstance(values, list):
        raise ValueError("missing report has no genuinely_missing_ids list")
    return {str(value) for value in values if ARTICLE_ID.fullmatch(str(value))}


def load_old_evidence(
    csv_path: Path, appledaily2: Path, missing: set[str]
) -> tuple[dict[str, list[dict[str, Any]]], Counter]:
    selected: dict[str, list[dict[str, str]]] = defaultdict(list)
    with csv_path.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            article_id = normalize_id(str(row.get("key") or ""))
            if article_id in missing:
                selected[article_id].append(
                    {"key": str(row.get("key") or ""), "path": str(row.get("path") or "")}
                )

    evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    counts: Counter[str] = Counter()
    for index, (article_id, rows) in enumerate(selected.items(), start=1):
        for row in rows:
            source = appledaily2 / row["path"]
            item: dict[str, Any] = {"key": row["key"], "path": row["path"]}
            try:
                with source.open("r", encoding="utf-8") as stream:
                    record = json.load(stream)
                uri = str(record.get("uri") or "")
                item.update(
                    {
                        "uri": uri,
                        "host": urlsplit(uri).hostname or "",
                        "url_category": fixed_url_category(uri),
                    }
                )
                counts[f"old_rows_{item['url_category']}"] += 1
            except Exception as exc:
                item["read_error"] = f"{type(exc).__name__}: {exc}"
                counts["old_json_read_errors"] += 1
            evidence[article_id].append(item)
        if index % 250 == 0:
            log(f"loaded old JSON evidence for {index:,}/{len(selected):,} IDs")
    counts["missing_ids_with_old_rows"] = len(evidence)
    counts["missing_ids_without_old_rows"] = len(missing - set(evidence))
    for items in evidence.values():
        categories = {item.get("url_category") for item in items if item.get("url_category")}
        for category in categories:
            counts[f"ids_{category}"] += 1
    return dict(evidence), counts


def scan_warc(task: tuple[str, set[str], str]) -> tuple[str, dict[str, list[dict]], Counter]:
    warc_text, targets, pipeline_text = task
    sys.path.insert(0, pipeline_text)
    from extract_text import extract_text, valid_content, valid_url
    from utils_and_ninjs3 import decode_html

    warc = Path(warc_text)
    found: dict[str, list[dict]] = defaultdict(list)
    counts: Counter[str] = Counter()
    started = time.monotonic()
    log(f"scanning available WARC {warc}")
    with warc.open("rb") as stream:
        for record_number, record in enumerate(ArchiveIterator(stream, parse_http=True), start=1):
            counts["records_scanned"] += 1
            if record_number % 100_000 == 0:
                log(
                    f"{warc.name}: records={record_number:,}, target responses="
                    f"{counts['target_responses']:,}, elapsed={time.monotonic() - started:.1f}s"
                )
            uri = record.headers.get("WARC-Target-URI", "")
            article_id = uri_article_id(uri)
            if article_id not in targets:
                continue
            warc_type = record.headers.get("WARC-Type", "")
            item: dict[str, Any] = {
                "warc": str(warc),
                "record_number": record_number,
                "warc_type": warc_type,
                "uri": uri,
            }
            if warc_type != "response":
                counts["target_non_response_records"] += 1
                found[article_id].append(item)
                continue
            counts["target_responses"] += 1
            status = record.http_headers.status_line if record.is_http and record.http_headers else ""
            content_type = (
                record.http_headers.get("Content-Type", "")
                if record.is_http and record.http_headers
                else ""
            )
            item.update({"status": status, "content_type": content_type})
            if "200 OK" not in (status or ""):
                item["classification"] = "non_200_response"
            elif not valid_url(content_type, uri):
                item["classification"] = "url_or_content_type_filtered_after_fix"
            else:
                try:
                    extracted = extract_text(decode_html(record))
                    item.update(
                        {
                            "classification": (
                                "accepted_after_fix"
                                if extracted["title"] and valid_content(extracted["content"])
                                else "rejected_content_after_fix"
                            ),
                            "extraction_method": extracted["method"],
                            "title_present": bool(extracted["title"]),
                            "content_length": len(extracted["content"]),
                        }
                    )
                except Exception as exc:
                    item["classification"] = "extraction_error"
                    item["error"] = f"{type(exc).__name__}: {exc}"
            counts[item["classification"]] += 1
            found[article_id].append(item)
    log(
        f"finished {warc.name}: records={counts['records_scanned']:,}, "
        f"target responses={counts['target_responses']:,}"
    )
    return str(warc), dict(found), counts


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    os.replace(temporary, path)


def run(args: argparse.Namespace) -> dict:
    missing = load_missing(args.missing_report)
    log(f"loaded {len(missing):,} genuinely missing canonical IDs")
    old_evidence, counts = load_old_evidence(args.left_only_csv, args.appledaily2, missing)

    warcs = [path.resolve() for path in args.warc if path.is_file()]
    missing_warcs = [str(path) for path in args.warc if not path.is_file()]
    if missing_warcs:
        log(f"warning: unavailable WARC paths: {missing_warcs}")
    combined: dict[str, list[dict]] = defaultdict(list)
    if warcs:
        tasks = [(str(path), missing, str(args.pipeline.resolve())) for path in warcs]
        with multiprocessing.Pool(processes=min(args.workers, len(tasks))) as pool:
            for _warc, evidence, warc_counts in pool.imap_unordered(scan_warc, tasks):
                counts.update(warc_counts)
                for article_id, items in evidence.items():
                    combined[article_id].extend(items)

    found_ids = set(combined)
    counts["genuinely_missing_ids"] = len(missing)
    counts["available_warcs_scanned"] = len(warcs)
    counts["ids_found_in_available_warcs"] = len(found_ids)
    counts["ids_not_found_in_available_warcs"] = len(missing - found_ids)
    articles = {}
    for article_id in sorted(missing):
        articles[article_id] = {
            "old_json_evidence": old_evidence.get(article_id, []),
            "available_warc_evidence": combined.get(article_id, []),
            "available_warc_status": (
                "found" if article_id in found_ids else "not_found_in_available_warcs"
            ),
        }
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope_warning": (
            "WARC absence applies only to the listed available_warcs; it does not prove "
            "absence from the complete 803-shard archive."
        ),
        "inputs": {
            "missing_report": str(args.missing_report.resolve()),
            "left_only_csv": str(args.left_only_csv.resolve()),
            "appledaily2": str(args.appledaily2.resolve()),
            "available_warcs": [str(path) for path in warcs],
            "unavailable_warcs": missing_warcs,
        },
        "summary": dict(counts),
        "articles": articles,
    }
    atomic_json(args.output, report)
    log(f"classification report written to {args.output}")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--missing-report", type=Path, default=DEFAULT_MISSING_REPORT)
    parser.add_argument("--left-only-csv", type=Path, default=DEFAULT_LEFT_ONLY)
    parser.add_argument("--appledaily2", type=Path, default=DEFAULT_APPLEDAILY2)
    parser.add_argument("--pipeline", type=Path, default=DEFAULT_PIPELINE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--warc", type=Path, nargs="*", default=list(DEFAULT_WARCS))
    parser.add_argument("--workers", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    try:
        report = run(parse_args())
    except KeyboardInterrupt:
        log("interrupted; final report was not written")
        return 130
    except Exception as exc:
        log(f"ERROR: {type(exc).__name__}: {exc}")
        return 2
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
