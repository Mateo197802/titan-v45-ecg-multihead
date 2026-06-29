from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class SpecialistFeatureLayout:
    rhythm_indices: tuple[int, ...]
    specialist_rhythm_indices: tuple[int, ...]
    pathology_indices: tuple[int, ...]
    include_morphology: bool = True
    signal_event_feature_dim: int = 0


def _select_columns(values: torch.Tensor, indices: tuple[int, ...]) -> torch.Tensor:
    if not indices:
        return values.new_empty((values.shape[0], 0))
    index = torch.tensor(indices, device=values.device, dtype=torch.long)
    if int(index.min()) < 0 or int(index.max()) >= values.shape[1]:
        raise ValueError("feature layout contains an out-of-range class index")
    return values.index_select(1, index)


def compose_specialist_features(
    *,
    backbone_features: torch.Tensor,
    rhythm_probabilities: torch.Tensor,
    pathology_probabilities: torch.Tensor,
    layout: SpecialistFeatureLayout,
    morphology: torch.Tensor | None = None,
    signal_event_features: torch.Tensor | None = None,
) -> torch.Tensor:
    batch_size = backbone_features.shape[0]
    tensors = (backbone_features, rhythm_probabilities, pathology_probabilities)
    if any(tensor.ndim != 2 or tensor.shape[0] != batch_size for tensor in tensors):
        raise ValueError("all specialist feature inputs must be aligned two-dimensional tensors")
    pieces = [backbone_features.float()]
    if layout.include_morphology:
        if morphology is None or morphology.ndim != 2 or morphology.shape[0] != batch_size:
            raise ValueError("the declared specialist layout requires aligned morphology features")
        pieces.append(morphology.float())
    pieces.extend(
        [
            _select_columns(rhythm_probabilities, layout.rhythm_indices).float(),
            _select_columns(rhythm_probabilities, layout.specialist_rhythm_indices).float(),
            _select_columns(pathology_probabilities, layout.pathology_indices).float(),
        ]
    )
    if layout.signal_event_feature_dim:
        expected = (batch_size, layout.signal_event_feature_dim)
        if signal_event_features is None or signal_event_features.shape != expected:
            raise ValueError(f"signal event features must have shape {expected}")
        pieces.append(signal_event_features.float())
    result = torch.cat(pieces, dim=1)
    if not torch.isfinite(result).all():
        raise ValueError("specialist features must be finite")
    return result
