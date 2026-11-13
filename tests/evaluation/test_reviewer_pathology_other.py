import csv
import importlib
import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts" / "evaluation"


@pytest.fixture
def other(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    yield importlib.import_module("reviewer_pathology_other")
    sys.modules.pop("reviewer_pathology_other", None)


def test_source_statements_and_non_controls(other):
    targets = {"ALMI", "LAO/LAE"}
    assert other.reference({"ALMI": 35, "ILMI": 100}, targets) == "positive"
    assert other.reference({"LAO/LAE": 0}, targets) == "ambiguous"
    assert other.reference({"NORM": 100, "ALMI": 10}, targets) == "ambiguous"
    assert other.reference({"NORM": 100, "SR": 0}, targets) == "control"
    assert other.reference({"SR": 100}, targets) == "unknown"
    assert other.reference({"NORM": 100, "IMI": 0}, targets) == "unknown"
    assert other.reference({"ILMI": 100}, targets) == "unknown"
    assert other.reference({"LAE": 100}, targets) == "unknown"


def test_fold_10_outcomes_not_parsed_and_cross_fold_patient_rejected(other, tmp_path):
    file = tmp_path / "metadata.csv"
    rows = [[1, "r/a", "4.0", "{'NORM': 100}"], [10, "", "", "must not parse"]]

    def write():
        with file.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("strat_fold", "filename_lr", "patient_id", "scp_codes"))
            writer.writerows(rows)

    write()
    refs, groups, reserved = other.read_references(file, 2)
    assert refs == {other.identity("ptbxl", "r/a"): {"NORM": 100}}
    assert list(groups.values()) == [(1, other.identity("ptbxl_patient", "4"))]
    assert reserved == 1
    rows.append([9, "r/b", "4", "{'ALMI': 100}"])
    write()
    with pytest.raises(ValueError, match="across official folds"):
        other.read_references(file, 3)


def test_calibration_ignores_held_and_evaluation_keeps_unknown_flow(other):
    keys = tuple("abcdefgh")
    x = np.array([[-2], [2], [-1], [1], [-3], [3], [-4], [4]], dtype=float)
    splits = dict(zip(keys, (("train", True), ("train", True),
                            ("calibration", True), ("calibration", True),
                            *(("held", True),) * 4), strict=True))
    refs = dict(zip(keys, ("control", "positive") * 3 + ("unknown", "ambiguous"), strict=True))
    recipe = {"minimum_training_per_polarity": 1, "minimum_calibration_per_polarity": 1,
              "minimum_held_per_polarity": 1, "l2": 0.01, "max_iterations": 250}
    model = other.endpoint_fit(x, keys, splits, {k: refs[k] for k in keys[:4]}, recipe)
    assert model["status"] == "calibrated"
    refs["outside"] = "positive"

    def metric(y, scores, threshold):
        assert y.tolist() == [0, 1]
        return {"correct": int(np.sum(y == (scores >= threshold)))}

    report = other.endpoint_evaluate(
        x, keys, {k: (9, k) for k in keys}, splits, refs, model,
        {"training": recipe, "statistics": {"seed": 3, "replicates": 1, "confidence": 0.95}},
        metric, lambda *args, **kwargs: {},
    )
    assert report["known_statement_subset_metrics"] == {"correct": 2}
    assert report["held_calls_by_reference_state"]["unknown:negative"] == 1
    assert report["all_source_reference_and_scoring_flow"]["outside_active_inventory"]["positive:not_scored"] == 1
