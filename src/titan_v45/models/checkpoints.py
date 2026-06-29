from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import torch


class CheckpointContractError(RuntimeError):
    """Raised when a checkpoint does not follow a frozen TITAN contract."""


@dataclass(frozen=True)
class ClassWiseArchitecture:
    input_dim: int
    hidden_dim: int
    output_dim: int


def select_state_dict(
    checkpoint: Mapping[str, object], key: str
) -> Mapping[str, torch.Tensor]:
    candidate = checkpoint.get(key)
    if not isinstance(candidate, Mapping):
        raise CheckpointContractError(f"checkpoint is missing {key} state_dict")
    if not candidate or not all(torch.is_tensor(value) for value in candidate.values()):
        raise CheckpointContractError(f"{key} must be a non-empty tensor mapping")
    return candidate


def infer_classwise_architecture(
    state_dict: Mapping[str, torch.Tensor],
) -> ClassWiseArchitecture:
    try:
        input_dim = int(state_dict["heads.0.0.weight"].numel())
        hidden_dim = int(state_dict["heads.0.1.weight"].shape[0])
    except (KeyError, IndexError) as error:
        raise CheckpointContractError("state_dict is not a classwise specialist") from error
    indices: set[int] = set()
    for key in state_dict:
        if not key.startswith("heads."):
            continue
        parts = key.split(".")
        if len(parts) > 1 and parts[1].isdigit():
            indices.add(int(parts[1]))
    if not indices or indices != set(range(max(indices) + 1)):
        raise CheckpointContractError("specialist head indices are not contiguous")
    return ClassWiseArchitecture(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        output_dim=len(indices),
    )
