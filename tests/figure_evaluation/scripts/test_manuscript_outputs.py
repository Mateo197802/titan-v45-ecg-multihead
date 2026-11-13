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
    assert "The 14 current manuscript figure PNGs are included." in readme
    assert "The manuscript source and compiled PDF are outside this repository." in readme
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


def test_repository_contains_only_manifested_manuscript_and_sph_images() -> None:
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
    sph_dir = ROOT / "outputs" / "figures" / "external_sph"
    sph = json.loads((sph_dir / "figure_manifest.json").read_text(encoding="utf-8"))
    assert sph["schema"] == "TITAN_V45_SPH_AGGREGATE_FIGURE_MANIFEST_V1"
    sph_files = {f"sph_{stem}.{ext}" for stem in ("profile_coverage", "endpoint_metrics", "duplicate_sensitivity")
                 for ext in ("png", "pdf")}
    assert set(sph["assets"]) == sph_files
    for name, digest in sph["assets"].items():
        assert hashlib.sha256((sph_dir / name).read_bytes()).hexdigest() == digest
    assert hashlib.sha256((ROOT / sph["source_aggregate"]).read_bytes()).hexdigest() == sph["source_aggregate_sha256"]
    assert hashlib.sha256((ROOT / sph["renderer"]).read_bytes()).hexdigest() == sph["renderer_sha256"]
    assert hashlib.sha256((ROOT / "scripts/external_validation/plot_sph_aggregate.py").read_bytes()).hexdigest() == sph["base_renderer_sha256"]

    pac_dir = ROOT / "outputs" / "figures" / "external_sph_pac"
    pac = json.loads((pac_dir / "pac_probe_figure_manifest.json").read_text(encoding="utf-8"))
    assert pac["schema"] == "TITAN_V45_SPH_PAC_FIGURE_MANIFEST_V1"
    pac_files = {"sph_pac_probe_exploratory.png", "sph_pac_probe_exploratory.pdf"}
    assert set(pac["figures"]) == pac_files
    for name, asset in pac["figures"].items():
        path = pac_dir / name
        assert asset["bytes"] == path.stat().st_size > 0
        assert hashlib.sha256(path.read_bytes()).hexdigest() == asset["sha256"]

    experimental_dir = ROOT / "outputs/figures/benchmarkmax"
    experimental = json.loads((experimental_dir / "figure_manifest.json").read_text(encoding="utf-8"))
    assert experimental["schema"] == "TITAN_V46_SPH_DIAGNOSTIC_FIGURES_V1"
    expected_experimental = {
        f"sph_baseline_{name}.{suffix}"
        for name in ("roc", "pr", "calibration", "score_distributions")
        for suffix in ("png", "pdf")
    }
    assert set(experimental["assets"]) == expected_experimental
    for name, digest in experimental["assets"].items():
        assert hashlib.sha256((experimental_dir / name).read_bytes()).hexdigest() == digest
    for item in ("input", "generator"):
        source = experimental[item]
        assert hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]

    b1_manifest = json.loads(
        (experimental_dir / "sph_b1_calibration_figure_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert b1_manifest["schema"] == "TITAN_V46_SPH_B1_CALIBRATION_FIGURES_V1"
    expected_b1 = {
        "sph_b1_calibration_deltas.png",
        "sph_b1_calibration_deltas.pdf",
    }
    assert set(b1_manifest["assets"]) == expected_b1
    for name, digest in b1_manifest["assets"].items():
        assert hashlib.sha256((experimental_dir / name).read_bytes()).hexdigest() == digest
    for item in ("input", "generator"):
        source = b1_manifest[item]
        assert hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]

    prevalence_manifest = json.loads(
        (experimental_dir / "sph_b1_prevalence_figure_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert prevalence_manifest["schema"] == "TITAN_V46_SPH_B1_PREVALENCE_FIGURE_MANIFEST_V1"
    expected_prevalence = {
        "sph_b1_prevalence_comparison.png",
        "sph_b1_prevalence_comparison.pdf",
    }
    assert set(prevalence_manifest["assets"]) == expected_prevalence
    for name, digest in prevalence_manifest["assets"].items():
        assert hashlib.sha256((experimental_dir / name).read_bytes()).hexdigest() == digest
    for item in ("input", "generator"):
        source = prevalence_manifest[item]
        assert hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]

    pac_manifest = json.loads(
        (experimental_dir / "sph_pac_head_comparison_32805.figure_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert pac_manifest["schema"] == "TITAN_V46_SPH_PAC_HEAD_FIGURE_V1"
    expected_pac = {
        "sph_pac_head_comparison_32805.png",
        "sph_pac_head_comparison_32805.pdf",
    }
    assert set(pac_manifest["files"]) == expected_pac
    for name, digest in pac_manifest["files"].items():
        assert hashlib.sha256((experimental_dir / name).read_bytes()).hexdigest() == digest
    assert pac_manifest["source_aggregate_sha256"] == hashlib.sha256(
        (ROOT / "outputs/results/benchmarkmax/sph_pac_head_comparison_32805.json").read_bytes()
    ).hexdigest()

    assert actual_media == (
        {f"outputs/figures/{name}" for name in expected}
        | {f"outputs/figures/external_sph/{name}" for name in sph_files}
        | {f"outputs/figures/external_sph_pac/{name}" for name in pac_files}
        | {f"outputs/figures/benchmarkmax/{name}" for name in expected_experimental}
        | {f"outputs/figures/benchmarkmax/{name}" for name in expected_b1}
        | {f"outputs/figures/benchmarkmax/{name}" for name in expected_prevalence}
        | {f"outputs/figures/benchmarkmax/{name}" for name in expected_pac}
    )
