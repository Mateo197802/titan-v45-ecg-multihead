from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_publication_scope_and_missing_manuscript_are_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    evidence_notes = (ROOT / "docs" / "figure-evidence.md").read_text(encoding="utf-8")
    assert "Only the 14 PNG images referenced by the submitted manuscript are included" in readme
    assert "full manuscript, its bibliography" in evidence_notes
    assert "not included" in evidence_notes


def test_dataset_citations_and_license_boundaries_are_explicit() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    chapman = (ROOT / "data" / "licenses" / "Chapman-Shaoxing-Ningbo-CC-BY-4.0.md").read_text(
        encoding="utf-8"
    )
    ptbxl = (ROOT / "data" / "licenses" / "PTB-XL-CC-BY-4.0.md").read_text(encoding="utf-8")
    model_license = (ROOT / "MODEL_LICENSE.md").read_text(encoding="utf-8")
    chapman_card = (ROOT / "reports" / "dataset_cards" / "chapman-shaoxing-external-dev.md").read_text(
        encoding="utf-8"
    )
    ptbxl_card = (ROOT / "reports" / "dataset_cards" / "ptb-xl-external-dev.md").read_text(
        encoding="utf-8"
    )
    assert "Scientific Data* 7, article 48 (2020)" in chapman
    assert "10.1038/s41597-020-0386-x" in chapman
    assert "Scientific Data* 7, article 48 (2020" in chapman_card
    assert "Scientific Data* 9, 136 (2022)" not in chapman_card
    assert "version 1.0.3" in ptbxl
    assert "10.13026/kfzx-aw45" in ptbxl
    assert "10.13026/kfzx-aw45" in ptbxl_card
    assert "Apache-2.0" in readme
    assert "non-commercial academic and validation purposes" in model_license
    assert "paid service" in model_license


def test_rhythm_source_attribution_matches_both_published_manifests() -> None:
    attribution = json.loads(
        (ROOT / "data/licenses/rhythm-source-attribution-v0.1.0.json").read_text(encoding="utf-8")
    )
    assert attribution["distribution_status"] == "HOLD_UNRESOLVED_SOURCE_RIGHTS"
    for profile, relative in [
        ("rhythm_primary8", "data/manifests/external_dev/rhythm_primary8_records.csv"),
        (
            "rhythm_primary6_diagnostic",
            "data/manifests/external_dev/rhythm_primary6_diagnostic_records.csv",
        ),
    ]:
        with (ROOT / relative).open(encoding="utf-8", newline="") as handle:
            counts = Counter(row["source"] for row in csv.DictReader(handle))
        expected = attribution["profiles"][profile]
        assert expected["record_rows"] == sum(counts.values())
        assert expected["source_counts"] == dict(counts)
    unresolved = next(source for source in attribution["sources"] if source.get("manifest_label") == "data_test")
    assert unresolved["license"] is None
    assert "UNRESOLVED" in unresolved["mapping_status"]


def test_historical_release_manifest_is_not_presented_as_provenance_complete() -> None:
    manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "TITAN_V45_RELEASE_MANIFEST_V1"
    rhythm = next(asset for asset in manifest["assets"] if asset["category"] == "external_dev_dataset")
    assert "license" not in rhythm
    assert "source_lineage" not in rhythm
    assert "does **not** contain per-asset license or source-lineage fields" in (
        ROOT / "docs/release-process.md"
    ).read_text(encoding="utf-8")


def test_repository_contains_only_the_manuscript_figure_images() -> None:
    manifest_path = ROOT / "outputs" / "figures" / "figure_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == "TITAN_V45_MANUSCRIPT_IMAGE_MANIFEST_V1"
    expected = {
        "fig00_ecg_ai_context.png",
        "fig00b_ecg_ai_evolution_gap.png",
        "fig01_graphical_abstract.png",
        "fig02_data_processing_bias_workflow.png",
        "fig03_cascade_contract.png",
        "fig03_internal_architecture.png",
        "fig06_rhythm_confusion.png",
        "fig07_pathology_confusion.png",
        "fig08_class_metrics.png",
        "fig09_roc_curves.png",
        "fig10_precision_recall_curves.png",
        "fig11_calibration.png",
        "fig12_source_performance.png",
        "fig13_error_flows.png",
    }
    assets = manifest["assets"]
    assert {asset["file"] for asset in assets} == expected
    assert len(assets) == len(expected)
    for asset in assets:
        assert asset["source"] == f"mdpi_Articulo/figures/{asset['file']}"
        assert len(asset["sha256"]) == 64
        path = ROOT / "outputs" / "figures" / asset["file"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == asset["sha256"]

    media_suffixes = {".bmp", ".eps", ".gif", ".jpeg", ".jpg", ".pdf", ".png", ".svg", ".tif", ".tiff", ".webp"}
    actual_media = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file()
        and not {".git", ".pytest_cache", "__pycache__"}.intersection(path.parts)
        and path.suffix.lower() in media_suffixes
    }
    assert actual_media == {f"outputs/figures/{name}" for name in expected}
