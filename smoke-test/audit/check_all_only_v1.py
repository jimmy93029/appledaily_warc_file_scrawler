#!/usr/bin/env python3
"""Stream all saved only-V1 WARC responses through the refined rules.

The input body is never retained after a record is checked. A compact JSON
summary and a JSONL file containing rejected-record diagnostics are produced.
No files in downloads_new are imported or modified.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import trafilatura
from bs4 import BeautifulSoup


DEFAULT_INPUT = Path("/home/jimmywu/sinica/venv/codes/compare/only_v1_warc_records.jsonl")
DEFAULT_REPORT = Path("/home/jimmywu/sinica/venv/codes/fix_temp/only_v1_check_report.json")
DEFAULT_REJECTED = Path("/home/jimmywu/sinica/venv/codes/fix_temp/only_v1_rejected.jsonl")

ALLOWED_HOSTS = {"appledaily.com.tw", "www.appledaily.com.tw", "tw.appledaily.com.tw"}
ARTICLE_PATH = re.compile(r"^/[^/]+/(?P<date>\d{8})/(?P<id>[A-Za-z0-9]+)/*$")
CHINESE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
NOT_FOUND = ("抱歉，要找的頁面不存在", "Sorry, page not found")


@dataclass
class Decision:
    accepted: bool
    article_key: str
    article_id: str | None
    target_uri: str
    title: str
    content_length: int
    extraction_method: str | None
    reasons: list[str]


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
            raise ValueError(f"invalid chunk size {size_line[:40]!r}") from exc
        if size == 0:
            return output.getvalue()
        chunk = source.read(size)
        if len(chunk) != size:
            raise ValueError(f"short chunk: expected {size}, got {len(chunk)}")
        output.write(chunk)
        if source.read(2) != b"\r\n":
            raise ValueError("chunk is missing its CRLF terminator")


def decode_html(item: dict, reasons: list[str]) -> str:
    body = item.get("body", "")
    is_base64 = item.get("body_encoding") == "base64"
    if is_base64:
        import base64

        try:
            raw = base64.b64decode(body, validate=True)
        except Exception as exc:
            reasons.append(f"invalid base64 body: {exc}")
            return ""
    else:
        raw = str(body).encode("utf-8")

    headers = {str(k).lower(): str(v) for k, v in item.get("http_headers", {}).items()}
    if "chunked" in headers.get("transfer-encoding", "").lower():
        if is_base64:
            # Base64 preserves the original bytes, so strict size-based decoding
            # is both possible and desirable.
            try:
                raw = dechunk(raw)
            except ValueError as exc:
                reasons.append(f"chunk decoding failed: {exc}")
                return ""
        else:
            # Text-mode JSONL is already decoded. A chunk boundary can split a
            # multibyte UTF-8 character, making the original byte counts
            # unrecoverable. Remove only complete chunk-size lines instead.
            text_body = str(body)
            text_body = re.sub(
                r"(?m)^[0-9A-Fa-f]{1,16}(?:;[^\r\n]*)?\r?\n",
                "",
                text_body,
            )
            raw = text_body.encode("utf-8")

    content_encoding = headers.get("content-encoding", "").lower()
    if content_encoding == "gzip":
        import gzip

        try:
            raw = gzip.decompress(raw)
        except (OSError, EOFError) as exc:
            reasons.append(f"gzip decoding failed: {exc}")
            return ""

    content_type = headers.get("content-type", "")
    match = re.search(r"charset=([^;\s]+)", content_type, re.I)
    charset = match.group(1).strip("\"'") if match else "utf-8"
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        reasons.append(f"unknown charset {charset!r}; decoded as UTF-8")
        return raw.decode("utf-8", errors="replace")


def extract(html: str, reasons: list[str]) -> tuple[str, str, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    content = ""
    method = None

    try:
        raw_result = trafilatura.extract(
            html,
            output_format="json",
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )
        if raw_result:
            result = json.loads(raw_result)
            content = (result.get("text") or "").strip()
            title = title or (result.get("title") or "").strip()
            if content:
                method = "trafilatura"
    except Exception as exc:
        reasons.append(f"Trafilatura error: {type(exc).__name__}: {exc}")

    if not content:
        article = soup.find("article") or soup.find(id="articleBody")
        if article:
            content = "\n".join(
                tag.get_text(" ", strip=True)
                for tag in article.find_all(["p", "h2", "h3", "h4", "h5", "h6"])
                if tag.get_text(strip=True)
            ).strip()
            if content:
                method = "article-elements"

    if not content:
        meta = soup.find("meta", property="og:description") or soup.find(
            "meta", attrs={"name": "description"}
        )
        if meta and meta.get("content"):
            content = meta["content"].strip()
            method = "meta-description"

    return title, content, method


def check(item: dict) -> Decision:
    reasons: list[str] = []
    uri = str(item.get("target_uri", "")).strip()
    parts = urlsplit(uri)
    host = (parts.hostname or "").lower()
    path_match = ARTICLE_PATH.fullmatch(parts.path)
    article_id = path_match.group("id") if path_match else None

    if parts.scheme not in {"http", "https"}:
        reasons.append("invalid URL scheme")
    if host not in ALLOWED_HOSTS:
        reasons.append(f"disallowed hostname: {host or '(empty)'}")
    if not path_match:
        reasons.append("path is not /section/YYYYMMDD/article-id")

    headers = {str(k).lower(): str(v) for k, v in item.get("http_headers", {}).items()}
    content_type = headers.get("content-type", "").lower()
    if not content_type.startswith("text/html"):
        reasons.append(f"not HTML: {content_type or '(missing Content-Type)'}")

    html = decode_html(item, reasons)
    title, content, method = extract(html, reasons) if html else ("", "", None)
    if not title:
        reasons.append("empty title")
    if not content:
        reasons.append("empty article content")
    elif not CHINESE.search(content):
        reasons.append("content has no Chinese characters")
    if any(marker in content for marker in NOT_FOUND):
        reasons.append("page-not-found content")

    csv_rows = item.get("matched_csv_rows") or []
    csv_id = str(csv_rows[0].get("altids value", "")).split("?", 1)[0] if csv_rows else ""
    article_key = csv_id or article_id or uri
    return Decision(
        accepted=not reasons,
        article_key=article_key,
        article_id=article_id,
        target_uri=uri,
        title=title,
        content_length=len(content),
        extraction_method=method,
        reasons=reasons,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--rejected", type=Path, default=DEFAULT_REJECTED)
    parser.add_argument("--progress-every", type=int, default=100)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    method_counts: Counter[str] = Counter()
    all_articles: set[str] = set()
    accepted_articles: set[str] = set()
    rejected_articles: set[str] = set()

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.rejected.parent.mkdir(parents=True, exist_ok=True)

    with args.input.open("r", encoding="utf-8-sig") as source, args.rejected.open(
        "w", encoding="utf-8"
    ) as rejected_output:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            counts["responses"] += 1
            try:
                item = json.loads(line)
                decision = check(item)
            except Exception as exc:
                counts["malformed_or_crashed"] += 1
                reason = f"checker exception: {type(exc).__name__}: {exc}"
                reason_counts[reason] += 1
                rejected_output.write(
                    json.dumps({"line_number": line_number, "reasons": [reason]}) + "\n"
                )
                continue

            all_articles.add(decision.article_key)
            if decision.extraction_method:
                method_counts[decision.extraction_method] += 1
            if decision.accepted:
                counts["accepted_responses"] += 1
                accepted_articles.add(decision.article_key)
            else:
                counts["rejected_responses"] += 1
                rejected_articles.add(decision.article_key)
                reason_counts.update(decision.reasons)
                rejected_output.write(
                    json.dumps(
                        {
                            "line_number": line_number,
                            "article_key": decision.article_key,
                            "article_id": decision.article_id,
                            "target_uri": decision.target_uri,
                            "title": decision.title,
                            "content_length": decision.content_length,
                            "extraction_method": decision.extraction_method,
                            "reasons": decision.reasons,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

            if args.progress_every and counts["responses"] % args.progress_every == 0:
                print(
                    f"checked={counts['responses']:,} accepted={counts['accepted_responses']:,} "
                    f"rejected={counts['rejected_responses']:,}",
                    file=sys.stderr,
                )

    # An article is resolved if at least one of its archived responses succeeds.
    unresolved_articles = rejected_articles - accepted_articles
    report = {
        "input": str(args.input),
        "input_size_bytes": args.input.stat().st_size,
        "response_counts": dict(counts),
        "unique_articles_seen": len(all_articles),
        "unique_articles_resolved": len(accepted_articles),
        "unique_articles_unresolved": len(unresolved_articles),
        "extraction_methods": dict(method_counts.most_common()),
        "rejection_reasons": dict(reason_counts.most_common()),
        "rejected_details": str(args.rejected),
        "interpretation": (
            "The refined rules solve every represented article"
            if not unresolved_articles and not counts["malformed_or_crashed"]
            else "Some represented articles remain unresolved; inspect rejected_details"
        ),
        "coverage_note": (
            "This checks only WARC responses present in the input JSONL, not CSV URLs "
            "that were never found or never written to it."
        ),
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not unresolved_articles and not counts["malformed_or_crashed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
