from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "outputs" / "results"


def _read_json(relative: str) -> dict[str, object]:
    return json.loads((RESULTS / relative).read_text(encoding="utf-8"))


def test_canonical_profile_evidence_preserves_status_and_metrics() -> None:
    payload = _read_json("primary/canonical_profiles.json")
    profiles = {item["profile"]: item for item in payload["profiles"]}
    assert profiles["rhythm_primary8"]["status"] == "NO_PASA"
    assert profiles["rhythm_primary8"]["accuracy"] == 0.9060647514819882
    assert profiles["rhythm_primary6_diagnostic"]["macro_f1"] == 0.8009383239876123
    assert profiles["pathology_primary4"]["status"] == "ACEPTADO_POR_DECISION_DEL_PROYECTO"
    assert profiles["pathology_primary4"]["accuracy"] == 0.8022904853689048
    assert all(item["top_k"] == 1 for item in payload["profiles"])
    assert all(item["hidden_abstention"] is False for item in payload["profiles"])


def test_primary8_confusion_matrix_uses_canonical_class_order() -> None:
    path = RESULTS / "external_dev" / "rhythm_primary8_confusion_matrix.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    classes = ["AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC"]
    assert rows[0] == ["true/pred", *classes]
    assert [row[0] for row in rows[1:]] == classes
    assert len(rows) == 9 and all(len(row) == 9 for row in rows)


def test_primary4_binary_confusions_match_promoted_report() -> None:
    path = RESULTS / "external_dev" / "pathology_primary4_confusion_matrices.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["class"] for row in rows] == ["ASMI", "LVH", "IMI", "ISC_"]
    assert [int(row["tp"]) for row in rows] == [106, 70, 84, 103]
    assert [int(row["fn"]) for row in rows] == [41, 42, 19, 16]


def test_release_manifest_preserves_expected_asset_set_and_size_limit() -> None:
    payload = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
    expected = [
        "backbone-v3f-original.pt",
        "specialists-v3p-e008-primary6-diagnostic.pt",
        "specialists-v3q-primary8-best-candidate.pt",
        "backbone-v3ag-pathology.pt",
        "specialists-v3ag-primary4-calibrated.pt",
        "external-dev-rhythm-chapman-shaoxing.tar.zst",
        "external-dev-pathology-ptbxl-fold10.tar.zst",
    ]
    assets = payload["assets"]
    assert [asset["name"] for asset in assets] == expected
    assert all(asset["bytes"] < 2 * 1024**3 for asset in assets)
    assert "release-manifest.json" in (ROOT / "SHA256SUMS").read_text(encoding="utf-8")
