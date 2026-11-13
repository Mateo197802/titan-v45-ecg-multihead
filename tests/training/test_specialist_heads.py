import numpy as np
import pytest
import torch

from titan_v45.training.specialist_heads import (
    P4_CLASSES,
    RHYTHM_CLASSES_P8,
    fit_classwise_binary_head,
    masked_binary_cross_entropy,
    masked_binary_focal_loss,
    ptbxl_p4_targets,
    rhythm_targets,
    source_balanced_element_weights,
    split_bucket,
    stable_fraction,
)


def test_challenge_mapping_masks_unsupported_source_classes():
    target, mask = rhythm_targets(
        ["164889003", "59118001"], RHYTHM_CLASSES_P8,
        supported_classes={"AFIB", "RBBB"},
    )
    assert target.tolist() == [1, 0, 0, 0, 1, 0, 0, 0]
    assert mask.tolist() == [True, False, False, False, True, False, False, False]


def test_ptbxl_zero_likelihood_is_unknown_and_not_a_positive_or_control():
    target, mask = ptbxl_p4_targets({"ASMI": 0, "NORM": 1})
    assert target.tolist() == [0, 0, 0, 0]
    assert not mask.any()


def test_ptbxl_only_explicit_target_or_clean_norm_controls_are_observed():
    positive, positive_mask = ptbxl_p4_targets({"ASMI": 100, "LVH": 0})
    control, control_mask = ptbxl_p4_targets({"NORM": 100})
    assert positive.tolist() == [1, 0, 0, 0]
    assert positive_mask.tolist() == [True, False, False, False]
    assert control.tolist() == [0, 0, 0, 0]
    assert control_mask.tolist() == [True, True, True, True]


def test_stable_split_is_deterministic_and_partitioned():
    args = {"seed": 20261111, "namespace": "study-v1", "train_fraction": 0.8,
            "validation_fraction": 0.1}
    key = "private-record-key"
    assert stable_fraction(key, seed=args["seed"], namespace=args["namespace"]) == stable_fraction(
        key, seed=args["seed"], namespace=args["namespace"]
    )
    assert split_bucket(key, **args) in {"train", "validation", "calibration"}


def test_source_balancing_equalizes_each_active_source_per_class():
    mask = torch.tensor([[1, 1], [1, 0], [1, 1], [1, 1]], dtype=torch.bool)
    weights = source_balanced_element_weights(["A", "A", "B", "B"], mask)
    assert float(weights[:2, 0].sum()) == pytest.approx(0.5)
    assert float(weights[2:, 0].sum()) == pytest.approx(0.5)
    assert float(weights[:2, 1].sum()) == pytest.approx(0.5)
    assert float(weights[2:, 1].sum()) == pytest.approx(0.5)


def test_masked_bce_ignores_unobserved_target_values():
    logits = torch.tensor([[0.0, 0.0]])
    mask = torch.tensor([[True, False]])
    first = masked_binary_cross_entropy(logits, torch.tensor([[1.0, 0.0]]), mask)
    second = masked_binary_cross_entropy(logits, torch.tensor([[1.0, 1.0]]), mask)
    assert float(first) == pytest.approx(float(second))


def test_masked_bce_rejects_all_unknown_targets():
    with pytest.raises(ValueError, match="no observed"):
        masked_binary_cross_entropy(torch.zeros((1, len(P4_CLASSES))),
                                    torch.zeros((1, len(P4_CLASSES))),
                                    torch.zeros((1, len(P4_CLASSES)), dtype=torch.bool))


@pytest.mark.parametrize("loss_name", ["weighted_bce", "source_balanced_bce", "focal"])
def test_head_training_uses_record_aggregated_validation(loss_name):
    rng = np.random.default_rng(4)
    train_x = rng.normal(size=(16, 5)).astype(np.float32)
    train_y = np.asarray([[i % 2, (i // 2) % 2] for i in range(16)], dtype=np.float32)
    train_mask = np.ones_like(train_y, dtype=bool)
    train_weights = np.ones_like(train_y)
    val_x = rng.normal(size=(8, 5)).astype(np.float32)
    val_y = np.asarray([[0, 0], [0, 0], [1, 1], [1, 1]] * 2, dtype=np.float32)
    val_mask = np.ones_like(val_y, dtype=bool)
    groups = ["a", "a", "b", "b", "c", "c", "d", "d"]

    model, receipt = fit_classwise_binary_head(
        train_x, train_y, train_mask, train_weights, val_x, val_y, val_mask,
        loss_name=loss_name, validation_group_ids=groups,
        validation_aggregation="mean_probabilities", max_epochs=2, patience=2, device="cpu",
    )
    assert model(torch.from_numpy(val_x)).shape == (8, 2)
    assert receipt["loss_name"] == loss_name
    assert receipt["best_epoch"] in (1, 2)


def test_focal_loss_ignores_masked_targets():
    logits = torch.zeros((1, 2))
    mask = torch.tensor([[True, False]])
    alpha = torch.tensor([0.5, 0.5])
    first = masked_binary_focal_loss(logits, torch.tensor([[1.0, 0.0]]), mask,
                                     alpha_positive=alpha)
    second = masked_binary_focal_loss(logits, torch.tensor([[1.0, 1.0]]), mask,
                                      alpha_positive=alpha)
    assert float(first) == pytest.approx(float(second))
