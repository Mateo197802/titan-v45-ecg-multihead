import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def other(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts" / "evaluation"))
    return importlib.import_module("reviewer_rhythm_other")


def test_normal_not_nsr_and_pac_is_other_only_for_p6(other):
    config = json.loads((ROOT / "configs/reviewer_experiments/november_rhythm_other.json").read_bytes())
    refs = {k: SimpleNamespace(primary_codes=v) for k, v in {
        "normal": {1}, "pac": {30}, "flutter": {51}, "uncertain": {1, 51},
        "qt": {148}, "primary": {50}, "duplicate": {50},
    }.items()}
    signals = dict(zip(refs, ("a", "b", "c", "d", "e", "f", "c"), strict=True))
    p6 = other.states_for(refs, refs, signals, set(config["endpoints"]["P6_Other_mapped"]["codes"]))
    p8 = other.states_for(refs, refs, signals, set(config["endpoints"]["P8_Other_mapped"]["codes"]))
    assert p6 == {"normal": "control", "pac": "positive", "flutter": "discordant_exact_signal",
                  "uncertain": "ambiguous", "qt": "unknown", "primary": "unknown",
                  "duplicate": "discordant_exact_signal"}
    assert p8 == {**p6, "pac": "unknown"}


def test_shared_auxiliary_and_deterministic_order(other):
    p6 = dict.fromkeys(reversed(other.P6), 0.1)
    p8 = dict.fromkeys(reversed(other.P8), 0.2)
    aux = {f"backbone_{i}": i / 10 for i in reversed(range(6))}
    row = {"profiles": {"P6": {"scores": p6, "auxiliary_scores": aux},
                        "P8": {"scores": p8, "auxiliary_scores": dict(aux)}}}
    assert other.feature_vector(row) == [0.1]*6 + [0.2]*8 + [i/10 for i in range(6)]
    row["profiles"]["P8"]["auxiliary_scores"]["backbone_0"] = 0.9
    with pytest.raises(ValueError, match="same six"):
        other.feature_vector(row)


def test_fit_excludes_unknown_and_held_and_reports_full_held_flow(other):
    x = np.asarray([[-2], [2], [-1], [1], [-3], [3], [-4], [4]], dtype=float)
    base = np.asarray([0.1, 0.9, 0.2, 0.8, 0.3, 0.7, 0.4, 0.6])
    keys = tuple("abcdefgh")
    splits = dict(zip(keys + ("unscored",), ["train"]*2 + ["calibration"]*2 + ["held"]*5, strict=True))
    states = dict(zip(keys + ("unscored",),
                      ["control", "positive"]*3 + ["unknown", "ambiguous", "positive"], strict=True))
    policy = {"l2": 0.01, "max_iterations": 250, "minimum_training_per_polarity": 1,
              "minimum_calibration_per_polarity": 1, "minimum_held_per_polarity": 1}
    saved = other.fit_endpoint(x, base, keys, {k: states[k] for k in keys[:4]}, splits, policy)
    assert saved["status"] == "calibrated"
    assert saved["comparator_threshold"] == 0.8

    def metric(y, s, cut):
        assert y.tolist() == [0, 1]
        return int(np.sum(y == (s >= cut)))

    report = other.evaluate_endpoint(
        x, base, keys, states, splits, dict(zip(keys, keys, strict=True)), saved, policy,
        {"seed": 10, "replicates": 10, "confidence": 0.95}, metric,
        lambda *a, **kw: None, lambda *a, **kw: None,
    )
    assert report["matched_known_held_ecgs"] == 2
    assert report["all_metadata_reference_scoring_flow"]["held"]["positive:not_scored"] == 1
    assert report["held_scored_calls_by_reference_state"]["candidate"]["unknown:negative"] == 1
    assert report["known_statement_metrics"]["candidate"]["metrics"] == 2
    assert report["known_statement_metrics"]["released_auxiliary_comparator"]["metrics"] == 1
