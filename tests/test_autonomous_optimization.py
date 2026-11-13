"""Regression checks for the frozen autonomous search policy."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts" / "domain_adaptation"
sys.path.insert(0, str(SCRIPTS))
try:
    from autonomous_export import ancestry
    from autonomous_interval_audit import interval
    from autonomous_loop import INITIAL, next_phase, qualifies, ranked, run_fit
    from autonomous_worker import PROTOCOL, settings
    from train_duration_aware import digest
finally:
    sys.path.remove(str(SCRIPTS))


def fit(arm, seed, f1=.61, class_ok=True, source=.52):
    return {"arm": arm, "seed": seed, "sources": {"chapman": source, "cpsc": .80},
            "guards": {"SB": {"pass": class_ok}}, "calibration_guard": True,
            "summary": {"f1": f1, "average_precision": .57, "brier_score": .01, "ece": .01}}


def test_gates_override_high_f1_and_a_single_seed():
    base = {"chapman": .52, "cpsc": .80}
    good = fit("linear", 20261112)
    unsafe = fit("late", 20261112, .9, class_ok=False)
    unstable = fit("balanced", 20261112, .8, source=.48)
    assert ranked([unsafe, unstable, good], base)[0] == good
    seeds = settings()["seeds"]
    family = [fit("linear", seed) for seed in seeds]
    assert qualifies(family, base, .58, seeds)
    assert not qualifies(family[:1], base, .58, seeds)
    family[1]["summary"]["f1"] = .57
    assert not qualifies(family, base, .58, seeds)


def test_rejected_hypothesis_is_not_repeated_at_same_anchor():
    state = {"working": INITIAL, "cycles": [], "screens": [{"endpoint": "SB", "arm": "linear", "anchor": INITIAL}]}
    assert "linear" not in next_phase(state, settings())["arms"]
    state["working"] = "sealed-composite"
    assert "linear" in next_phase(state, settings())["arms"]


def test_permanent_integrity_failure_does_not_retry(tmp_path):
    (tmp_path / "attempts").mkdir()
    (tmp_path / "fits").mkdir()
    state, path = {"attempts": []}, tmp_path / "state.json"
    phase = {"number": 1, "endpoint": "SB"}

    class InvalidRunner:
        def fit(self, *_):
            raise ValueError("label provenance mismatch")

    with pytest.raises(ValueError, match="provenance mismatch"):
        run_fit(tmp_path, path, state, InvalidRunner(), phase, {}, "linear", 20261112, "100")
    persisted = json.loads(path.read_bytes())
    assert persisted["attempts"][0]["outcome"] == "PERMANENT_ERROR"
    with pytest.raises(ValueError, match="prior fit"):
        run_fit(tmp_path, path, persisted, InvalidRunner(), phase, {}, "linear", 20261112, "101")


def test_transient_attempt_retries_at_most_once(tmp_path):
    (tmp_path / "attempts").mkdir()
    (tmp_path / "fits").mkdir()
    state, path = {"attempts": []}, tmp_path / "state.json"
    phase = {"number": 1, "endpoint": "SB"}

    class InterruptedRunner:
        def fit(self, *_):
            raise OSError("temporary node failure")

    for job in ("100", "101"):
        with pytest.raises(OSError):
            run_fit(tmp_path, path, state, InterruptedRunner(), phase, {}, "linear", 20261112, job)
    assert run_fit(tmp_path, path, state, InterruptedRunner(), phase, {}, "linear", 20261112, "102") is None
    assert len(json.loads(path.read_bytes())["attempts"]) == 2


def test_resume_publishes_completed_receipt_without_retraining(tmp_path):
    fit_id = "01-SB-linear-20261112"
    stage = tmp_path / "attempts" / f"{fit_id}-1"
    stage.mkdir(parents=True)
    (tmp_path / "fits").mkdir()
    (stage / "best.pt").write_bytes(b"synthetic checkpoint")
    (stage / "private_scores.npz").write_bytes(b"synthetic scores")
    receipt = {"checkpoint_sha256": digest(stage / "best.pt"), "scores_sha256": digest(stage / "private_scores.npz"),
               "protocol_sha256": digest(PROTOCOL), "test_opened": False}
    (stage / "fit.json").write_text(json.dumps(receipt), encoding="utf-8")
    state = {"attempts": [{"fit": fit_id, "stage": stage.name, "job": "100", "outcome": "STARTED"}]}
    phase = {"number": 1, "endpoint": "SB"}
    # A missing runner proves a completed attempt is never dispatched again.
    assert run_fit(tmp_path, tmp_path / "state.json", state, None, phase, {}, "linear", 20261112, "101") == receipt
    assert (tmp_path / "fits" / fit_id / "fit.json").is_file()
    assert not stage.exists()
    assert len(state["attempts"]) == 1


def test_composite_ancestry_checks_multiple_checkpoints_and_cycles():
    fits = {"sb": {"checkpoint_sha256": "sb-hash", "anchor_sha256": "original"},
            "afib": {"checkpoint_sha256": "afib-hash", "anchor_sha256": "sb-hash"},
            "avb": {"checkpoint_sha256": "avb-hash", "anchor_sha256": "afib-hash"}}
    assert ancestry(fits, "avb") == ["avb", "afib", "sb"]
    fits["sb"]["anchor_sha256"] = "avb-hash"
    with pytest.raises(ValueError, match="cyclic"):
        ancestry(fits, "avb")


def test_paired_interval_has_fixed_endpoints_and_patient_clusters():
    patient = np.repeat(np.arange(20), 2)
    y = np.column_stack([np.tile([0, 1], 20), np.tile([1, 0], 20)])
    a = y * .8 + .1
    worse = a.copy()
    worse[0:2] = 1 - worse[0:2]
    assert interval(y, a, a, patient, [.5, .5], [.5, .5], 100, 7) == (0., 0., 0., 100)
    point, low, high, count = interval(y, a, worse, patient, [.5, .5], [.5, .5], 100, 7)
    assert count == 100
    assert low <= point < 0
    assert high == 0.
