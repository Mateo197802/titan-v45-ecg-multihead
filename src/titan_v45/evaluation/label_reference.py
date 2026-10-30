"""Saved ECG-reference consistency, not longitudinal or clinical adjudication."""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping


def audit_af_reference_rows(
    rows: Iterable[Mapping[str, str]], *, reference_field: str,
) -> dict[str, object]:
    groups: dict[str, Counter[str]] = {}
    seen = set()
    for row in rows:
        identifier = row["record_id"]
        if identifier in seen:
            raise ValueError("duplicate record_id in reference table")
        seen.add(identifier)
        counts = groups.setdefault(row["source"], Counter())
        codes = {part.strip() for part in row["dx_codes"].split("|") if part.strip()}
        labels = {part.strip() for part in row[reference_field].split("|") if part.strip()}
        known = bool(codes) and all(code.isascii() and code.isdigit() for code in codes)
        af_code, af_label = "164889003" in codes, "AFIB" in labels
        counts.update({"records": 1, "af_reference_positive": int(af_label),
                       "af_code_positive": int(af_code), "unresolved_code_rows": int(not known),
                       "af_flag_mismatches": int(known and af_code != af_label),
                       "af_and_nsr_code_overlap": int(af_code and "426783006" in codes),
                       "af_and_nsr_reference_overlap": int(af_label and "NSR" in labels)})
    total = sum(groups.values(), Counter())
    return {
        "schema": "TITAN_V45_AF_REFERENCE_CONSISTENCY_V1",
        "scope": "saved_ecg_reference_flags_not_clinical_or_longitudinal_validation",
        "reference_field": reference_field, "records": total["records"],
        "af_reference_positive": total["af_reference_positive"],
        "af_code_positive": total["af_code_positive"],
        "unresolved_code_rows": total["unresolved_code_rows"],
        "af_flag_mismatches": total["af_flag_mismatches"],
        "all_af_flags_match_codes": bool(seen) and total["unresolved_code_rows"] == total["af_flag_mismatches"] == 0,
        "sources": [{"source_label": source, **dict(counts)} for source, counts in sorted(groups.items())],
        "clinical_readjudication": False, "incident_af_validated": False,
        "first_diagnosis_validated": False, "independent_validation": False,
    }
