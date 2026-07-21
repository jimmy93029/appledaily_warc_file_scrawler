#!/usr/bin/env python3
"""Convert one WARC file into corrected ninjs 3.2 article directories."""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from fastwarc import ArchiveIterator

from extract_image2 import extract_image_info, image_output_path, url_keys
from extract_text import extract_text, valid_content, valid_url
from organize_deduplicate import (
    convert_record,
    find_article_json,
    install_candidate,
    version_key,
)
from utils_and_ninjs3 import (
    article_parts,
    decode_html,
    decode_response_content,
    meta_data,
    write_json,
)


SHARD_FILE = re.compile(r"^file(?P<number>\d+)(?:\.warc)?$")


def configure_logger(warc_name: str) -> logging.Logger:
    """Log errors to stderr so the nohup log stays outside the data tree."""
    logger = logging.getLogger(f"warc:{warc_name}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def shard_number(path: Path) -> int:
    match = SHARD_FILE.fullmatch(path.name)
    if not match:
        raise ValueError(f"WARC filename must look like fileN.warc: {path}")
    return int(match.group("number"))


def open_duplicate_log(output_root: Path):
    path = output_root.with_name(f"{output_root.name}_duplicates.tsv")
    stream = path.open("a", encoding="utf-8")
    if path.stat().st_size == 0:
        stream.write("article_id\tkept\tdiscarded\taction\n")
        stream.flush()
    return stream


def merge_evidence(existing: dict, incoming: dict) -> None:
    for source in incoming.get("sources", []):
        if source not in existing["sources"]:
            existing["sources"].append(source)
    for caption in incoming.get("captions", []):
        if caption not in existing["captions"]:
            existing["captions"].append(caption)


def merge_article(existing: dict, incoming: dict) -> None:
    if len(incoming["content"]) > len(existing["content"]):
        for field in ("title", "content", "raw_credit", "method", "uri", "warc_date"):
            existing[field] = incoming[field]
    for field in ("published_candidates", "modified_candidates"):
        for candidate in incoming[field]:
            if candidate not in existing[field]:
                existing[field].append(candidate)
    for url, evidence in incoming["image_candidates"].items():
        if url not in existing["image_candidates"]:
            existing["image_candidates"][url] = evidence
        else:
            merge_evidence(existing["image_candidates"][url], evidence)


def process_warc(
    file_path: str,
    output_base_dir: str = "/mnt/data/datastw2",
    max_records: int | None = None,
) -> dict:
    warc_path = Path(file_path)
    output_root = Path(output_base_dir)
    if not output_root.is_dir():
        raise FileNotFoundError(
            "HUMAN ACTION REQUIRED: create the output root before processing: "
            f"{output_root}"
        )
    current_shard = shard_number(warc_path)
    logger = configure_logger(warc_path.name)
    counters: Counter[str] = Counter()
    articles: dict[str, dict] = {}

    for stale in output_root.glob(f".{warc_path.stem}.incoming-*"):
        if stale.is_dir():
            shutil.rmtree(stale)
        else:
            stale.unlink()
    staging_context = tempfile.TemporaryDirectory(
        prefix=f".{warc_path.stem}.incoming-", dir=output_root
    )
    output_dir = Path(staging_context.name)

    print(f"Processing text: {warc_path}")
    try:
        with warc_path.open("rb") as stream:
            for record_number, record in enumerate(ArchiveIterator(stream, parse_http=True), start=1):
                counters["first_pass_records"] += 1
                if max_records and record_number > max_records:
                    break
                if record.headers.get("WARC-Type") != "response":
                    continue
                if not record.is_http or not record.http_headers:
                    continue
                if "200 OK" not in (record.http_headers.status_line or ""):
                    continue
                uri = record.headers.get("WARC-Target-URI", "")
                content_type = record.http_headers.get("Content-Type", "")
                if not valid_url(content_type, uri):
                    continue
                counters["article_candidates"] += 1

                try:
                    article_id, _date, _section = article_parts(uri)
                    html = decode_html(record)
                    extracted = extract_text(html)
                    if not extracted["title"] or not valid_content(extracted["content"]):
                        counters["rejected_content"] += 1
                        continue
                    candidate = {
                        **extracted,
                        "uri": uri,
                        "warc_date": record.headers.get("WARC-Date"),
                        "image_candidates": extract_image_info(html, uri, article_id),
                        "matched_images": {},
                    }
                    if article_id in articles:
                        counters["duplicate_article_responses"] += 1
                        merge_article(articles[article_id], candidate)
                    else:
                        articles[article_id] = candidate
                        counters["unique_articles"] += 1
                except Exception:
                    counters["article_errors"] += 1
                    logger.exception(
                        "Article extraction failed: warc=%s record=%d uri=%s",
                        warc_path,
                        record_number,
                        uri,
                    )
    except Exception:
        counters["fatal_first_pass_errors"] += 1
        logger.exception("First WARC pass failed: %s", warc_path)

    reverse_index: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for article_id, article in articles.items():
        for original_url in article["image_candidates"]:
            for key in url_keys(original_url):
                reference = (article_id, original_url)
                if reference not in reverse_index[key]:
                    reverse_index[key].append(reference)
    counters["retained_image_candidates"] = sum(
        len(article["image_candidates"]) for article in articles.values()
    )

    print(f"Processing images: {warc_path}")
    try:
        with warc_path.open("rb") as stream:
            for record_number, record in enumerate(ArchiveIterator(stream, parse_http=True), start=1):
                counters["second_pass_records"] += 1
                if max_records and record_number > max_records:
                    break
                if record.headers.get("WARC-Type") != "response":
                    continue
                if not record.is_http or not record.http_headers:
                    continue
                if "200 OK" not in (record.http_headers.status_line or ""):
                    continue
                content_type = record.http_headers.get("Content-Type", "").lower()
                if not content_type.startswith("image/"):
                    continue
                uri = record.headers.get("WARC-Target-URI", "")
                references = []
                for key in url_keys(uri):
                    references.extend(reverse_index.get(key, []))
                references = list(dict.fromkeys(references))
                if not references:
                    continue

                try:
                    image_bytes = decode_response_content(record)
                    for article_id, original_url in references:
                        article = articles[article_id]
                        if original_url in article["matched_images"]:
                            continue
                        article_dir = output_dir / article_id
                        saved_path = image_output_path(str(article_dir), original_url, content_type)
                        with open(saved_path, "wb") as image_file:
                            image_file.write(image_bytes)
                        evidence = dict(article["image_candidates"][original_url])
                        evidence["content_type"] = content_type.split(";", 1)[0]
                        evidence["saved_path"] = saved_path
                        evidence["rendition_href"] = f"./{article_id}/img/{Path(saved_path).name}"
                        article["matched_images"][original_url] = evidence
                        counters["saved_article_images"] += 1
                except Exception:
                    counters["image_errors"] += 1
                    logger.exception(
                        "Image extraction failed: warc=%s record=%d uri=%s",
                        warc_path,
                        record_number,
                        uri,
                    )
    except Exception:
        counters["fatal_second_pass_errors"] += 1
        logger.exception("Second WARC pass failed: %s", warc_path)

    with open_duplicate_log(output_root) as duplicate_log:
        for article_id, article in articles.items():
            try:
                images = list(article["matched_images"].values())
                data = meta_data(
                    title=article["title"],
                    content=article["content"],
                    raw_credit=article["raw_credit"],
                    warc_date=article["warc_date"],
                    uri=article["uri"],
                    published_candidates=article["published_candidates"],
                    modified_candidates=article["modified_candidates"],
                    images=images,
                )
                article_dir = output_dir / article_id
                source_json = write_json(data, article_dir, article_id)
                uri_date = article_parts(article["uri"])[1]
                if not re.fullmatch(r"(?:19|20)\d{6}", uri_date):
                    if data.get("firstCreated"):
                        counters["folder_date_from_first_created"] += 1
                    else:
                        counters["folder_date_from_warc_capture"] += 1
                record, canonical_id, compact_date = convert_record(data, source_json)
                target = (
                    output_root
                    / compact_date[:4]
                    / compact_date[4:6]
                    / compact_date[6:]
                    / canonical_id
                )
                if not target.exists():
                    install_candidate(article_dir, target, canonical_id, record)
                    counters["written_articles"] += 1
                    counters["unique_articles_written"] += 1
                    continue

                counters["global_duplicates"] += 1
                target_json = find_article_json(target)
                if target_json is None:
                    replace = True
                    existing = {}
                else:
                    with target_json.open("r", encoding="utf-8") as stream:
                        existing = json.load(stream)
                    replace = version_key(record, current_shard) > version_key(existing, -1)
                if replace:
                    install_candidate(article_dir, target, canonical_id, record)
                    counters["written_articles"] += 1
                    counters["duplicates_replaced"] += 1
                    duplicate_log.write(
                        f"{canonical_id}\t{warc_path}#{canonical_id}\t"
                        f"{target_json or target}\treplaced\n"
                    )
                else:
                    counters["duplicates_discarded"] += 1
                    duplicate_log.write(
                        f"{canonical_id}\t{target_json}\t"
                        f"{warc_path}#{canonical_id}\tdiscarded\n"
                    )
            except Exception:
                counters["write_errors"] += 1
                logger.exception("ninjs write failed: warc=%s article_id=%s", warc_path, article_id)

    staging_context.cleanup()

    counters["unmatched_image_candidates"] = max(
        counters["retained_image_candidates"] - counters["saved_article_images"], 0
    )
    summary = {
        "warc": str(warc_path),
        "output_directory": str(output_root),
        "layout": "YEAR/MONTH/DAY/ARTICLE_ID",
        **counters,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("warc", help="Input .warc file")
    parser.add_argument("--output", default="/mnt/data/datastw2")
    parser.add_argument("--max-records", type=int, help="Bound both passes for testing")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = process_warc(args.warc, args.output, args.max_records)
    fatal = result.get("fatal_first_pass_errors", 0) + result.get("fatal_second_pass_errors", 0)
    raise SystemExit(2 if fatal else 0)
