import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_a10_table_identifies_each_real_release_model():
    manifest = json.loads((ROOT / "release-manifest.json").read_bytes())
    doc = (ROOT / "docs/reproducibility/a10_verified_artifacts.md").read_text(encoding="utf-8")
    weights = [entry for entry in manifest["assets"] if entry["category"] == "model"]
    assert len(weights) == 5
    for entry in weights:
        row = f"[{entry['name']}]({entry['download_url']}) | {entry['bytes']} | `{entry['sha256']}`"
        assert row in doc
    assert "NOT_AVAILABLE" in doc


def test_v3c_summary_agrees_with_its_nine_row_figure_snapshot():
    summary = json.loads((ROOT / "outputs/results/optuna/v3c_promoted_configuration.json").read_bytes())
    with (ROOT / "tests/figure_evaluation/tables_snapshot/optuna_trials.csv").open(
        encoding="utf-8", newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == summary["completed_trials"] == 9
    ranking = max(rows, key=lambda row: float(row["ranking_score"]))
    peak = max(rows, key=lambda row: float(row["peak_composite_score"]))
    assert int(ranking["trial"]) == summary["best_trial"] == 6
    assert int(peak["trial"]) == 8
    assert float(ranking["ranking_score"]) == summary["ranking_score"]
    for name, value in summary["parameters"].items():
        assert float(ranking[name]) == pytest.approx(value, rel=1e-8, abs=1e-15)
