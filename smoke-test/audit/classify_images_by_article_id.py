#!/usr/bin/env python3
"""Evaluate an article-ID-first image filter using WARC audit evidence.

The script consumes ``warc_recoverable_fields.jsonl`` and classifies every
discovered image URL. A missing article ID means "filtered candidate", not
proven advertising. Trusted counter-evidence (OG, JSON-LD and img tags) is
reported so possible false exclusions remain visible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = BASE_DIR / "warc_recoverable_fields.jsonl"
DEFAULT_OUTPUT = BASE_DIR / "images_classified_by_article_id.jsonl"
DEFAULT_REPORT = BASE_DIR / "images_classified_by_article_id_report.json"
ARTICLE_URI = re.compile(r"^/[^/]+/(?P<date>\d{8})/(?P<id>[A-Za-z0-9]+)/*$")


def parse_article_uri(uri: str) -> tuple[str, str]:
    match = ARTICLE_URI.fullmatch(urlsplit(uri).path)
    if not match:
        raise ValueError(f"unexpected article URI: {uri}")
    return match.group("id"), match.group("date")


def source_flags(sources: list[str]) -> dict[str, bool]:
    return {
        "in_img_tag": any(source.startswith("img[") for source in sources),
        "in_og_image": any("og:image" in source for source in sources),
        "in_twitter_image": any("twitter:image" in source for source in sources),
        "in_json_ld": any(source.startswith("json-ld[") for source in sources),
    }


def classify_image(image: dict, article_id: str, article_date: str) -> dict:
    url = image["url"]
    decoded_url = unquote(url)
    path = unquote(urlsplit(url).path)
    flags = source_flags(image.get("sources", []))

    id_segment = f"/{article_id}/"
    contains_id = article_id.lower() in decoded_url.lower()
    contains_date = article_date in decoded_url
    article_img_path = id_segment.lower() in path.lower() and "/img/" in path.lower()
    exact_archive_path = (
        f"/{article_date}/{article_id}/img/".lower() in path.lower()
    )
    corroborated_img_og_jsonld = (
        flags["in_img_tag"] and flags["in_og_image"] and flags["in_json_ld"]
    )

    keep = contains_id or flags["in_og_image"] or flags["in_json_ld"]
    if contains_id:
        decision = "keep_article_id_match"
        confidence = "high" if article_img_path else "medium"
    elif keep:
        decision = "keep_og_or_json_ld"
        confidence = "high"
    else:
        decision = "filter_no_id_og_or_json_ld"
        confidence = "high"

    trusted_without_id = not contains_id and (
        flags["in_og_image"] or flags["in_json_ld"] or corroborated_img_og_jsonld
    )
    return {
        "url": url,
        "decision": decision,
        "confidence": confidence,
        "criteria": {
            "contains_article_id": contains_id,
            "contains_article_date": contains_date,
            "path_contains_article_id_img": article_img_path,
            "path_matches_date_article_id_img": exact_archive_path,
            **flags,
            "corroborated_img_og_jsonld": corroborated_img_og_jsonld,
        },
        "kept_metadata_exception": trusted_without_id,
        "sources": image.get("sources", []),
        "captions": image.get("captions", []),
    }


def update_counts(counts: Counter, classification: dict) -> None:
    counts["images"] += 1
    decision = classification["decision"]
    counts[decision] += 1
    if classification["kept_metadata_exception"]:
        counts["kept_metadata_exceptions"] += 1
    for criterion, present in classification["criteria"].items():
        if present:
            counts[f"criterion:{criterion}"] += 1


def percentages(counts: Counter) -> dict:
    total = counts["images"]
    return {
        key: {
            "count": value,
            "percentage": round(value * 100 / total, 4) if total else 0.0,
        }
        for key, value in sorted(counts.items())
        if key not in {"images", "responses"}
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--progress-every", type=int, default=10_000)
    parser.add_argument("--limit", type=int, help="Stop after N response records (testing).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    response_counts: Counter = Counter()
    unique_counts: Counter = Counter()
    seen_article_images: set[tuple[str, str]] = set()

    with args.input.open("r", encoding="utf-8-sig") as source, args.output.open(
        "w", encoding="utf-8"
    ) as output:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            article_id, article_date = parse_article_uri(record["uri"])
            classifications = []
            for image in record.get("evidence", {}).get("images", []):
                classification = classify_image(image, article_id, article_date)
                classifications.append(classification)
                update_counts(response_counts, classification)
                unique_key = (article_id, classification["url"])
                if unique_key not in seen_article_images:
                    seen_article_images.add(unique_key)
                    update_counts(unique_counts, classification)

            output.write(
                json.dumps(
                    {
                        "source_warc": record.get("source_warc"),
                        "record_number": record.get("record_number"),
                        "uri": record["uri"],
                        "article_id": article_id,
                        "article_date": article_date,
                        "kept_count": sum(
                            item["decision"].startswith("keep_")
                            for item in classifications
                        ),
                        "filtered_count": sum(
                            item["decision"].startswith("filter_")
                            for item in classifications
                        ),
                        "images": classifications,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            response_counts["responses"] += 1
            if args.progress_every and response_counts["responses"] % args.progress_every == 0:
                print(f"processed={response_counts['responses']:,}", file=sys.stderr)
            if args.limit and response_counts["responses"] >= args.limit:
                break

    report = {
        "input": str(args.input),
        "output": str(args.output),
        "response_records": response_counts["responses"],
        "response_image_occurrences": {
            "total": response_counts["images"],
            "metrics": percentages(response_counts),
        },
        "unique_article_image_pairs": {
            "total": unique_counts["images"],
            "metrics": percentages(unique_counts),
        },
        "decision_rule": (
            "Keep when the decoded image URL contains the article ID, or when "
            "the URL appears in og:image or JSON-LD image metadata."
        ),
        "limitation": (
            "The source audit recorded img-tag presence but not exact figure/container "
            "placement. OG/JSON-LD evidence is retained to expose possible false exclusions."
        ),
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
