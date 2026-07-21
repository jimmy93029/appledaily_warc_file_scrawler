#!/usr/bin/env python3
"""Dump and diagnose selected article/image records from WARC files."""

from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path
from typing import Any

from fastwarc import ArchiveIterator

from extract_image2 import extract_image_info, url_keys
from extract_text import extract_text, valid_content, valid_url
from utils_and_ninjs3 import article_parts, decode_html, decode_response_content


DEFAULT_IDS = (
    "REEGHV4YGNHNZF4CDZRQZLIS5U",
    "MQ4K56B4OGGLOFYB5ODR3ZM4AA",
)


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "record"


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def response_meta(record: Any, warc_path: Path, record_number: int) -> dict[str, Any]:
    headers = dict(record.headers.items())
    http_headers = dict(record.http_headers.items()) if record.http_headers else {}
    return {
        "warc": str(warc_path),
        "record_number": record_number,
        "warc_target_uri": record.headers.get("WARC-Target-URI", ""),
        "warc_date": record.headers.get("WARC-Date"),
        "warc_headers": headers,
        "http_status": record.http_headers.status_line if record.http_headers else None,
        "http_headers": http_headers,
    }


def extract_article_payload(record: Any, article_id: str) -> dict[str, Any]:
    uri = record.headers.get("WARC-Target-URI", "")
    html = decode_html(record)
    extracted = extract_text(html)
    image_candidates = extract_image_info(html, uri, article_id)
    return {
        "uri": uri,
        "title": extracted["title"],
        "content_length": len(extracted["content"]),
        "valid_content": valid_content(extracted["content"]),
        "raw_credit": extracted["raw_credit"],
        "published_candidates": extracted["published_candidates"],
        "modified_candidates": extracted["modified_candidates"],
        "image_candidates": image_candidates,
        "html": html,
        "extracted": extracted,
    }


def classify_record(record: Any, article_ids: tuple[str, ...]) -> tuple[str | None, str | None]:
    uri = record.headers.get("WARC-Target-URI", "")
    lowered_uri = uri.lower()
    content_type = record.http_headers.get("Content-Type", "").lower() if record.http_headers else ""
    for article_id in article_ids:
        if article_id.lower() in lowered_uri:
            if content_type.startswith("image/"):
                return article_id, "image"
            if valid_url(content_type, uri):
                try:
                    found_id, _date, _section = article_parts(uri)
                except ValueError:
                    found_id = None
                if found_id == article_id:
                    return article_id, "article"
            return article_id, "related"
    return None, None


def dump_record(
    *,
    output_dir: Path,
    article_id: str,
    kind: str,
    record: Any,
    warc_path: Path,
    record_number: int,
) -> dict[str, Any]:
    meta = response_meta(record, warc_path, record_number)
    record_dir = output_dir / article_id / kind / f"{warc_path.stem}_record{record_number}"
    write_text(record_dir / "meta.json", json.dumps(meta, ensure_ascii=False, indent=2))

    content_type = record.http_headers.get("Content-Type", "") if record.http_headers else ""
    if kind == "article":
        payload = extract_article_payload(record, article_id)
        write_text(record_dir / "body.html", payload["html"])
        write_text(record_dir / "extracted.json", json.dumps(payload["extracted"], ensure_ascii=False, indent=2))
        write_text(
            record_dir / "image_candidates.json",
            json.dumps(payload["image_candidates"], ensure_ascii=False, indent=2),
        )
        meta.update(
            {
                "kind": kind,
                "dump_dir": str(record_dir),
                "title": payload["title"],
                "content_length": payload["content_length"],
                "valid_content": payload["valid_content"],
                "image_candidate_count": len(payload["image_candidates"]),
                "image_candidates": payload["image_candidates"],
            }
        )
    elif kind == "image":
        body = decode_response_content(record)
        suffix = Path(meta["warc_target_uri"]).suffix or ".bin"
        body_path = record_dir / f"body{suffix}"
        write_bytes(body_path, body)
        meta.update(
            {
                "kind": kind,
                "dump_dir": str(record_dir),
                "body_path": str(body_path),
                "body_size": len(body),
                "content_type": content_type.split(";", 1)[0],
            }
        )
    else:
        body = decode_response_content(record)
        write_text(record_dir / "body.base64.txt", base64.b64encode(body).decode("ascii"))
        meta.update(
            {
                "kind": kind,
                "dump_dir": str(record_dir),
                "body_size": len(body),
                "content_type": content_type,
            }
        )
    return meta


def summarize(records: list[dict[str, Any]], article_ids: tuple[str, ...]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for article_id in article_ids:
        article_records = [record for record in records if record["kind"] == "article" and article_id in record["warc_target_uri"]]
        image_records = [record for record in records if record["kind"] == "image" and article_id in record["warc_target_uri"]]
        candidates: dict[str, dict[str, Any]] = {}
        for record in article_records:
            for url, evidence in record.get("image_candidates", {}).items():
                candidates.setdefault(url, evidence)

        matched = []
        unmatched = []
        for url, evidence in candidates.items():
            hits = [
                image
                for image in image_records
                if url_keys(url) & url_keys(image["warc_target_uri"])
            ]
            item = {
                "url": url,
                "sources": evidence.get("sources", []),
                "captions": evidence.get("captions", []),
                "matching_image_records": [
                    {
                        "warc": hit["warc"],
                        "record_number": hit["record_number"],
                        "uri": hit["warc_target_uri"],
                        "body_path": hit.get("body_path"),
                    }
                    for hit in hits
                ],
            }
            if hits:
                matched.append(item)
            else:
                unmatched.append(item)

        summary[article_id] = {
            "article_record_count": len(article_records),
            "article_records": [
                {
                    "warc": record["warc"],
                    "record_number": record["record_number"],
                    "uri": record["warc_target_uri"],
                    "title": record.get("title"),
                    "content_length": record.get("content_length"),
                    "valid_content": record.get("valid_content"),
                    "dump_dir": record.get("dump_dir"),
                }
                for record in article_records
            ],
            "image_record_count": len(image_records),
            "image_records": [
                {
                    "warc": record["warc"],
                    "record_number": record["record_number"],
                    "uri": record["warc_target_uri"],
                    "body_path": record.get("body_path"),
                    "body_size": record.get("body_size"),
                }
                for record in image_records
            ],
            "candidate_count": len(candidates),
            "matched_candidates": matched,
            "unmatched_candidates": unmatched,
            "captionless_candidates": [
                {
                    "url": url,
                    "sources": evidence.get("sources", []),
                }
                for url, evidence in candidates.items()
                if not evidence.get("captions")
            ],
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("warcs", nargs="+", type=Path)
    parser.add_argument("--article-id", action="append", dest="article_ids")
    parser.add_argument("--output", type=Path, default=Path("/tmp/warc_article_diagnosis"))
    args = parser.parse_args()

    article_ids = tuple(args.article_ids or DEFAULT_IDS)
    records: list[dict[str, Any]] = []
    args.output.mkdir(parents=True, exist_ok=True)

    for warc_path in args.warcs:
        with warc_path.open("rb") as stream:
            for record_number, record in enumerate(ArchiveIterator(stream, parse_http=True), start=1):
                if record.headers.get("WARC-Type") != "response":
                    continue
                if not record.is_http or not record.http_headers:
                    continue
                if "200 OK" not in (record.http_headers.status_line or ""):
                    continue
                article_id, kind = classify_record(record, article_ids)
                if not article_id or not kind:
                    continue
                try:
                    records.append(
                        dump_record(
                            output_dir=args.output,
                            article_id=article_id,
                            kind=kind,
                            record=record,
                            warc_path=warc_path,
                            record_number=record_number,
                        )
                    )
                except Exception as exc:
                    records.append(
                        {
                            "warc": str(warc_path),
                            "record_number": record_number,
                            "warc_target_uri": record.headers.get("WARC-Target-URI", ""),
                            "kind": kind,
                            "error": repr(exc),
                        }
                    )

    summary = summarize(records, article_ids)
    write_text(args.output / "records.json", json.dumps(records, ensure_ascii=False, indent=2))
    write_text(args.output / "summary.json", json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nWrote full dumps to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
