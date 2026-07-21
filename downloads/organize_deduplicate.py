#!/usr/bin/env python3
"""Convert, date-organize, and globally de-duplicate extracted article folders.

The program intentionally keeps no article-ID set in memory.  An article's
canonical ``YEAR/MONTH/DAY/ARTICLE_ID`` destination is the on-disk index: if
that directory already exists, the new occurrence is a duplicate.  When two
captures differ, the capture with the newer ``versionCreated`` wins; quality
and source shard number provide deterministic tie-breakers.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


STANDARD = {
    "name": "ninjs",
    "version": "3.2",
    "schema": "https://iptc.org/std/ninjs/ninjs-schema_3.2.json",
}
SHARD_NAME = re.compile(r"^file(?P<number>\d+)$")
URI_ARTICLE = re.compile(
    r"^/(?P<section>[^/]+)/(?P<date>\d{8})/(?P<id>[A-Za-z0-9]+)/*$"
)
SAFE_ID = re.compile(r"^[A-Za-z0-9]+$")
EXACT_DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


class PreflightError(RuntimeError):
    """A condition that must be fixed before any archive record is processed."""


def clean_uri(value: Any) -> str:
    uri = str(value or "").strip()
    parsed = urlsplit(uri)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def first_value(record: dict, *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, "", []):
            return value
    return None


def exact_date_value(record: dict, camel: str, legacy: str) -> str | None:
    """Keep evidenced date-times; omit legacy date-only values from ninjs 3.2."""
    value = first_value(record, camel, legacy)
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value if EXACT_DATETIME.fullmatch(value) else None


def normalized_list(value: Any) -> list[dict]:
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def article_parts(record: dict, source_json: Path) -> tuple[str, str, str]:
    uri_match = URI_ARTICLE.fullmatch(urlsplit(clean_uri(record.get("uri"))).path)
    alt_ids = normalized_list(first_value(record, "altIds", "altids"))
    article_id = next(
        (
            str(item.get("value"))
            for item in alt_ids
            if item.get("role") == "internal" and item.get("value")
        ),
        "",
    )
    if not article_id and uri_match:
        article_id = uri_match.group("id")
    if not article_id:
        article_id = source_json.stem
    if not SAFE_ID.fullmatch(article_id):
        raise ValueError(f"unsafe or missing article ID: {article_id!r}")

    date = uri_match.group("date") if uri_match else ""
    if not date:
        for camel, legacy in (
            ("firstCreated", "firstcreated"),
            ("versionCreated", "versioncreated"),
        ):
            date_value = first_value(record, camel, legacy)
            if not isinstance(date_value, str):
                continue
            candidate = date_value[:10].replace("-", "")
            if re.fullmatch(r"(?:19|20)\d{6}", candidate):
                date = candidate
                break
    if not re.fullmatch(r"(?:19|20)\d{6}", date):
        raise ValueError("no valid article date in uri or firstCreated")
    section = uri_match.group("section") if uri_match else ""
    return article_id, date, section


def canonical_headlines(value: Any) -> list[dict]:
    result = []
    for item in normalized_list(value):
        text = item.get("value")
        if text:
            output = {"role": item.get("role") or "main", "value": str(text)}
            result.append(output)
    return result


def canonical_bodies(value: Any) -> list[dict]:
    result = []
    for item in normalized_list(value):
        text = item.get("value")
        if text is None:
            continue
        result.append(
            {
                "role": item.get("role") or "main",
                "contentType": item.get("contentType") or item.get("contenttype") or "text/plain",
                "value": str(text),
            }
        )
    return result


def canonical_associations(value: Any) -> list[dict]:
    result = []
    for index, item in enumerate(normalized_list(value)):
        if item.get("type") != "picture" and not item.get("uri"):
            continue
        uri = str(item.get("uri") or "").strip()
        if not uri:
            renditions = normalized_list(item.get("renditions"))
            uri = str(renditions[0].get("href") or "").strip() if renditions else ""
        if not uri:
            continue
        association = {
            "name": str(item.get("name") or f"picture{index}"),
            "uri": uri,
            "type": "picture",
        }
        captions = canonical_headlines(item.get("headlines"))
        if captions:
            for caption in captions:
                caption.pop("role", None)
            association["headlines"] = captions
        result.append(association)
    return result


def convert_record(record: dict, source_json: Path) -> tuple[dict, str, str]:
    """Return canonical ninjs 3.2 data, article ID, and compact date."""
    article_id, date, section = article_parts(record, source_json)
    associations = canonical_associations(record.get("associations"))
    subjects = normalized_list(record.get("subjects"))
    if not subjects and section:
        subjects = [{"name": section}]

    output: dict[str, Any] = {
        "uri": clean_uri(record.get("uri")),
        "standard": dict(STANDARD),
    }
    for camel, legacy in (
        ("firstCreated", "firstcreated"),
        ("versionCreated", "versioncreated"),
        ("contentCreated", "contentcreated"),
    ):
        value = exact_date_value(record, camel, legacy)
        if value:
            output[camel] = value

    output["type"] = "composite" if associations else "text"
    if associations:
        output["profile"] = "text-photo"
    output.update(
        {
            "language": str(record.get("language") or "zh-Hant-TW"),
            "headlines": canonical_headlines(record.get("headlines")),
            "subjects": subjects,
            "bodies": canonical_bodies(record.get("bodies")),
            "associations": associations,
            "by": str(record.get("by") or ""),
            "located": str(record.get("located") or "").removesuffix("報導").strip(),
            "altIds": [{"role": "internal", "value": article_id}],
        }
    )
    return output, article_id, date


def version_key(record: dict, shard_number: int) -> tuple:
    raw_version = record.get("versionCreated") or ""
    try:
        version = datetime.fromisoformat(str(raw_version).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        version = float("-inf")
    body_size = sum(len(str(item.get("value") or "")) for item in record.get("bodies", []))
    return version, body_size, len(record.get("associations", [])), shard_number


def write_json(path: Path, record: dict) -> None:
    temporary = path.with_suffix(".json.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temporary, path)


def install_candidate(source_dir: Path, target_dir: Path, article_id: str, record: dict) -> None:
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = target_dir.parent / f".{article_id}.incoming"
    old = target_dir.parent / f".{article_id}.replaced"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(source_dir, staging)
    json_paths = list(staging.glob("*.json"))
    source_name = f"{article_id}.json"
    for json_path in json_paths:
        if json_path.name == source_name or len(json_paths) == 1:
            write_json(json_path, record)
            break
    else:
        write_json(staging / f"{article_id}.json", record)

    if not target_dir.exists():
        os.replace(staging, target_dir)
        return
    if old.exists():
        shutil.rmtree(old)
    os.replace(target_dir, old)
    try:
        os.replace(staging, target_dir)
    except BaseException:
        os.replace(old, target_dir)
        raise
    shutil.rmtree(old)


def iter_shards(source: Path, start: int | None, end: int | None) -> Iterable[tuple[int, Path]]:
    shards = []
    for path in source.iterdir():
        match = SHARD_NAME.fullmatch(path.name)
        if not path.is_dir() or not match:
            continue
        number = int(match.group("number"))
        if start is not None and number < start:
            continue
        if end is not None and number > end:
            continue
        shards.append((number, path))
    yield from sorted(shards)


def find_article_json(article_dir: Path) -> Path | None:
    preferred = article_dir / f"{article_dir.name}.json"
    if preferred.is_file():
        return preferred
    return next((path for path in article_dir.glob("*.json") if path.is_file()), None)


def organize(args: argparse.Namespace) -> Counter:
    source = args.source.resolve()
    output = args.output.resolve()
    if not source.is_dir():
        raise PreflightError(f"source directory does not exist: {source}")
    if source == output or source in output.parents:
        raise PreflightError("output must not be the source or inside the source")
    if not output.exists():
        raise PreflightError(
            "HUMAN ACTION REQUIRED: the top-level output directory does not exist.\n"
            "No archive records were processed and the program will not create it.\n"
            f"After approval, create it yourself with:\n  mkdir -p {output}"
        )
    if not output.is_dir():
        raise PreflightError(f"output exists but is not a directory: {output}")
    if not os.access(output, os.W_OK | os.X_OK):
        raise PreflightError(
            "HUMAN ACTION REQUIRED: the output directory is not writable/searchable.\n"
            f"Ask the programmer to update its ownership or permissions: {output}"
        )
    if output.exists() and any(output.iterdir()) and not args.resume:
        raise PreflightError(
            f"output is not empty: {output}\n"
            "Inspect it first, then rerun with --resume if it is the intended partial output."
        )
    report = args.report or output.with_name(f"{output.name}_duplicates.tsv")
    errors = output.with_name(f"{output.name}_errors.tsv")
    for auxiliary in (report, errors):
        if not auxiliary.parent.is_dir():
            raise PreflightError(
                "HUMAN ACTION REQUIRED: a report parent directory does not exist.\n"
                f"Create it yourself before running:\n  mkdir -p {auxiliary.parent}"
            )
        if not os.access(auxiliary.parent, os.W_OK | os.X_OK):
            raise PreflightError(f"report directory is not writable: {auxiliary.parent}")

    print(f"Preflight OK: source={source}")
    print(f"Preflight OK: existing output={output}")
    print("The program will now create only YEAR/MONTH/DAY/ARTICLE_ID subdirectories.")
    counters: Counter[str] = Counter()

    with report.open("a", encoding="utf-8") as duplicate_log, errors.open(
        "a", encoding="utf-8"
    ) as error_log:
        if report.stat().st_size == 0:
            duplicate_log.write("article_id\tkept\tdiscarded\taction\n")
        if errors.stat().st_size == 0:
            error_log.write("source\terror\n")

        for shard_number, shard in iter_shards(source, args.start, args.end):
            counters["shards"] += 1
            for article_dir in shard.iterdir():
                if args.max_occurrences is not None and counters["occurrences"] >= args.max_occurrences:
                    break
                if not article_dir.is_dir():
                    continue
                source_json = find_article_json(article_dir)
                if source_json is None:
                    counters["missing_json"] += 1
                    continue
                counters["occurrences"] += 1
                try:
                    with source_json.open("r", encoding="utf-8") as stream:
                        raw = json.load(stream)
                    if not isinstance(raw, dict):
                        raise TypeError("article JSON is not an object")
                    record, article_id, compact_date = convert_record(raw, source_json)
                    target = output / compact_date[:4] / compact_date[4:6] / compact_date[6:] / article_id
                    if not target.exists():
                        install_candidate(article_dir, target, article_id, record)
                        counters["unique"] += 1
                        continue

                    counters["duplicates"] += 1
                    target_json = find_article_json(target)
                    if target_json is None:
                        replace = True
                        existing = {}
                    else:
                        with target_json.open("r", encoding="utf-8") as stream:
                            existing = json.load(stream)
                        replace = version_key(record, shard_number) > version_key(existing, -1)
                    if replace:
                        install_candidate(article_dir, target, article_id, record)
                        counters["replaced"] += 1
                        duplicate_log.write(
                            f"{article_id}\t{source_json}\t{target_json or target}\treplaced\n"
                        )
                    else:
                        counters["discarded"] += 1
                        duplicate_log.write(
                            f"{article_id}\t{target_json}\t{source_json}\tdiscarded\n"
                        )
                except Exception as exc:  # keep a multi-day archive run progressing
                    counters["errors"] += 1
                    error_log.write(f"{source_json}\t{type(exc).__name__}: {exc}\n")

            print(
                f"file{shard_number}: occurrences={counters['occurrences']:,} "
                f"unique={counters['unique']:,} duplicates={counters['duplicates']:,} "
                f"errors={counters['errors']:,}",
                flush=True,
            )
            if args.max_occurrences is not None and counters["occurrences"] >= args.max_occurrences:
                break
    return counters


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="directory containing file0 ... file803")
    parser.add_argument("output", type=Path, help="new YEAR/MONTH/DAY/ARTICLE_ID tree")
    parser.add_argument("--start", type=int, help="first shard number, inclusive")
    parser.add_argument("--end", type=int, help="last shard number, inclusive")
    parser.add_argument("--resume", action="store_true", help="continue into an existing output")
    parser.add_argument("--max-occurrences", type=int, help="stop early for a smoke test")
    parser.add_argument("--report", type=Path, help="duplicate TSV path (outside data tree by default)")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        summary = organize(parse_args())
    except PreflightError as exc:
        print(f"PRE-FLIGHT STOP\n{exc}")
        raise SystemExit(2) from None
    print(json.dumps(dict(summary), indent=2, sort_keys=True))
