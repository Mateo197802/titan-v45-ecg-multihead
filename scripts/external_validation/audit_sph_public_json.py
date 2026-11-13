"""Check public SPH aggregate JSON for selected individual identifier patterns.

This bounded guard does not certify general de-identification or scan media.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FORBIDDEN_KEYS = {"record_id", "patient_id", "ecg_id", "subject_id", "study_id"}
SPH_RECORD_ID = re.compile(r"(?<![A-Za-z0-9])A[0-9]{5}(?![A-Za-z0-9])")


def inspect_value(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise ValueError("individual identifier field found")
            if SPH_RECORD_ID.search(key):
                raise ValueError("individual SPH record pattern found in field name")
            inspect_value(child)
    elif isinstance(value, list):
        for child in value:
            inspect_value(child)
    elif isinstance(value, str) and SPH_RECORD_ID.search(value):
        raise ValueError("individual SPH record pattern found in string")


def audit_directory(directory):
    files = sorted(Path(directory).glob("*.json"))
    if not files:
        raise ValueError("no SPH JSON files to inspect")
    for path in files:
        try:
            inspect_value(json.loads(path.read_text(encoding="utf-8")))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"public SPH JSON audit failed: {path.name}") from exc
    return {"json_files_checked": len(files), "individual_identifiers_detected": 0,
            "scope": "top-level JSON files; specified identifier fields and A-plus-five-digit pattern only"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit_directory(args.directory), sort_keys=True))


if __name__ == "__main__":
    main()
