from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.benchmarkmax.plot_sph_prevalence_comparison import render_figure

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "outputs/results/benchmarkmax/sph_b1_prevalence_comparison_32763.json"


def test_render_prevalence_comparison_png_and_pdf_from_aggregate(tmp_path):
    pytest.importorskip("matplotlib")

    outputs = render_figure(REPORT, tmp_path)

    assert set(outputs) == {
        "sph_b1_prevalence_comparison.png",
        "sph_b1_prevalence_comparison.pdf",
    }
    assert all((tmp_path / name).stat().st_size > 1000 for name in outputs)


def test_renderer_rejects_missing_endpoint_interval(tmp_path):
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    del report["endpoints"]["P8:PAC"]["patient_cluster_bootstrap_deltas"]["comparisons"][
        "platt_minus_prevalence"
    ]["ece"]["ci95"]
    path = tmp_path / "incomplete.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="CI95"):
        render_figure(path, tmp_path / "out")


def test_renderer_rejects_nonaggregate_input(tmp_path):
    path = tmp_path / "not-aggregate.json"
    path.write_text('{"schema":"individual-ledger"}', encoding="utf-8")

    with pytest.raises(ValueError, match="aggregate"):
        render_figure(path, tmp_path / "out")
