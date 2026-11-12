import csv
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


def test_paired_metrics_mask_unknown_and_protect_support(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/external_validation"))
    from evaluate_code15 import label, paired_metrics

    assert label("False") == 0
    assert label("") == label("unspecified") == -1
    y = np.array([[1, -1], [1, -1], [0, 0], [0, 0], [-1, 0]])
    old = np.array([[.8, .9], [.2, .1], [.2, .2], [.8, .1], [.9, .8]])
    new = np.array([[.8, .9], [.8, .1], [.2, .2], [.2, .1], [.9, .8]])
    config = dict(bootstrap_seed=42, bootstrap_replicates=100,
                  minimum_distinct_positive_and_negative_patients=1,
                  promotion_macro_f1_gain_min=.03, promotion_max_sensitivity_drop=.05,
                  promotion_max_macro_brier_increase=.01, promotion_max_empty_set_rate_increase=.01)
    rows, comparison = paired_metrics(
        y, old, new, np.array(["a", "a", "b", "c", "d"]), np.array([.5, .5]), ["AFIB", "SB"], config,
    )
    assert rows[0]["n_ecg_with_reference"] == 4
    assert rows[0]["n_positive_patients"] == 1
    assert rows[1]["f1"] == 1 and rows[0]["f1"] == .5
    assert rows[2]["estimable"] is False and rows[2]["specificity"] is None
    assert comparison["macro_f1_delta"] == .5 and not comparison["observed_metric_gate_pass"]


def test_bounded_adapter_is_not_unanchored(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/external_validation"))
    from fit_code_transfer import fit_endpoint, residual_logits

    x = np.array([[-2.], [-1.], [1.], [2.]])
    initial = np.zeros(4)
    theta, iterations = fit_endpoint(x, initial, np.array([0, 0, 1, 1]), np.ones(4),
                                     cap=1.5, l2=.05, maxiter=80)
    adjusted = residual_logits(x, initial, np.zeros(1), np.ones(1), theta, 1.5)
    assert iterations > 0
    assert adjusted[0] < 0 < adjusted[-1]
    assert np.max(np.abs(adjusted)) <= 1.5


def test_independent_verifier_handles_ranking_ties(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/external_validation"))
    from evaluate_code15 import estimates
    from verify_code15_evaluation import independent_estimates

    y = np.array([1, 0, 1, 0])
    scores = np.array([.8, .8, .7, .1])
    assert independent_estimates(y, scores, .75) == estimates(y, scores >= .75, scores)


def test_locked_evaluator_hdf5_join_and_cached_resume(tmp_path, monkeypatch):
    h5py = pytest.importorskip("h5py")
    root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(root / "scripts/external_validation"))
    import evaluate_code15 as evaluator
    import verify_code15_evaluation as verifier

    code = tmp_path / "code15"
    code.mkdir()
    output = tmp_path / "partial"
    candidate_dir = tmp_path / "candidate"
    candidate_dir.mkdir()
    patients = [f"patient-{i}" for i in range(500) if evaluator.selected(f"patient-{i}")][:8]
    rng = np.random.default_rng(7)
    archives, metadata = [], []
    config = json.loads((root / "docs/external_validation_20261111/FROZEN_CODE15_PROTOCOL.json").read_bytes())
    config["evaluation"].update(bootstrap_replicates=15, minimum_distinct_positive_and_negative_patients=1)
    endpoints = list(config["reference"])
    for j, part in enumerate((10, 15)):
        member = f"exams_part{part}.hdf5"
        ids = np.arange(1 + 4 * j, 5 + 4 * j)
        waveforms = np.pad(rng.normal(size=(4, 4000, 12)).astype(np.float32),
                           ((0, 0), (48, 48), (0, 0)))
        with h5py.File(tmp_path / member, "w") as h5:
            h5["exam_id"] = ids
            h5["tracings"] = waveforms
        archive = code / f"exams_part{part}.zip"
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.write(tmp_path / member, member)
        archives.append({"key": archive.name, "size": archive.stat().st_size,
                         "checksum": "md5:" + hashlib.md5(archive.read_bytes(), usedforsecurity=False).hexdigest()})
        for i, exam in enumerate(ids):
            metadata.append({"trace_file": member, "exam_id": int(exam),
                             "patient_id": patients[j * 4 + i],
                             **dict.fromkeys(config["reference"].values(), i % 2)})
    index = code / "exams.csv"
    with index.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(metadata[0]))
        writer.writeheader()
        writer.writerows(metadata)
    catalog = code / "record.json"
    catalog.write_text(json.dumps({"files": archives}), encoding="utf-8")
    config.update(metadata_sha256=evaluator.digest(index), catalog_sha256=evaluator.digest(catalog))
    protocol = tmp_path / "protocol.json"
    protocol.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(evaluator, "PROTOCOL", protocol)
    monkeypatch.setattr(verifier, "PROTOCOL", protocol)
    receipt = {"protocol_sha256": evaluator.digest(protocol), "endpoints": endpoints,
               "code_or_mimic_outcomes_used": False, "thresholds_changed": False, "profiles": {}}
    for profile in config["evaluation"]["profiles"]:
        path = candidate_dir / f"{profile}.npz"
        np.savez(path, endpoints=endpoints, mean=np.zeros(2), scale=np.ones(2),
                 coefficients=np.zeros((3, 5)), cap=np.asarray(1.5))
        receipt["profiles"][profile] = {"sha256": evaluator.digest(path)}
    (candidate_dir / "candidate_receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    thresholds = {p: dict.fromkeys(endpoints, .5) for p in config["evaluation"]["profiles"]}
    monkeypatch.setitem(sys.modules, "probe_frozen", SimpleNamespace(
        load_scorers=lambda *_: (None, None, {}, thresholds),
    ))
    monkeypatch.setattr(evaluator, "historical_signatures", lambda *_: (np.zeros((1, 3000)), 0))
    monkeypatch.setattr(evaluator, "_safe_morphology", lambda *_: lambda *_a, **_k: np.zeros(2))
    scored = []

    def batch(_model, samples):
        scored.append(len(samples))
        return {p: (np.zeros((len(samples), 2)), np.ones((len(samples), 8), dtype=np.float32))
                for p in thresholds}

    monkeypatch.setattr(evaluator, "_rhythm_batch", batch)
    args = dict(study=tmp_path, candidates=candidate_dir, assets=tmp_path, historical=tmp_path,
                scratch=tmp_path / "scratch", output=output, archives=["exams_part10.zip"],
                reuse_partial=None)
    args["scratch"].mkdir()
    evaluator.run(SimpleNamespace(**args))
    first = json.loads((output / "code15_evaluation_receipt.json").read_bytes())
    assert first["n_ecg"] == 4 and not first["complete_archive_coverage"]
    assert first["point_estimates_independently_verified"]["status"] == "PASS"
    full_output = tmp_path / "full"
    args.update(output=full_output, archives=None, reuse_partial=output)
    evaluator.run(SimpleNamespace(**args))
    final = json.loads((full_output / "code15_evaluation_receipt.json").read_bytes())
    assert scored == [4, 4]
    assert final["n_ecg"] == 8 and final["complete_archive_coverage"]
    assert final["reused_verified_first_archive"] and final["promotion"]["P6"]["decision"] == "FAIL"
