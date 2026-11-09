from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "scale_sensitivity", ROOT / "scripts/benchmarkmax/sph_scale_sensitivity.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sample_row(score, labels, top1="A", fallback=False):
    return {"status": "scored", "profiles": {
        "P6": {"scores": {"A": score}, "labels": labels, "top1": top1, "used_fallback": fallback},
        "P8": {"scores": {"A": score}, "labels": labels, "top1": top1, "used_fallback": fallback},
        "P4": {"scores": {"A": score}, "labels": labels, "top1": top1, "used_fallback": fallback},
    }}


def test_selection_is_order_independent_and_requires_full_sample():
    ids = [f"record-{i}" for i in range(200)]
    assert module.select_records(ids, 128) == module.select_records(reversed(ids), 128)
    with pytest.raises(ValueError):
        module.select_records(ids, 201)
    with pytest.raises(ValueError):
        module.select_records(["same", "same"], 1)


def test_paired_changes_and_failure_detection():
    baseline = [sample_row(0.25, []), sample_row(0.75, ["A"])]
    modified = [sample_row(0.5, ["A"], "B", True), sample_row(0.5, [])]
    summary = module.compare(baseline, modified)
    assert summary["records"] == 2
    assert summary["profiles"]["P4"]["score_changes"]["A"]["mean_absolute"] == 0.25
    assert summary["profiles"]["P4"]["score_changes"]["A"]["label_changes"] == 2
    assert summary["profiles"]["P8"]["fallback_changes"] == 1
    with pytest.raises(ValueError):
        module.compare(baseline, modified[:1])
    modified[0]["status"] = "inference_failure"
    with pytest.raises(ValueError):
        module.compare(baseline, modified)
