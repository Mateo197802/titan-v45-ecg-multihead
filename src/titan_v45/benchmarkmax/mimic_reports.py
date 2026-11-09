"""Deterministic PAC phrase classification for MIMIC machine-report lines.

This utility does not establish clinical labels. It refuses mappings until a
corresponding author records approval of the phrase dictionary.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

ReportClass = Literal[
    "explicit_positive",
    "explicit_negative",
    "uncertain_or_qualified",
    "not_mentioned_or_report_missing",
]

REPORT_COLUMNS = tuple(f"report_{index}" for index in range(18))
MAPPING_SCHEMA = "TITAN_V46_MIMIC_PAC_REPORT_MAPPING_V1"
_TOKEN_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass(frozen=True, init=False)
class ApprovedPACPhraseMapping:
    mapping_id: str
    explicit_positive: tuple[tuple[str, ...], ...]
    explicit_negative: tuple[tuple[str, ...], ...]
    uncertain_or_qualified: tuple[tuple[str, ...], ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ValueError("ApprovedPACPhraseMapping must come from load_approved_pac_mapping")

    @classmethod
    def _from_validated_mapping(
        cls,
        mapping_id: str,
        explicit_positive: tuple[tuple[str, ...], ...],
        explicit_negative: tuple[tuple[str, ...], ...],
        uncertain_or_qualified: tuple[tuple[str, ...], ...],
    ) -> ApprovedPACPhraseMapping:
        instance = object.__new__(cls)
        object.__setattr__(instance, "mapping_id", mapping_id)
        object.__setattr__(instance, "explicit_positive", explicit_positive)
        object.__setattr__(instance, "explicit_negative", explicit_negative)
        object.__setattr__(instance, "uncertain_or_qualified", uncertain_or_qualified)
        return instance


@dataclass(frozen=True)
class _Hit:
    start: int
    end: int
    category: ReportClass


def _tokens(text: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return tuple(_TOKEN_PATTERN.findall(normalized))


def _parse_mapping(raw: object) -> ApprovedPACPhraseMapping:
    if not isinstance(raw, Mapping):
        raise ValueError("mapping document must be a JSON object")
    if raw.get("schema") != MAPPING_SCHEMA:
        raise ValueError("unsupported PAC phrase mapping schema")
    if raw.get("status") != "approved_by_corresponding_author":
        raise ValueError("PAC phrase mapping requires author approval")
    mapping_id = raw.get("mapping_id")
    if not isinstance(mapping_id, str) or not mapping_id.strip():
        raise ValueError("mapping_id must be a non-empty string")

    approval = raw.get("approval")
    if not isinstance(approval, Mapping):
        raise ValueError("author approval metadata is required")
    approved_by = approval.get("approved_by")
    approved_on = approval.get("approved_on")
    if not isinstance(approved_by, str) or not approved_by.strip():
        raise ValueError("author approval must identify the approving author")
    if not isinstance(approved_on, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", approved_on):
        raise ValueError("author approval date must use YYYY-MM-DD")
    try:
        date.fromisoformat(approved_on)
    except ValueError as exc:
        raise ValueError("author approval date must use YYYY-MM-DD") from exc

    phrases = raw.get("phrases")
    if not isinstance(phrases, Mapping):
        raise ValueError("phrases must contain the three report-state lists")

    parsed: dict[str, tuple[tuple[str, ...], ...]] = {}
    owner_by_phrase: dict[tuple[str, ...], str] = {}
    for category in (
        "explicit_positive",
        "explicit_negative",
        "uncertain_or_qualified",
    ):
        values = phrases.get(category)
        if not isinstance(values, list):
            raise ValueError(f"phrases.{category} must be a list")
        if category != "explicit_negative" and not values:
            raise ValueError(f"phrases.{category} must not be empty")
        category_phrases: list[tuple[str, ...]] = []
        for phrase in values:
            if not isinstance(phrase, str) or not phrase.strip():
                raise ValueError(f"phrases.{category} entries must be non-empty strings")
            normalized = _tokens(phrase)
            if not normalized:
                raise ValueError(f"phrases.{category} contains a phrase with no word tokens")
            owner = owner_by_phrase.get(normalized)
            if owner is not None and owner != category:
                raise ValueError("the same normalized phrase cannot belong to multiple classes")
            if owner == category:
                raise ValueError(f"phrases.{category} contains a duplicate normalized phrase")
            owner_by_phrase[normalized] = category
            category_phrases.append(normalized)
        parsed[category] = tuple(category_phrases)

    return ApprovedPACPhraseMapping._from_validated_mapping(
        mapping_id.strip(),
        parsed["explicit_positive"],
        parsed["explicit_negative"],
        parsed["uncertain_or_qualified"],
    )


def load_approved_pac_mapping(path: Path) -> ApprovedPACPhraseMapping:
    """Load and validate a versioned mapping with explicit author sign-off."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _parse_mapping(raw)


def report_lines_from_row(row: Mapping[str, object]) -> tuple[str, ...]:
    """Read report_0..report_17 without collapsing blank slots or their order."""
    missing = [column for column in REPORT_COLUMNS if column not in row]
    if missing:
        raise ValueError("machine measurements must include report_0..report_17")
    lines: list[str] = []
    for column in REPORT_COLUMNS:
        value = row[column]
        if value is None:
            lines.append("")
        elif isinstance(value, str):
            lines.append(value)
        else:
            raise ValueError(f"{column} must be text or null")
    return tuple(lines)


def _phrase_hits(
    tokens: tuple[str, ...],
    phrases: tuple[tuple[str, ...], ...],
    category: ReportClass,
) -> list[_Hit]:
    hits: list[_Hit] = []
    for phrase in phrases:
        width = len(phrase)
        for start in range(len(tokens) - width + 1):
            if tokens[start : start + width] == phrase:
                hits.append(_Hit(start, start + width, category))
    return hits


def _classify_line(line: str, mapping: ApprovedPACPhraseMapping) -> ReportClass | None:
    tokens = _tokens(line)
    hits = (
        _phrase_hits(tokens, mapping.explicit_positive, "explicit_positive")
        + _phrase_hits(tokens, mapping.explicit_negative, "explicit_negative")
        + _phrase_hits(tokens, mapping.uncertain_or_qualified, "uncertain_or_qualified")
    )
    if not hits:
        return None

    active = [
        hit
        for hit in hits
        if not any(
            other.category != hit.category
            and other.start <= hit.start
            and other.end >= hit.end
            and (other.start, other.end) != (hit.start, hit.end)
            for other in hits
        )
    ]
    categories = {hit.category for hit in active}
    if len(categories) != 1:
        return "uncertain_or_qualified"
    return next(iter(categories))


def classify_report_lines(
    lines: Sequence[str | None],
    mapping: ApprovedPACPhraseMapping | Mapping[str, object],
) -> ReportClass:
    """Classify report lines; missing text is never converted to explicit negative."""
    approved = mapping if isinstance(mapping, ApprovedPACPhraseMapping) else _parse_mapping(mapping)
    line_states: set[ReportClass] = set()
    for line in lines:
        if line is None:
            continue
        if not isinstance(line, str):
            raise ValueError("machine report lines must be text or null")
        state = _classify_line(line, approved)
        if state is not None:
            line_states.add(state)
    if not line_states:
        return "not_mentioned_or_report_missing"
    if "uncertain_or_qualified" in line_states:
        return "uncertain_or_qualified"
    if {"explicit_positive", "explicit_negative"}.issubset(line_states):
        return "uncertain_or_qualified"
    return next(iter(line_states))


def classify_measurement_row(
    row: Mapping[str, object],
    mapping: ApprovedPACPhraseMapping | Mapping[str, object],
) -> ReportClass:
    """Classify one machine-measurement CSV row without returning its text or IDs."""
    return classify_report_lines(report_lines_from_row(row), mapping)
