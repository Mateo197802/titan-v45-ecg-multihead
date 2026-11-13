from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_checksum_coverage_and_ambiguous_institution_are_preserved():
    path = ROOT / "outputs/results/revision_20261029/packaged_checksum_summary.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert receipt["records"] == 2193
    assert receipt["exact_match_records"] == 2026
    assert receipt["ambiguous_source_records"] == 10
    assert receipt["unmatched_by_declared_source"] == {"codetest_zenodo_3765780": 167}
    assert sum(receipt["matched_by_declared_source"].values()) == 2026


def test_hold_and_selected_source_notice_are_both_disclosed():
    audit = json.loads((ROOT / "data/licenses/rhythm-source-attribution-v0.1.0.json").read_text())
    assert audit["distribution_status"] == "HOLD_UNRESOLVED_SOURCE_RIGHTS"
    doc = (ROOT / "docs/reviewer_closure/SOURCE_RIGHTS_DISPOSITION.md").read_text(encoding="utf-8")
    for text in ("2,026/2,193", "167", "84", "10", "already-public", "HOLD"):
        assert text in doc
