from __future__ import annotations

import torch

from titan_v45.models.backbone import TitanV4Hybrid

ECG_AXIS_HEAD_DIMS = {
    "rate_frequency": 3,
    "supraventricular_irregular": 2,
    "ectopy": 2,
    "conduction": 6,
    "repolarization_qt": 1,
}


def build_titan_v45_backbone(*, morphology_dim: int = 10) -> TitanV4Hybrid:
    return TitanV4Hybrid(
        in_channels=12,
        num_rhythm=14,
        num_pathology=7,
        morphology_dim=int(morphology_dim),
        d_model=640,
        num_transformer_layers=9,
        nhead=10,
        stage_channels=(96, 192, 384, 768),
        ecg_axis_heads=ECG_AXIS_HEAD_DIMS,
    )


def parameter_count(model: torch.nn.Module) -> int:
    return int(sum(parameter.numel() for parameter in model.parameters()))
