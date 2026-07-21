"""Article text, credit and date extraction for the revised pipeline."""

from __future__ import annotations

import html as html_lib
import json
import re
from typing import Any, Iterable
from urllib.parse import urlsplit

import trafilatura
from bs4 import BeautifulSoup


APPLEDAILY_DOMAIN_ROOTS = ("appledaily.com", "appledaily.com.tw")
# Article URLs normally look like /SECTION/YYYYMMDD/ARTICLE_ID, but a small
# number of archived URLs contain a malformed date segment.  The stable key is
# the final 26-character ID, so date validation must not decide whether an
# otherwise valid Apple Daily article is admitted.
ARTICLE_PATH = re.compile(r"^/[^/]+/[^/]+/[A-Za-z0-9]{26}/*$")
CHINESE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
NOT_FOUND = ("抱歉，要找的頁面不存在", "Sorry, page not found")

PUBLISHED_META_KEYS = (
    ("property", "article:published_time"),
    ("name", "published_time"),
    ("property", "og:article:published_time"),
)
MODIFIED_META_KEYS = (
    ("property", "article:modified_time"),
    ("name", "modified_time"),
    ("property", "og:article:modified_time"),
)

BRACKETED_REPORT = re.compile(
    r"[（(【［\[]\s*(?P<credit>[^）)】］\]\r\n]{1,120}?)"
    r"\s*報導\s*[）)】］\]]"
)
BARE_REPORT = re.compile(
    r"(?m)^[ \t]*(?P<credit>[^\r\n。！？；：]{1,120}?[／/╱∕⁄]"
    r"[^\r\n。！？；：]{1,80}?)\s*報導(?=$|[ \t]*[，。！？])"
)
CREATOR_CREDIT = re.compile(
    r"(?m)(?P<full>(?:圖\s*[•．・]?\s*文|文\s*[•．・]?\s*圖|攝影|圖|文)"
    r"\s*[／/╱∕⁄]\s*[^\r\n，。；]{2,80})"
)
GENERIC_CREDIT_LINE = re.compile(
    r"(?m)^[ \t]*(?P<credit>[^\r\n。！？；：]{1,100}?[／/╱∕⁄]"
    r"[^\r\n。！？；：]{1,80})[ \t]*$"
)


def is_appledaily_host(hostname: str | None) -> bool:
    """Accept Apple Daily apex domains and real subdomains, never substrings."""
    hostname = (hostname or "").lower().rstrip(".")
    return any(
        hostname == root or hostname.endswith(f".{root}")
        for root in APPLEDAILY_DOMAIN_ROOTS
    )


def valid_url(content_type: str | None, target_url: str) -> bool:
    if not content_type or not content_type.lower().startswith("text/html"):
        return False
    parts = urlsplit(target_url)
    return (
        parts.scheme in {"http", "https"}
        and is_appledaily_host(parts.hostname)
        and ARTICLE_PATH.fullmatch(parts.path) is not None
    )


def valid_content(content: str) -> bool:
    return bool(content and CHINESE.search(content)) and not any(
        marker in content for marker in NOT_FOUND
    )


def iter_json_objects(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_json_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_json_objects(child)


def json_ld_objects(soup: BeautifulSoup) -> list[dict[str, Any]]:
    objects = []
    for script in soup.find_all("script", type=re.compile(r"ld\+json", re.I)):
        raw = script.string or script.get_text()
        if not raw.strip():
            continue
        try:
            objects.extend(iter_json_objects(json.loads(raw)))
        except (json.JSONDecodeError, TypeError):
            continue
    return objects


def date_candidates(soup: BeautifulSoup, meta_keys, ld_key: str) -> list[dict]:
    candidates = []
    for attribute, value in meta_keys:
        tag = soup.find("meta", attrs={attribute: re.compile(f"^{re.escape(value)}$", re.I)})
        if tag and tag.get("content"):
            candidates.append(
                {"value": tag["content"].strip(), "source": f"meta[{attribute}={value}]"}
            )
    for index, obj in enumerate(json_ld_objects(soup)):
        value = obj.get(ld_key)
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, str) and item.strip():
                candidates.append({"value": item.strip(), "source": f"json-ld[{index}].{ld_key}"})
    return candidates


def strip_promotional_tail(text: str) -> str:
    markers = ("《蘋果新聞網》", "「升級壹會員」", "《升級壹會員》", "一指在APP內訂閱")
    positions = [text.find(marker) for marker in markers if text.find(marker) >= 0]
    if not positions:
        return text.strip()
    position = min(positions)
    line_start = text.rfind("\n", 0, position)
    return text[: line_start if line_start >= 0 else position].strip()


def extract_credit(content: str) -> tuple[str, str]:
    """Return unchanged content plus one extracted production credit.

    The canonical record keeps the source credit line in ``bodies`` while also
    exposing its parsed author and location as top-level ninjs properties.
    """
    searches = (
        BRACKETED_REPORT.search(content),
        BARE_REPORT.search(content),
        CREATOR_CREDIT.search(content),
    )
    match = next((item for item in searches if item), None)
    if not match:
        # Bare author/role lines are accepted only near the beginning or end.
        lines = content.splitlines()
        edge_text = "\n".join(lines[:3] + lines[-5:])
        generic = GENERIC_CREDIT_LINE.search(edge_text)
        return (content, generic.group("credit").strip()) if generic else (content, "")

    raw_credit = match.group(0).strip()
    return content, raw_credit


def extract_text(raw_html: str) -> dict:
    """Extract the first *valid* body, falling through all available sources."""
    soup = BeautifulSoup(raw_html, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    content_candidates: list[tuple[str, str]] = []
    method = "none"

    extraction_warnings = []
    try:
        extracted = trafilatura.extract(
            raw_html,
            output_format="json",
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )
    except Exception as exc:  # A failed primary engine must not block fallbacks.
        extracted = None
        extraction_warnings.append(f"trafilatura: {type(exc).__name__}: {exc}")
    if extracted:
        try:
            result = json.loads(extracted)
        except (json.JSONDecodeError, TypeError):
            result = {}
        trafilatura_content = str(result.get("text") or "").strip()
        title = title or str(result.get("title") or "").strip()
        if trafilatura_content:
            content_candidates.append(("trafilatura", trafilatura_content))

    # Do not gate fallbacks on mere non-emptiness.  A non-empty Trafilatura
    # result can still be navigation, an error page, or text with no Chinese.
    article = soup.find("article") or soup.find(id="articleBody")
    if article:
        article_content = "\n".join(
            node.get_text(" ", strip=True)
            for node in article.find_all(["p", "h2", "h3", "h4", "h5", "h6"])
            if node.get_text(strip=True)
        ).strip()
        if article_content:
            content_candidates.append(("article-elements", article_content))

    meta = soup.find("meta", property="og:description") or soup.find(
        "meta", attrs={"name": "description"}
    )
    if meta and meta.get("content"):
        content_candidates.append(("meta-description", str(meta["content"]).strip()))

    content = ""
    first_nonempty = ("none", "")
    for candidate_method, candidate in content_candidates:
        candidate = strip_promotional_tail(html_lib.unescape(candidate))
        if candidate and not first_nonempty[1]:
            first_nonempty = (candidate_method, candidate)
        if valid_content(candidate):
            method, content = candidate_method, candidate
            break
    if not content:
        method, content = first_nonempty

    title = html_lib.unescape(title)
    content, raw_credit = extract_credit(content)
    return {
        "title": title,
        "content": content,
        "raw_credit": raw_credit,
        "published_candidates": date_candidates(soup, PUBLISHED_META_KEYS, "datePublished"),
        "modified_candidates": date_candidates(soup, MODIFIED_META_KEYS, "dateModified"),
        "method": method,
        "extraction_warnings": extraction_warnings,
    }
