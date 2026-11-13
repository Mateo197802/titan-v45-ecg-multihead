import importlib
from pathlib import Path

import pytest
import torch

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts" / "evaluation"


@pytest.fixture
def audit(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return importlib.import_module("audit_reviewer_release_head_support")


def test_declared_subsets_and_positive_support_are_separate(audit):
    checkpoint = {"primary8_classes": ["Flutter"], "reports": {"final_validation": {
        "rhythm": {"panels": {"Flutter": {"tp": 5, "fn": 3, "tn": 7, "fp": 2}}}}}}
    result = audit.validation_coverage(checkpoint, "rhythm", ["NSR", "Flutter"])
    assert result["embedded_validation_panels"]["Flutter"] == {
        "validation_positive": 8, "validation_negative": 9, "validation_observations": 17}
    assert result["no_embedded_validation_panel"] == ["NSR"]
    checkpoint["primary8_classes"].append("NSR")
    with pytest.raises(ValueError, match="panels"):
        audit.validation_coverage(checkpoint, "rhythm", ["NSR", "Flutter"])


def test_identical_final_row_does_not_hide_changed_shared_head(audit):
    f = {"state_dict": {"head_rhythm.1.weight": torch.ones((2, 2)),
                        "head_rhythm.4.weight": torch.zeros((2, 2)), "head_rhythm.4.bias": torch.zeros(2)}}
    g = {"state_dict": {k: v.clone() for k, v in f["state_dict"].items()}}
    g["state_dict"]["head_rhythm.1.weight"][0, 0] = 4
    g["state_dict"]["head_rhythm.4.weight"][1, 0] = 4
    out = audit.tensor_rows(f, g, "rhythm", ["NSR", "Flutter"])
    assert out["final_row_numeric_differences"]["NSR"]["weight_elements_different"] == 0
    assert out["final_row_numeric_differences"]["Flutter"]["weight_elements_different"] == 1
    assert out["shared_head_tensor_equal"] == {"head_rhythm.1.weight": False}
