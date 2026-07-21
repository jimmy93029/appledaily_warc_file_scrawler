#!/usr/bin/env python3
"""Verify image URL and caption extraction from diagnosis body.html dumps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from extract_image2 import extract_image_info, url_keys


DEFAULT_DIAGNOSIS_DIR = Path("/mnt/data/working2/file364_article_diagnosis")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def image_records_for_article(article_dir: Path) -> list[dict[str, Any]]:
    records = []
    for meta_path in sorted((article_dir / "image").glob("*/meta.json")):
        meta = read_json(meta_path)
        records.append(
            {
                "record": meta_path.parent.name,
                "uri": meta.get("warc_target_uri", ""),
                "body_path": meta.get("body_path"),
                "body_size": meta.get("body_size"),
            }
        )
    return records


def matching_image_records(url: str, image_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_keys = url_keys(url)
    return [
        record
        for record in image_records
        if candidate_keys & url_keys(record["uri"])
    ]


def verify_article(article_dir: Path) -> dict[str, Any]:
    article_id = article_dir.name
    image_records = image_records_for_article(article_dir)
    article_results = []

    for body_path in sorted((article_dir / "article").glob("*/body.html")):
        record_dir = body_path.parent
        meta = read_json(record_dir / "meta.json")
        html = body_path.read_text(encoding="utf-8")
        candidates = extract_image_info(html, meta["warc_target_uri"], article_id)

        candidate_results = []
        for url, evidence in candidates.items():
            captions = [
                caption.get("value", "")
                for caption in evidence.get("captions", [])
                if caption.get("value", "").strip()
            ]
            matches = matching_image_records(url, image_records)
            candidate_results.append(
                {
                    "url": url,
                    "sources": evidence.get("sources", []),
                    "captions": captions,
                    "has_caption": bool(captions),
                    "matching_image_records": matches,
                    "has_matching_image_record": bool(matches),
                }
            )

        article_results.append(
            {
                "record": record_dir.name,
                "body_html": str(body_path),
                "uri": meta["warc_target_uri"],
                "candidate_count": len(candidate_results),
                "captioned_candidate_count": sum(
                    1 for candidate in candidate_results if candidate["has_caption"]
                ),
                "matched_candidate_count": sum(
                    1 for candidate in candidate_results if candidate["has_matching_image_record"]
                ),
                "candidates": candidate_results,
            }
        )

    all_candidates = [
        candidate
        for record in article_results
        for candidate in record["candidates"]
    ]
    unique_urls = {}
    for candidate in all_candidates:
        unique_urls.setdefault(candidate["url"], candidate)

    return {
        "article_id": article_id,
        "article_record_count": len(article_results),
        "dumped_image_record_count": len(image_records),
        "unique_candidate_count": len(unique_urls),
        "unique_captioned_candidate_count": sum(
            1 for candidate in unique_urls.values() if candidate["has_caption"]
        ),
        "unique_matched_candidate_count": sum(
            1 for candidate in unique_urls.values() if candidate["has_matching_image_record"]
        ),
        "article_records": article_results,
    }


def print_human_summary(report: dict[str, Any]) -> None:
    for article in report["articles"]:
        print(f"\n=== {article['article_id']} ===")
        print(
            "article_records={article_record_count} "
            "dumped_image_records={dumped_image_record_count} "
            "unique_candidates={unique_candidate_count} "
            "captioned={unique_captioned_candidate_count} "
            "matched_images={unique_matched_candidate_count}".format(**article)
        )
        for record in article["article_records"]:
            print(f"- {record['record']}: {record['candidate_count']} candidates")
            print(f"  html: {record['body_html']}")
            for candidate in record["candidates"]:
                status = []
                status.append("caption" if candidate["has_caption"] else "NO_CAPTION")
                status.append("matched" if candidate["has_matching_image_record"] else "NO_IMAGE_RECORD")
                print(f"  [{', '.join(status)}] {candidate['url']}")
                for caption in candidate["captions"]:
                    print(f"    caption: {caption}")
                for match in candidate["matching_image_records"]:
                    print(f"    image: {match['record']} {match['body_path']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diagnosis_dir", nargs="?", type=Path, default=DEFAULT_DIAGNOSIS_DIR)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    args = parser.parse_args()

    article_dirs = [
        path
        for path in sorted(args.diagnosis_dir.iterdir())
        if path.is_dir() and (path / "article").is_dir()
    ]
    report = {
        "diagnosis_dir": str(args.diagnosis_dir),
        "articles": [verify_article(article_dir) for article_dir in article_dirs],
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
