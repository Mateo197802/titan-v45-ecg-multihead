from __future__ import annotations

import pytest
import torch

from titan_v45.models.checkpoints import (
    CheckpointContractError,
    infer_classwise_architecture,
    select_state_dict,
)
from titan_v45.models.specialists import ClassWiseBinaryMLP


def test_infer_classwise_architecture_from_frozen_state_dict() -> None:
    model = ClassWiseBinaryMLP(input_dim=681, output_dim=8, hidden_dim=512)
    architecture = infer_classwise_architecture(model.state_dict())
    assert architecture.input_dim == 681
    assert architecture.hidden_dim == 512
    assert architecture.output_dim == 8


def test_select_state_dict_rejects_missing_or_non_tensor_payload() -> None:
    with pytest.raises(CheckpointContractError, match="state_dict"):
        select_state_dict({}, "state_dict")
    with pytest.raises(CheckpointContractError, match="tensor mapping"):
        select_state_dict({"state_dict": {"bad": "value"}}, "state_dict")


def test_select_state_dict_accepts_tensor_mapping() -> None:
    state = {"weight": torch.zeros(2, 2)}
    assert select_state_dict({"state_dict": state}, "state_dict") is state
