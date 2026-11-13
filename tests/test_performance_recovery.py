"""Behavioral tests for the development-only recovery safeguards."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts" / "domain_adaptation"
sys.path.insert(0, str(SCRIPTS))
try:
    from recovery_calibration import (
        bm,
        choose_cut,
        eligible_method,
        fit_map,
        grouped_folds,
        operating_frontier,
        transform,
    )
    from recovery_inputs import authorized_bank, authorized_extra
    from recovery_selection import finalists, full_decision
    from recovery_training import RecoveryNet, loss_cell
    from verify_recovery_delivery import check_counts, json_value
finally:
    sys.path.remove(str(SCRIPTS))


def test_frontier_preserves_ties_and_adjacent_float32_cuts():
    a = np.float32(.5)
    b = np.nextafter(a, np.float32(1))
    scores = np.asarray([a, b, b, np.float32(.7)], dtype=np.float32)
    labels = np.asarray([0, 1, 0, 1])
    frontier = operating_frontier(labels, scores, {"sensitivity_min": .75})
    assert len(frontier["tp"]) == len(set(scores)) + 1
    for i, threshold in enumerate(frontier["threshold"]):
        metrics = bm(labels, scores, threshold)
        assert all(metrics[k] == frontier[k][i] for k in ("tp", "tn", "fp", "fn"))
    assert choose_cut(labels, scores, {"sensitivity_min": .75, "ppv_min": .75})["feasible"] is False
    assert choose_cut(labels, scores, {"sensitivity_min": .75, "ppv_min": .60})["feasible"] is True


def test_calibration_grouping_and_low_support_isotonic_fallback():
    groups = np.repeat(["a", "b", "c", "d", "e", "f"], 10)
    fold = grouped_folds(groups)
    assert set(fold) == {0, 1, 2}
    for person in np.unique(groups):
        assert len(set(fold[groups == person])) == 1
    y = np.tile([0, 0, 0, 1, 1], 12)
    p = np.linspace(.01, .99, 60)
    assert eligible_method("isotonic", y, fold) == "platt"
    for method in ("identity", "temperature", "platt", "isotonic"):
        mapped = transform(p, fit_map(y, p, method))
        assert np.all((mapped >= 0) & (mapped <= 1))
        assert np.all(np.diff(mapped) >= 0)


def test_readers_reject_test_before_opening_paths(tmp_path):
    with pytest.raises(ValueError, match="only registered development"):
        authorized_bank(tmp_path, "test", "per_lead_zscore")
    with pytest.raises(ValueError, match="unregistered source"):
        authorized_extra(tmp_path, "mimic", "test", "per_lead_zscore")


def test_full_and_repeat_gates_use_validation_ap_not_f1():
    runs = [
        dict(mode="partial", seed=20261112, validation_macro_ap=.550, validation_guard_ap=.41),
        dict(mode="specialist", seed=20261112, validation_macro_ap=.562, validation_guard_ap=.43),
        dict(mode="cpsc", seed=20261112, validation_macro_ap=.567, validation_guard_ap=.44),
        dict(mode="mimic", seed=20261112, validation_macro_ap=.567, validation_guard_ap=.45),
        dict(mode="partial", seed=20261113, validation_macro_ap=.8, validation_guard_ap=.8),
    ]
    incumbent = {"incumbent_calibration_all_guards_feasible": True,
                 "code_validation": {"A": {"macro_raw_auprc": .55}}}
    assert full_decision(runs, incumbent)["allow_full"] is True
    assert finalists(runs) == ["specialist", "mimic"]
    incumbent["code_validation"]["A"]["macro_raw_auprc"] = .53
    assert full_decision(runs, incumbent)["allow_full"] is False


@pytest.mark.parametrize("kind", ["shared", "independent", "residual"])
def test_new_branches_start_from_incumbent_logits(kind):
    class Backbone(torch.nn.Module):
        d_model = 4

        def forward_features(self, wave):
            return wave[:, :4].mean(dim=-1)

    base = SimpleNamespace(backbone=Backbone(), head=torch.nn.Linear(13, 5))
    model = RecoveryNet(base, kind)
    wave, desc, rr = torch.randn(2, 12, 917), torch.randn(2, 7), torch.zeros(2, 4)
    duration = torch.tensor([[1., 0.], [1., 0.]])
    wanted = base.head(torch.cat((base.backbone.forward_features(wave), desc, duration), dim=1))
    assert torch.equal(model(wave, desc, rr), wanted)


def test_hard_negative_weight_only_increases_known_difficult_negatives():
    logits = torch.tensor([[0., 0., 0., 0.]])
    truth = torch.tensor([[1., 0., 0., -1.]])
    old_scores = torch.tensor([[.9, .7, .2, .9]])
    raw = loss_cell(logits, truth, torch.ones(4), "bce")
    hard = loss_cell(logits, truth, torch.ones(4), "hard_negative", old_scores)
    assert torch.equal(hard / raw, torch.tensor([[1., 1.75, 1., 1.]]))


def test_public_evidence_rejects_private_rows_and_invalid_denominators():
    with pytest.raises(ValueError, match="individual"):
        json_value({"patient_id": "restricted"})
    with pytest.raises(ValueError, match="private path"):
        json_value({"folder": "/home/account/internal"})
    with pytest.raises(ValueError, match="supports"):
        check_counts({"tp": 10, "tn": 20, "fp": 1, "fn": 2, "positive_support": 11, "negative_support": 21})
