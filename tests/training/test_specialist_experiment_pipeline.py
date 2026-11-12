import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "specialist_train_evaluate", ROOT / "scripts/specialist_experiments/train_evaluate.py"
)
pipeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pipeline)


def test_candidate_rhythm_scores_aggregate_by_record_without_mixing_rows():
    records = [
        {"scored": True},
        {"scored": True},
    ]
    features = np.asarray([
        [2.0] * 8,
        [0.0] * 8,
        [-2.0] * 8,
    ], dtype=np.float32)
    window_records = np.asarray([0, 0, 1], dtype=np.int32)

    scores = pipeline._candidate_record_scores(
        torch.nn.Identity(), features, window_records, records, "P8", "cpu"
    )

    assert scores.shape == (2, 8)
    assert np.isclose(scores[0, 0], np.mean([1 / (1 + np.exp(-2)), 0.5]))
    assert np.isclose(scores[1, 0], 1 / (1 + np.exp(2)))


def test_threshold_calibration_uses_only_the_declared_calibration_source():
    records = []
    scores = np.full((6, 6), 0.0)
    for index, label in enumerate([0, 0, 1, 1]):
        targets = [label, 0, 0, 0, 0, 0, 0, 0]
        records.append({"scored": True, "split": "calibration", "source": "chapman_shaoxing",
                        "targets": targets, "mask": [1] * 8})
        scores[index, 0] = [0.1, 0.2, 0.8, 0.9][index]
    for index in range(4, 6):
        records.append({"scored": True, "split": "source_holdout", "source": "georgia",
                        "targets": [1] * 8, "mask": [1] * 8})
        scores[index, 0] = 0.99

    thresholds = pipeline._calibrate_thresholds(records, scores, pipeline.RHYTHM_CLASSES_P6,
                                                "calibration")

    assert 0.2 < thresholds["AFIB"] <= 0.8


def test_threshold_calibration_ignores_unscored_and_nonfinite_records():
    records = [
        {"scored": True, "split": "calibration", "source": "chapman_shaoxing",
         "targets": [0, 0, 0, 0, 0, 0, 0, 0], "mask": [1] * 8},
        {"scored": False, "split": "calibration", "source": "chapman_shaoxing",
         "targets": [1, 0, 0, 0, 0, 0, 0, 0], "mask": [1] * 8},
        {"scored": True, "split": "calibration", "source": "chapman_shaoxing",
         "targets": [1, 0, 0, 0, 0, 0, 0, 0], "mask": [1] * 8},
    ]
    scores = np.zeros((3, 6), dtype=np.float64)
    scores[:, 0] = [0.1, np.nan, 0.9]

    thresholds = pipeline._calibrate_thresholds(records, scores, pipeline.RHYTHM_CLASSES_P6,
                                                "calibration")

    assert thresholds["AFIB"] == 0.9


def test_aggregate_split_summary_contains_no_row_hashes():
    metadata = {
        "study_id": "test",
        "preflight_aggregates": {"rhythm": {"chapman_shaoxing": {"included_records": 2}}},
        "preprocessing_errors_by_source_and_type": {},
        "rhythm_records": [{
            "source": "chapman_shaoxing", "split": "train", "identity_hash": "private-hash",
            "group_hash": "private-group", "scored": True, "targets": [1, 0],
            "mask": [1, 1], "classes": ["A", "B"],
        }],
        "pathology_records": [{
            "source": "ptbxl", "split": "internal_evaluation", "identity_hash": "private-id",
            "group_hash": "private-patient", "scored": True, "targets": [0],
            "mask": [1], "classes": ["ASMI"],
        }],
    }

    result = pipeline._dataset_split_summary(metadata)

    assert result["tasks"]["rhythm"]["chapman_shaoxing"]["train"]["class_support"]["A"] == {
        "observed": 1, "positive": 1, "negative_or_control": 0,
    }
    serialized = str(result)
    assert "private-hash" not in serialized
    assert "private-group" not in serialized
    assert "private-patient" not in serialized


def test_summary_macro_compares_only_identical_evaluable_endpoints():
    rows = [
        {"profile": "P4", "scope": "test", "source": "ptbxl",
         "model": "published_baseline", "endpoint": "ASMI", "estimable": True, "f1": 0.5},
        {"profile": "P4", "scope": "test", "source": "ptbxl",
         "model": "published_baseline", "endpoint": "LVH", "estimable": True, "f1": 0.7},
        {"profile": "P4", "scope": "test", "source": "ptbxl",
         "model": "weighted_bce_seed_1", "endpoint": "ASMI", "estimable": True, "f1": 0.6},
        {"profile": "P4", "scope": "test", "source": "ptbxl",
         "model": "weighted_bce_seed_1", "endpoint": "LVH", "estimable": False, "f1": None},
    ]

    summaries = pipeline._summary_rows(rows)
    candidate = next(item for item in summaries if item["model"] == "weighted_bce_seed_1")

    assert candidate["comparison_endpoints"] == ["ASMI"]
    assert candidate["evaluable_endpoints"] == 1
    assert candidate["model_evaluable_endpoints"] == 1
    assert candidate["macro_f1"] == 0.6
    assert candidate["baseline_macro_f1"] == 0.5
    assert np.isclose(candidate["delta_macro_f1_vs_baseline"], 0.1)
    assert len({tuple(item.keys()) for item in summaries}) == 1


def test_p6_baseline_thresholds_ignore_json_key_sorting():
    classes = pipeline.RHYTHM_CLASSES_P6
    thresholds = dict(sorted({name: 0.5 for name in classes}.items()))
    logits = np.zeros((1, 8), dtype=np.float32)

    scores = pipeline._baseline_rhythm_scores(
        logits, np.asarray([0], dtype=np.int32), [{"scored": True}], "P6", thresholds
    )

    assert scores.shape == (1, 6)
    assert np.array_equal(scores, np.full((1, 6), 0.5))


def test_feature_revision_guard_allows_training_only_changes(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "_git_revision", lambda repo: "training-commit")
    monkeypatch.setattr(
        pipeline.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0)
    )

    result = pipeline._verify_feature_code_compatibility(tmp_path, "feature-commit")

    assert result == "training-commit"


def test_feature_revision_guard_rejects_extraction_pipeline_changes(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "_git_revision", lambda repo: "training-commit")
    results = iter((SimpleNamespace(returncode=0), SimpleNamespace(returncode=1)))
    monkeypatch.setattr(pipeline.subprocess, "run", lambda *args, **kwargs: next(results))

    with pytest.raises(ValueError, match="feature extraction code or inputs changed"):
        pipeline._verify_feature_code_compatibility(tmp_path, "feature-commit")
