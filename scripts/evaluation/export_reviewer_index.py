"""Export the provisional reviewer index without copying private correspondence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def expected_ids():
    ids = {f"R1-{number}" for number in range(1, 5)} | {"R2-general", "R2-5", "R2-6"}
    for number, suffixes in ((1, "ab"), (2, "abcdef"), (3, "abcdefgh"), (4, "abcdefghijklm")):
        ids.update(f"R2-{number}{suffix}" for suffix in suffixes)
    return ids | {f"A-{number:02d}" for number in range(1, 13)}


def parse_index(text):
    rows = []
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or cells[0] not in expected_ids():
            continue
        if cells[2] not in {"MANUSCRIPT_UPDATE_ONLY", "VERIFIED_WITH_LIMITATIONS",
                            "CLAIM_WITHDRAWAL_REQUIRED", "EXPERIMENT_COMPLETED"}:
            raise ValueError(f"unknown disposition for {cells[0]}")
        rows.append(dict(zip(("id", "concern", "disposition", "evidence_and_action"), cells, strict=True)))
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)) or set(ids) != expected_ids():
        raise ValueError("reviewer index must contain each of the 48 IDs exactly once")
    return {"schema": "TITAN_V45_REVIEWER_INDEX_POST_SPH_V1", "items": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = parse_index(args.source.read_text(encoding="utf-8"))
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
