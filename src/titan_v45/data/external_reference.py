"""Conservative machine-statement parser; unknown is not a binary negative."""
from __future__ import annotations

import re

REPORT_COLUMNS = tuple(f"report_{i}" for i in range(18))
STATEMENTS = {
    "AFIB": ("atrial fibrillation",),
    "SB": ("sinus bradycardia",),
    "STACH": ("sinus tachycardia",),
    "NSR": ("normal sinus rhythm",),
    "RBBB": ("right bundle branch block", "complete right bundle branch block"),
    "PAC": ("premature atrial complex", "premature atrial complexes",
            "premature atrial contraction", "premature atrial contractions"),
    "1AVB": ("first degree av block", "1st degree av block", "first degree atrioventricular block"),
    "PVC": ("premature ventricular complex", "premature ventricular complexes",
            "premature ventricular contraction", "premature ventricular contractions"),
    "ASMI": ("anteroseptal myocardial infarction", "anteroseptal infarct"),
    "LVH": ("left ventricular hypertrophy",),
    "IMI": ("inferior myocardial infarction", "inferior infarct"),
}
# ISC_ is not inferred from broad ST/T or nonspecific ischemia statements.
UNCERTAIN = re.compile(r"\b(?:possible|possibly|probable|cannot rule out|may represent|suggests?|suspect(?:ed)?|consider)\b")
HISTORICAL = re.compile(r"\b(?:prior|previous(?:ly)?|history of|old|age undetermined|no longer|resolved)\b")
NEGATIONS = ("no evidence of ", "negative for ", "no ")


def _normalized(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", text.lower()).split())


def classify_report(row) -> dict[str, str]:
    lines = [_normalized(row[key] or "") for key in REPORT_COLUMNS]
    result = {}
    for endpoint, phrases in STATEMENTS.items():
        evidence = set()
        for line in lines:
            if not any(re.search(rf"\b{re.escape(phrase)}\b", line) for phrase in phrases):
                continue
            if HISTORICAL.search(line):
                evidence.add("historical")
            elif UNCERTAIN.search(line):
                evidence.add("uncertain")
            elif line in phrases:
                evidence.add("positive")
            elif any(line == prefix + phrase for prefix in NEGATIONS for phrase in phrases):
                evidence.add("explicit_negative")
            else:
                evidence.add("ambiguous")
        result[endpoint] = next(iter(evidence)) if len(evidence) == 1 else (
            "conflict" if evidence else "unmentioned"
        )
    return {**result, "ISC_": "unmapped"}
