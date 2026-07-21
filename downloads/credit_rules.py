#!/usr/bin/env python3
"""Deterministic Apple Daily credit parsing rules for later ninjs cleanup.

Unknown right-hand values are retained as locations. Only explicit non-location
terms are excluded, allowing domestic, foreign, and previously unseen places.
The original credit is always returned for an external audit trail.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass


NON_LOCATION_EXACT = {
    "連線",
    "綜合",
    "綜合報導",
    "外電",
    "編譯",
    "整理",
}

NON_LOCATION_CONTAINS = {
    "顧問",
}

# These are production/styling roles, not article authors. If a generic credit
# line starts with one of them, reject the entire line instead of guessing.
NON_BY_PREFIXES = {
    "髮",
    "髮型",
    "妝",
    "妝髮",
    "化妝",
    "梳化",
    "造型",
    "服裝",
    "模特兒",
    "模特",
    "協力",
    "場地",
    "道具",
}

SEPARATOR_TRANSLATION = str.maketrans(
    {"/": "／", "╱": "／", "∕": "／", "⁄": "／"}
)
OUTER_BRACKETS = str.maketrans("（(【［[）)】］]", "          ")
CREDIT_PREFIX = re.compile(
    r"^(?P<prefix>圖\s*[•．・]?\s*文|文\s*[•．・]?\s*圖|攝影|圖|文)\s*／\s*(?P<name>.+)$"
)


@dataclass(frozen=True)
class CreditResult:
    matched: bool
    by: str
    located: str
    raw_credit: str
    credit_type: str
    right_side: str
    confidence: str


def normalize_credit(value: str) -> str:
    value = value.strip().translate(SEPARATOR_TRANSLATION)
    value = value.translate(OUTER_BRACKETS).strip()
    return re.sub(r"\s+", " ", value)


def is_non_location(value: str) -> bool:
    value = value.strip()
    if value in NON_LOCATION_EXACT:
        return True
    return any(word in value for word in NON_LOCATION_CONTAINS)


def classify_right_side(value: str) -> str:
    value = value.removesuffix("報導").strip()
    if is_non_location(value):
        return ""
    return value


def parse_credit(raw_credit: str) -> CreditResult:
    """Parse one already-isolated credit/byline string without using NLP."""
    normalized = normalize_credit(raw_credit)
    if not normalized:
        return CreditResult(False, "", "", raw_credit, "empty", "", "none")

    prefix_match = CREDIT_PREFIX.fullmatch(normalized)
    if prefix_match:
        return CreditResult(
            True,
            prefix_match.group("name").strip(),
            "",
            raw_credit,
            "explicit_creator_credit",
            "",
            "high",
        )

    if "／" not in normalized:
        return CreditResult(False, "", "", raw_credit, "unrecognized", "", "none")

    # Without the explicit 報導 anchor, accept only one simple separator. This
    # rejects compound styling credits such as:
    has_report_anchor = normalized.endswith("報導")
    if not has_report_anchor and normalized.count("／") != 1:
        return CreditResult(False, "", "", raw_credit, "ambiguous_multi_credit", "", "none")

    by, right = (part.strip() for part in normalized.split("／", 1))
    compact_by = re.sub(r"\s+", "", by)
    if any(compact_by == role or compact_by.startswith(role) for role in NON_BY_PREFIXES):
        return CreditResult(False, "", "", raw_credit, "non_author_role", right, "high")
    if not by or len(by) > 60:
        return CreditResult(False, "", "", raw_credit, "invalid_by_candidate", right, "none")
    right_without_suffix = right.removesuffix("報導").strip()
    located = classify_right_side(right)
    if located:
        credit_type = "by_and_location"
        confidence = "medium"  # Inferred by exclusion, not a location whitelist.
    else:
        credit_type = "by_and_non_location_role"
        confidence = "high" if is_non_location(right_without_suffix) else "medium"

    return CreditResult(
        bool(by),
        by,
        located,
        raw_credit,
        credit_type,
        right_without_suffix,
        confidence,
    )
