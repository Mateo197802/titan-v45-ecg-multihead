import csv
from pathlib import Path

from titan_v45.evaluation.release_evidence import verify_release_evidence

ROOT = Path(__file__).resolve().parents[2]


def test_handoff_matches_recomputed_historical_evidence():
    document = (ROOT / "docs/reviewer_closure/HISTORICAL_EVIDENCE_HANDOFF.md").read_text(
        encoding="utf-8"
    )
    profiles = verify_release_evidence(ROOT)["profiles"]
    p6 = profiles["rhythm_primary6_diagnostic"]
    p8 = profiles["rhythm_primary8"]
    p4 = profiles["pathology_primary4"]
    assert f"{p6['records']:,} selected ECG records" in document
    assert f"{p6['correct']:,} top-1 correct" in document
    assert f"accuracy {p6['accuracy']:.2%}" in document
    assert f"macro-F1 {p6['macro_f1']:.2%}" in document
    assert f"{p8['records']:,} selected ECG records" in document
    assert f"accuracy {p8['accepted_accuracy']:.2%}" in document
    assert f"macro-F1 {p8['macro_f1']:.2%}" in document
    assert f"{p4['panel_rows']} binary panel observations" in document
    assert f"accuracy {p4['mean_accuracy']:.2%}" in document
    assert f"macro-F1 {p4['macro_f1']:.2%}" in document
    with (ROOT / "data/manifests/external_dev/pathology_primary4_panels.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        records = {row["record_id"] for row in csv.DictReader(handle)}
    assert f"{len(records)} unique record keys" in document
