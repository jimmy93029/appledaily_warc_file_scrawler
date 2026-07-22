"""Low-level decoding and ninjs 3.2 serialization helpers."""

from __future__ import annotations

import gzip
import io
import json
import os
import re
import zlib
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from final_cleaning_rules import (
    build_associations,
    clean_text_value,
    final_dates,
    parse_by_and_location,
)


# Keep the source date segment for diagnostics, but do not reject an article
# solely because that segment is malformed.  The canonical identifier is the
# final, exactly 26-character path component.
ARTICLE_PATH = re.compile(
    r"^/(?P<section>[^/]+)/(?P<date>[^/]+)/(?P<id>[A-Za-z0-9]{26})/*$"
)


def article_parts(url: str) -> tuple[str, str, str]:
    match = ARTICLE_PATH.fullmatch(urlsplit(url).path)
    if not match:
        raise ValueError(f"Unsupported article URL: {url}")
    return match.group("id"), match.group("date"), match.group("section")


def clean_uri(raw_uri: str) -> str:
    """Drop query parameters/fragments so the article URI can de-duplicate cleanly."""
    parsed = urlsplit(raw_uri)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def get_new_id(url: str, status: str = "text") -> str | None:
    if status == "text":
        try:
            return article_parts(url)[0]
        except ValueError:
            return None
    # Retained only for compatibility with older callers. External/S3 image
    # URLs cannot reliably reveal their parent article ID.
    parts = [part for part in urlsplit(url).path.split("/") if part]
    return parts[-3] if len(parts) >= 3 and parts[-2] == "img" else None


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


def decode_response_content(record) -> bytes:
    """Return transfer/content-decoded HTTP response bytes."""
    raw = record.reader.read()
    headers = {str(key).lower(): str(value) for key, value in record.http_headers.items()}
    if "chunked" in headers.get("transfer-encoding", "").lower():
        raw = dechunk(raw)
    content_encoding = headers.get("content-encoding", "").lower().strip()
    if content_encoding == "gzip":
        raw = gzip.decompress(raw)
    elif content_encoding == "deflate":
        try:
            raw = zlib.decompress(raw)
        except zlib.error:
            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
    return raw


def decode_html(record) -> str:
    raw = decode_response_content(record)
    content_type = record.http_headers.get("Content-Type", "")
    match = re.search(r"charset=([^;\s]+)", content_type, re.I)
    charset = match.group(1).strip("\"'") if match else (record.http_charset or "utf-8")
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def write_json(data: dict, output_dir: str | Path, file_name: str) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{file_name}.json"
    temporary = path.with_suffix(".json.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    os.replace(temporary, path)
    return path


def meta_data(
    *,
    title: str,
    content: str,
    raw_credit: str,
    warc_date: str | None,
    uri: str,
    published_candidates: list[dict],
    modified_candidates: list[dict],
    images: list[dict],
) -> dict:
    """Build the final conservative ninjs object (no genres/infoSources/creator)."""
    uri = clean_uri(uri)
    article_id, uri_date, section = article_parts(uri)
    byline = parse_by_and_location(raw_credit)
    associations = build_associations(article_id, images)
    data = {
        "uri": uri,
        "standard": {
            "name": "ninjs",
            "version": "3.2",
            "schema": "https://iptc.org/std/ninjs/ninjs-schema_3.2.json",
        },
    }
    data.update(
        final_dates(
            published_candidates,
            modified_candidates,
            warc_date,
            url_date=uri_date,
        )
    )
    data["type"] = "composite" if associations else "text"
    if associations:
        data["profile"] = "text-photo"
    data.update({
        "language": "zh-Hant-TW",
        "headlines": [{"role": "main", "value": clean_text_value(title)}],
        "subjects": [{"name": section}],
        "bodies": [
            {"role": "main", "contentType": "text/plain", "value": clean_text_value(content)}
        ],
        "associations": associations,
        "by": byline["by"],
        "located": byline["located"],
        "altIds": [{"role": "internal", "value": article_id}],
    })
    return data
