from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/evaluation"))
try:
    import reviewer_morphology_multiseed as morph
    import reviewer_morphology_runtime as runtime
    import reviewer_selective_utility as selective
finally:
    sys.path.pop(0)


def test_numerical_fixtures_and_flat_line_artifact():
    mod = runtime.imported(ROOT / "scripts/cedia/recovery_candidates/morphology_features_v4.py", "morph_fixture")
    result = runtime.check_fixtures(mod)
    assert len(result["observed"]) == 10
    assert result["pulse_peak_count"] == 3
    assert result["flat_line_artifact"]["peaks"] == 36
    assert result["flat_line_artifact"]["normalized_values"][0] > .9


def test_equal_coverage_finite_utility_and_denominators():
    import json

    recipe = json.loads((ROOT / "configs/reviewer_experiments/two_comment_rigorous_v1.json").read_text())["selective"]
    recipe["replicates"] = 200
    endpoints = [("P8", "R"), ("P4", "P")]
    thresholds = {"P8": {"R": .5}, "P4": {"P": .5}}
    rows = []
    for i in range(100):
        p = .9 if i % 2 else .53
        profiles = {"P8": {"scores": {"R": p}, "labels": ["R"]},
                    "P4": {"scores": {"P": p}, "labels": ["P"]}}
        rows.append((str(i), str(i//2), profiles, p-.6, [int(i % 2), -1]))
    rows.append(("failed", "failed", None, None, [1, 0]))
    result = selective.evaluate(rows, endpoints, thresholds, recipe)
    assert result["technical_unscored"] == 1
    assert result["known_scored_opportunities"] == 100
    assert result["unknown_scored_opportunities"] == 100
    frozen = result["rules"]["frozen_joint"]
    assert frozen["accepted"] == 50
    assert frozen["accepted_risk"] == 0
    assert frozen["withheld_errors"] == 50
    assert frozen["endpoints"]["P8:R"]["positive_technical_unscored"] == 1
    assert frozen["endpoints"]["P8:R"]["tp"] == 50
    assert frozen["endpoints"]["P8:R"]["accepted_score_brier"] == pytest.approx(.01)
    assert result["rules"]["random_equal_coverage"]["accepted_risk"] == .5
    assert frozen["full_scored_cost"]["1"] == .5


def test_window_membership_and_identical_arm_retraining():
    torch = pytest.importorskip("torch")
    torch.set_num_threads(1)
    rng = np.random.default_rng(7)
    x = rng.normal(size=(40, 5))
    ids = np.arange(20)
    wi = np.repeat(ids, 2)
    y = ids % 2
    params = {"learning_rate": .025, "weight_decay": .001, "batch_size": 16, "epochs": 2}
    one, two = (morph.fit_arm(x, wi, ids, y, 1978, params) for _ in range(2))
    np.testing.assert_array_equal(morph.scores(one, x, wi, ids, "P6"),
                                  morph.scores(two, x, wi, ids, "P6"))
    with pytest.raises(ValueError, match="missing"):
        morph.window_index(wi, np.array([0, 20]))
