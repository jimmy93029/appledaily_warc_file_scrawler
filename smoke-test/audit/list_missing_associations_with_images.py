#!/usr/bin/env python3
"""Find ninjs articles with empty associations but image files on disk.

The source tree is read-only. Each mismatch is written as one JSONL object
containing the complete original ninjs record and an inventory of its sibling
``img`` directory. Errors are logged with tracebacks rather than skipped.
"""

from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import os
import sys
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = Path("/mnt/data/appledaily2")
DEFAULT_OUTPUT = BASE_DIR / "missing_associations_with_images.jsonl"
DEFAULT_ERROR_LOG = BASE_DIR / "missing_associations_with_images.errors.log"


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


def image_inventory(image_dir: Path) -> list[dict]:
    images = []
    if not image_dir.is_dir():
        return images

    for path in sorted(image_dir.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.name.startswith("."):
            continue
        stat = path.stat()
        content_type, _ = mimetypes.guess_type(path.name)
        images.append(
            {
                "name": path.name,
                "stem": path.stem,
                "suffix": path.suffix.lower(),
                "content_type": content_type or "application/octet-stream",
                "size_in_bytes": stat.st_size,
                "absolute_path": str(path),
                "relative_to_article": str(path.relative_to(image_dir.parent)),
            }
        )
    return images


def iter_article_json_files(root: Path):
    for current_dir, subdirs, files in os.walk(root):
        directory = Path(current_dir)
        if "img" not in subdirs:
            continue
        for name in files:
            if name.lower().endswith(".json"):
                yield directory / name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--error-log", type=Path, default=DEFAULT_ERROR_LOG)
    parser.add_argument("--progress-every", type=int, default=10_000)
    parser.add_argument("--limit", type=int, help="Stop after this many mismatches (testing).")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Stop on the first unreadable or malformed JSON file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.error_log)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()

    with args.output.open("w", encoding="utf-8") as output:
        for json_path in iter_article_json_files(args.root):
            counts["article_json_with_img_dir"] += 1
            try:
                images = image_inventory(json_path.parent / "img")
                if not images:
                    counts["empty_img_directories"] += 1
                    continue

                with json_path.open("r", encoding="utf-8-sig") as source:
                    ninjs = json.load(source)

                # Article directories are expected to contain one ninjs object.
                # Preserve unexpected JSON types in the error report for review.
                if not isinstance(ninjs, dict):
                    raise TypeError(f"expected a JSON object, got {type(ninjs).__name__}")

                associations = ninjs.get("associations")
                if associations:
                    counts["associations_present"] += 1
                    continue

                mismatch = {
                    "source_json": str(json_path),
                    "article_directory": str(json_path.parent),
                    "article_id": json_path.stem,
                    "association_state": "missing" if "associations" not in ninjs else "empty",
                    "image_count_on_disk": len(images),
                    "image_files": images,
                    "ninjs": ninjs,
                }
                output.write(json.dumps(mismatch, ensure_ascii=False) + "\n")
                counts["missing_associations_with_images"] += 1

                if args.limit and counts["missing_associations_with_images"] >= args.limit:
                    break
            except Exception:
                counts["errors"] += 1
                logging.exception("Failed to audit article JSON: %s", json_path)
                if args.strict:
                    raise

            if (
                args.progress_every
                and counts["article_json_with_img_dir"] % args.progress_every == 0
            ):
                print(
                    f"checked={counts['article_json_with_img_dir']:,} "
                    f"mismatches={counts['missing_associations_with_images']:,} "
                    f"errors={counts['errors']:,}",
                    file=sys.stderr,
                )

    summary = {
        "root": str(args.root),
        "output": str(args.output),
        "error_log": str(args.error_log),
        **counts,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
    return 2 if counts["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
