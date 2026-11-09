from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGGREGATE = ROOT / "outputs/results/benchmarkmax/sph_b1_prevalence_comparison_32763.json"
RESULTS = ROOT / "docs/benchmarkmax/B1_SPH_PREVALENCE_RESULTS.md"
FIGURE_MANIFEST = ROOT / "outputs/figures/benchmarkmax/sph_b1_prevalence_figure_manifest.json"


def test_prevalence_result_document_reconciles_with_aggregate():
    report = json.loads(AGGREGATE.read_text(encoding="utf-8"))
    document = RESULTS.read_text(encoding="utf-8")
    assert "not independent," in document.lower()
    assert "external, or clinical validation" in document.lower()
    assert "ECG statement" in document

    for name, endpoint in report["endpoints"].items():
        support = endpoint["source_support"]
        support_row = (
            f"| {name.replace(':', ' ')} | {support['positive_records']:,} | "
            f"{support['negative_records']:,} | {support['positive_patients']:,} |"
        )
        assert support_row in document
        bootstrap = endpoint["patient_cluster_bootstrap_deltas"]["comparisons"]
        for metric, title in (("brier", "Brier Score"), ("ece", "10-Bin ECE"), ("log_loss", "Log-Loss")):
            assert f"### {title}" in document
            values = endpoint["metrics"]
            deltas = []
            for comparison in ("raw_minus_prevalence", "platt_minus_prevalence"):
                result = bootstrap[comparison][metric]
                deltas.append(
                    f"{result['point_difference_first_minus_second']:+.6f} "
                    f"[{result['ci95'][0]:+.6f}, {result['ci95'][1]:+.6f}]"
                )
            row = (
                f"| {name.replace(':', ' ')} | {values['raw_v45_oof'][metric]:.6f} | "
                f"{values['constant_prevalence_oof'][metric]:.6f} | "
                f"{values['platt_oof'][metric]:.6f} | {deltas[0]} | {deltas[1]} |"
            )
            assert row in document


def test_prevalence_figure_manifest_binds_aggregate_renderer_and_assets():
    manifest = json.loads(FIGURE_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema"] == "TITAN_V46_SPH_B1_PREVALENCE_FIGURE_MANIFEST_V1"
    assert manifest["input"]["path"] == "outputs/results/benchmarkmax/sph_b1_prevalence_comparison_32763.json"
    assert manifest["input"]["sha256"] == hashlib.sha256(AGGREGATE.read_bytes()).hexdigest()
    generator = ROOT / manifest["generator"]["path"]
    assert manifest["generator"]["sha256"] == hashlib.sha256(generator.read_bytes()).hexdigest()
    expected_assets = {"sph_b1_prevalence_comparison.png", "sph_b1_prevalence_comparison.pdf"}
    assert set(manifest["assets"]) == expected_assets
    for name, digest in manifest["assets"].items():
        assert hashlib.sha256((FIGURE_MANIFEST.parent / name).read_bytes()).hexdigest() == digest
