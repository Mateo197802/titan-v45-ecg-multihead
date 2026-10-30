"""TITAN V4.5 clean 12-lead ResNet-1D + SE + Transformer backbone."""

from __future__ import annotations

from collections.abc import Mapping

import torch
import torch.nn as nn


class SqueezeExcitation1D(nn.Module):
    def __init__(self, channels: int, reduction: int = 16) -> None:
        super().__init__()
        hidden = max(channels // reduction, 8)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.gate = nn.Sequential(
            nn.Conv1d(channels, hidden, kernel_size=1),
            nn.SiLU(),
            nn.Conv1d(hidden, channels, kernel_size=1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x * self.gate(self.pool(x))


class ResidualSEBlock1D(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, *, stride: int, dropout: float) -> None:
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size=7, stride=stride, padding=3, bias=False)
        self.norm1 = nn.BatchNorm1d(out_channels)
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size=7, padding=3, bias=False)
        self.norm2 = nn.BatchNorm1d(out_channels)
        self.se = SqueezeExcitation1D(out_channels)
        self.dropout = nn.Dropout(dropout)
        self.skip = (
            nn.Identity()
            if stride == 1 and in_channels == out_channels
            else nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm1d(out_channels),
            )
        )
        self.activation = nn.SiLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.skip(x)
        x = self.activation(self.norm1(self.conv1(x)))
        x = self.dropout(x)
        x = self.se(self.norm2(self.conv2(x)))
        return self.activation(x + residual)


class SinusoidalPositionEncoding(nn.Module):
    def __init__(self, d_model: int, max_length: int = 256) -> None:
        super().__init__()
        position = torch.arange(max_length, dtype=torch.float32).unsqueeze(1)
        scale = torch.exp(torch.arange(0, d_model, 2, dtype=torch.float32) * (-torch.log(torch.tensor(10000.0)) / d_model))
        encoding = torch.zeros(max_length, d_model, dtype=torch.float32)
        encoding[:, 0::2] = torch.sin(position * scale)
        encoding[:, 1::2] = torch.cos(position * scale)
        self.register_buffer("encoding", encoding.unsqueeze(0), persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.shape[1] > self.encoding.shape[1]:
            raise ValueError(f"sequence length {x.shape[1]} exceeds positional capacity {self.encoding.shape[1]}")
        return x + self.encoding[:, : x.shape[1]].to(dtype=x.dtype)


class TitanV4Hybrid(nn.Module):
    """Large controlled ECG backbone with explicit 12-lead availability input."""

    def __init__(
        self,
        in_channels: int = 12,
        num_rhythm: int = 14,
        num_pathology: int = 7,
        morphology_dim: int = 0,
        d_model: int = 640,
        num_transformer_layers: int = 9,
        nhead: int = 10,
        stage_channels: tuple[int, int, int, int] = (96, 192, 384, 768),
        dropout: float = 0.15,
        clinical_axis_heads: Mapping[str, int] | None = None,
    ) -> None:
        super().__init__()
        if in_channels != 12:
            raise ValueError("TITAN V4.5 requires the canonical 12-lead input tensor")
        if len(stage_channels) != 4:
            raise ValueError("stage_channels must define four ResNet stages")
        if d_model % nhead:
            raise ValueError("d_model must be divisible by nhead")

        self.in_channels = in_channels
        self.morphology_dim = int(morphology_dim)
        self.d_model = int(d_model)
        self.last_conv_activations: torch.Tensor | None = None
        self.last_conv_gradients: torch.Tensor | None = None

        stem_channels, stage2, stage3, stage4 = stage_channels
        self.stem = nn.Sequential(
            nn.Conv1d(in_channels, stem_channels, kernel_size=15, stride=2, padding=7, bias=False),
            nn.BatchNorm1d(stem_channels),
            nn.SiLU(),
        )
        self.res_layers = nn.Sequential(
            ResidualSEBlock1D(stem_channels, stem_channels, stride=1, dropout=dropout),
            ResidualSEBlock1D(stem_channels, stage2, stride=2, dropout=dropout),
            ResidualSEBlock1D(stage2, stage2, stride=1, dropout=dropout),
            ResidualSEBlock1D(stage2, stage3, stride=2, dropout=dropout),
            ResidualSEBlock1D(stage3, stage3, stride=1, dropout=dropout),
            ResidualSEBlock1D(stage3, stage4, stride=2, dropout=dropout),
        )
        self.token_projection = nn.Conv1d(stage4, d_model, kernel_size=1, bias=False)
        self.position = SinusoidalPositionEncoding(d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=False,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_transformer_layers)
        self.final_norm = nn.LayerNorm(d_model)
        self.lead_mask_projection = nn.Sequential(nn.Linear(in_channels, d_model), nn.SiLU(), nn.Linear(d_model, d_model))

        rhythm_input_dim = d_model + self.morphology_dim
        self.head_rhythm = nn.Sequential(nn.LayerNorm(rhythm_input_dim), nn.Linear(rhythm_input_dim, 512), nn.SiLU(), nn.Dropout(0.30), nn.Linear(512, num_rhythm))
        self.head_quality = nn.Sequential(nn.Linear(d_model, 128), nn.SiLU(), nn.Dropout(dropout), nn.Linear(128, 1), nn.Sigmoid())
        self.head_biometrics = nn.Sequential(nn.Linear(d_model, 256), nn.SiLU(), nn.Dropout(dropout), nn.Linear(256, 3))
        self.num_pathology = int(num_pathology)
        self.head_pathology = nn.Sequential(nn.LayerNorm(d_model), nn.Linear(d_model, 512), nn.SiLU(), nn.Dropout(0.30), nn.Linear(512, self.num_pathology))
        self.clinical_axis_head_dims = dict(clinical_axis_heads or {})
        self.head_clinical_axes = nn.ModuleDict(
            {
                axis: nn.Sequential(
                    nn.LayerNorm(d_model),
                    nn.Linear(d_model, 256),
                    nn.SiLU(),
                    nn.Dropout(0.25),
                    nn.Linear(256, int(dim)),
                )
                for axis, dim in self.clinical_axis_head_dims.items()
            }
        )

    def _capture_gradients(self, gradients: torch.Tensor) -> None:
        self.last_conv_gradients = gradients.detach()

    def forward_features(self, x: torch.Tensor, lead_mask: torch.Tensor | None = None) -> torch.Tensor:
        if x.ndim != 3 or x.shape[1] != self.in_channels:
            raise ValueError(f"expected [batch, {self.in_channels}, time], got {tuple(x.shape)}")
        if lead_mask is None:
            lead_mask = torch.ones((x.shape[0], self.in_channels), dtype=torch.bool, device=x.device)
        if lead_mask.shape != (x.shape[0], self.in_channels):
            raise ValueError(f"lead_mask must have shape {(x.shape[0], self.in_channels)}, got {tuple(lead_mask.shape)}")
        mask = lead_mask.to(device=x.device, dtype=x.dtype)
        x = x * mask.unsqueeze(-1)
        x = self.stem(x)
        x = self.res_layers(x)
        x = self.token_projection(x)
        self.last_conv_activations = x
        self.last_conv_gradients = None
        if x.requires_grad:
            x.register_hook(self._capture_gradients)
        x = self.position(x.transpose(1, 2))
        x = self.transformer(x)
        features = self.final_norm(x.mean(dim=1) + self.lead_mask_projection(mask))
        return features

    def forward(
        self,
        x: torch.Tensor,
        morphology_features: torch.Tensor | None = None,
        return_features: bool = False,
        lead_mask: torch.Tensor | None = None,
    ):
        features = self.forward_features(x, lead_mask=lead_mask)
        rhythm_features = features
        if self.morphology_dim:
            if morphology_features is None:
                raise ValueError("morphology_features is required when morphology_dim > 0")
            morphology_features = torch.nan_to_num(morphology_features.to(features), nan=0.0, posinf=0.0, neginf=0.0)
            rhythm_features = torch.cat([features, morphology_features], dim=1)
        outputs = (
            self.head_rhythm(rhythm_features),
            self.head_quality(features),
            self.head_biometrics(features),
            self.head_pathology(features),
        )
        return (*outputs, features) if return_features else outputs

    def clinical_axis_logits(self, features: torch.Tensor) -> dict[str, torch.Tensor]:
        return {axis: head(features) for axis, head in self.head_clinical_axes.items()}

    def enable_mc_dropout(self) -> None:
        """Activate dropout layers while preserving evaluation statistics elsewhere."""
        for module in self.modules():
            if isinstance(module, nn.Dropout):
                module.train()
