import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from titan_v45.data.external_ecg import LEADS


@pytest.fixture
def modules(monkeypatch):
    pytest.importorskip("h5py")
    root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(root / "scripts/domain_adaptation"))
    return tuple(importlib.import_module(name) for name in ("freeze_candidate", "evaluate_new_holdout"))


def test_selection_repeats_then_uses_median_seed(modules):
    select, _ = modules
    seeds = (1, 2, 3)
    scores = {"frozen_backbone_mlp": (.52, .53, .54), "partial": (.68, .64, .66), "nonfinalist": (.60,)}
    rows = [{"mode": mode, "normalization": "normal", "seed": seed, "validation_macro_ap": score,
             "validation_macro_f1_at_half": score / 2, "checkpoint_sha256": str(seed), "slurm_job": str(seed)}
            for mode, values in scores.items() for seed, score in enumerate(values, 1)]
    cfg = {"eligible_nonfrozen": ["partial", "nonfinalist"]}
    selected, results = select.choose(rows, cfg, seeds)
    assert (selected["mode"], selected["seed"]) == ("partial", 3)
    assert results[1]["mean_macro_ap"] == pytest.approx(.66)
    with pytest.raises(ValueError, match="seed coverage incomplete"):
        select.choose([r for r in rows if r["seed"] != 2], cfg, seeds)


def test_calibration_and_paired_bootstrap_use_valid_reference_and_patients(modules):
    _, evaluate = modules
    labels = np.asarray([[1], [1], [0], [0], [-1]])
    people = np.asarray(["a", "a", "b", "c", "d"])
    base = np.asarray([[.3], [.3], [.7], [.2], [.99]])
    new = np.asarray([[.9], [.8], [.2], [.1], [.99]])
    thresholds, policy = evaluate.thresholds_on_calibration(labels, new, ["AFIB"])
    assert policy["AFIB"]["floor_met"] and policy["AFIB"]["calibration_sensitivity"] == 1
    points, paired, macro = evaluate.intervals(
        labels, {"P6": base, "P8": base, "candidate": new},
        {"P6": [.5], "P8": [.5], "candidate": thresholds}, people, ["AFIB"],
        {"support_min_positive_and_negative_patients": 1, "bootstrap_seed": 42, "bootstrap_replicates": 32})
    assert points[-1]["positive_ecgs"] == 2 and points[-1]["positive_patients"] == 1
    assert points[-1]["tp"] == 2 and points[-1]["fp"] == 0
    assert macro[0]["candidate_minus_baseline"] == 1
    assert paired[1]["value"] == 1


def test_promotion_requires_protected_endpoints_not_only_macro_gain(modules):
    select, evaluate = modules
    cfg = json.loads(select.PROTOCOL.read_bytes())
    endpoints = "|".join(cfg["endpoints"])
    aggregates = [{"model": model, "duration": "all", "endpoints": endpoints, "macro_f1": score,
                   "candidate_minus_baseline": .20, "paired_ci_low": .10}
                  for model, score in (("P6", .55), ("P8", .55), ("candidate", .75))]
    points = [{"model": model, "duration": "all", "endpoint": endpoint, "sensitivity": .80, "ppv": .80, "brier": .03}
              for model in ("P6", "P8", "candidate") for endpoint in cfg["endpoints"]]
    assert evaluate.within_code_decision(points, aggregates, cfg)["external_adaptation"] == "PASS"
    next(x for x in points if x["model"] == "candidate" and x["endpoint"] == "AFIB")["sensitivity"] = .70
    result = evaluate.within_code_decision(points, aggregates, cfg)
    assert result["research_target_met"] and result["external_adaptation"] == "FAIL"
    assert result["independent_generalization"] == "NOT_EVALUATED"


def test_reduce_consumes_sealed_scores_without_inference(modules, monkeypatch, tmp_path):
    select, evaluate = modules
    cfg = json.loads(select.PROTOCOL.read_bytes())
    cfg["calibration"]["bootstrap_replicates"] = 16
    protocol = tmp_path / "protocol.json"
    evaluate.write_json(protocol, cfg)
    monkeypatch.setattr(evaluate, "PROTOCOL", protocol)
    threshold_file = tmp_path / "FROZEN_CANDIDATE_THRESHOLDS.json"
    evaluate.write_json(threshold_file, {})
    scores = tmp_path / "private_test_predictions.npz"
    y = np.tile(np.arange(40)[:, None] % 2, (1, 5))
    p = y * .8 + .1
    np.savez(scores, exams=np.arange(40), patients=np.arange(40), durations=np.full(40, 917), labels=y,
             candidate=p, P6=1 - p, P8=1 - p)
    evaluate.write_json(tmp_path / "WITHIN_CODE_SCORE_RECEIPT.json", {
        "test_ecgs": 40, "test_patients": 40, "private_prediction_sha256": evaluate.digest(scores),
        "protocol_sha256": evaluate.digest(protocol), "threshold_file_sha256": evaluate.digest(threshold_file),
        "operating_thresholds": {name: [.5] * 5 for name in ("P6", "P8", "candidate")}})
    result = tmp_path / "delivery"
    evaluate.reduce(tmp_path, result)
    assert len(list(result.iterdir())) == 7
    scores.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="sealed prediction"):
        evaluate.reduce(tmp_path, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_multisource_reader_masks_unobserved_targets_and_fails_on_identity_change(modules, monkeypatch, tmp_path):
    try:
        importlib.import_module("wfdb")
    except ModuleNotFoundError:
        monkeypatch.setitem(sys.modules, "wfdb", SimpleNamespace(rdheader=None, rdrecord=None))
    extra = importlib.import_module("build_additional_sources")
    folder = tmp_path / "cpsc2018"
    folder.mkdir()
    base = "record.v1"
    (folder / f"{base}.hea").write_text("synthetic", encoding="ascii")
    data = folder / f"{base}.dat"
    data.write_bytes(b"sealed")
    header = SimpleNamespace(fs=500, sig_len=5200, file_name=[data.name] * 12)
    monkeypatch.setattr(extra.wfdb, "rdheader", lambda _: header)

    def signal(_, sampfrom, sampto):
        assert (sampfrom, sampto) == (100, 5100)
        t = np.arange(sampto - sampfrom) / 500
        return SimpleNamespace(p_signal=np.sin(t[:, None] * np.arange(1, 13)[None, :]), sig_name=LEADS, units=["mV"] * 12)

    monkeypatch.setattr(extra.wfdb, "rdrecord", signal)
    endpoints = ["AFIB", "SB", "STACH", "RBBB", "1AVB"]
    row = {"source": "cpsc2018", "relative_record": base, "signal_sha256": extra.digest(data),
           "classes": endpoints, "targets": [1, 1, 0, 0, 0], "mask": [1, 0, 0, 1, 1]}
    result, error = extra.read_candidate(tmp_path, endpoints, row)
    assert error is None and result[0].shape == (12, 1250) and result[2] == [1, -1, -1, 0, 0]
    data.write_bytes(b"different")
    with pytest.raises(ValueError, match="source_waveform_identity_mismatch"):
        extra.read_candidate(tmp_path, endpoints, row)
