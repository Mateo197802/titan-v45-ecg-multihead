import importlib
import zipfile
from pathlib import Path

import numpy as np
import pytest
import torch


@pytest.fixture
def closure(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/evaluation"))
    return importlib.import_module("score_reviewer_closure_ludb")


def test_inventory_uses_publisher_checksums_not_diagnoses(closure, tmp_path):
    archive = tmp_path / "source.zip"
    files = {"RECORDS": b"data/1\n", "data/1.hea": b"header", "data/1.dat": b"waveform"}
    checks = "\n".join(f"{closure.sha256(blob)}  {name}" for name, blob in files.items())
    with zipfile.ZipFile(archive, "w") as z:
        for k, v in files.items():
            z.writestr(closure.PREFIX + k, v)
        z.writestr(closure.PREFIX + "SHA256SUMS.txt", checks)
    raw, enrolled, receipt = closure.inventory(archive, tmp_path, 1)
    assert enrolled == ["data/1"]
    assert (raw / "data/1.dat").read_bytes() == files["data/1.dat"]
    assert receipt["publisher_verified_waveform_files"] == 2
    with pytest.raises(ValueError, match="enrollment"):
        closure.inventory(archive, tmp_path, 2)


def test_joint_decision_keeps_abstention_separate_from_technical_failure(closure):
    policy = {"cutoffs": {"P8": 0.1, "P4": 0.1}}
    thresholds = {"P8": {"a": 0.5}, "P4": {"b": 0.5}}
    profiles = {"P8": {"status": "scored", "scores": {"a": 0.1}, "labels": ["a"]},
                "P4": {"status": "scored", "scores": {"b": 0.3}, "labels": []}}
    assert closure.route(profiles, thresholds, policy)["emitted"] == {"P8": ["a"], "P4": []}
    profiles["P4"]["scores"]["b"] = 0.49
    assert closure.route(profiles, thresholds, policy)["state"] == "abstained"
    assert closure.route(profiles, thresholds, policy)["emitted"] is None
    profiles["P4"] = {"status": "technical_unscored"}
    assert closure.route(profiles, thresholds, policy)["state"] == "technical_unscored"


def test_runtime_hook_detects_wrong_morphology_slice(closure):
    audit = closure.TensorAudit(torch)
    sample = (np.zeros((12, 1250)), np.ones(12), np.arange(10, dtype=np.float32))
    audit.start([sample])
    head = torch.nn.Identity()
    audit.attach_head("P4", head, 670)
    x = torch.zeros(1, 670)
    x[:, 640:650] = torch.arange(10)
    head(x)
    assert audit.counts["P4"]["windows"] == 1
    with pytest.raises(ValueError, match="layout"):
        head(x.roll(1, dims=1))
    audit.remove()
