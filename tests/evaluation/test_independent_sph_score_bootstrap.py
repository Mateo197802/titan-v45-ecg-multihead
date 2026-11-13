from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from titan_v45.evaluation import sph_report

ROOT = Path(__file__).resolve().parents[2]


def load_script(name):
    path = ROOT / "scripts" / "external_validation" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_score_intervals_match_frozen_corrected_evaluator(monkeypatch):
    checker = load_script("independent_sph_score_bootstrap")
    correction = load_script("evaluate_sph_ece_corrected")
    original = sph_report._metric_values
    monkeypatch.setattr(
        sph_report,
        "_metric_values",
        lambda y, p, s, w, n: correction.corrected_metric_values(original, y, p, s, w, n),
    )
    y = np.array([0, 1, 0, 1, 0, 1, 1, 0])
    scores = np.array([0.0, 0.1, 0.1, 0.3, 0.3, 0.7, 1.0, 1.0])
    clusters = ["a", "a", "b", "c", "d", "e", "e", "f"]
    expected = sph_report._cluster_bootstrap(
        y, scores >= 0.5, scores, clusters, seed=17, replicates=100, ece_bins=10
    )
    actual = checker.score_intervals(y, scores, clusters, seed=17, replicates=100, bins=10)
    checker.compare_intervals(actual, expected)


def test_degenerate_draws_and_invalid_input():
    checker = load_script("independent_sph_score_bootstrap")
    result = checker.score_intervals([0, 0], [0.1, 0.9], ["a", "b"], seed=0, replicates=5, bins=10)
    assert result["auroc"]["valid_replicates"] == 0
    assert result["average_precision"]["valid_replicates"] == 0
    assert result["brier_score"]["valid_replicates"] == 5
    with pytest.raises(ValueError):
        checker.score_intervals([0, 1], [0.0, 1.1], ["a", "b"], seed=0, replicates=5, bins=10)


def test_interval_comparison_rejects_changed_or_missing_results():
    checker = load_script("independent_sph_score_bootstrap")
    observed = checker.score_intervals([0, 1], [0.1, 0.9], ["a", "b"],
                                       seed=1, replicates=10, bins=10)
    expected = {key: value.copy() for key, value in observed.items()}
    expected["brier_score"]["high"] += 0.1
    with pytest.raises(ValueError, match="brier_score"):
        checker.compare_intervals(observed, expected)
    del expected["ece"]
    expected["brier_score"] = observed["brier_score"]
    with pytest.raises(ValueError, match="ece"):
        checker.compare_intervals(observed, expected)


def test_published_receipt_has_all_endpoints_and_verified_script():
    path = ROOT / "outputs/results/external_sph/sph_independent_score_bootstrap_32728.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    protocol = json.loads((ROOT / "configs/external_validation/sph_frozen.json").read_text())
    names = {f"{item['profile']}:{item['name']}" for item in protocol["endpoints"]}
    assert set(receipt["endpoints"]) == names
    assert all(item == {"score_metrics": 4, "primary_and_sensitivity": True}
               for item in receipt["endpoints"].values())
    assert receipt["individual_records_exported"] is False
    script = ROOT / "scripts/external_validation/independent_sph_score_bootstrap.py"
    assert receipt["script_sha256"] == hashlib.sha256(script.read_bytes()).hexdigest()
    assert receipt["inputs"]["aggregate"] == "09f93d9f310baaca672a33b0f369593cd88835a8ef08dc9929945c57cf18c988"
    assert receipt["inputs"]["protocol"] == hashlib.sha256(
        (ROOT / "configs/external_validation/sph_frozen.json").read_bytes()
    ).hexdigest()
