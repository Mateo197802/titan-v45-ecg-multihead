from __future__ import annotations

import torch


class SpecialistMLP(torch.nn.Module):
    def __init__(
        self, input_dim: int, output_dim: int, *, hidden_dim: int = 256, dropout: float = 0.25
    ) -> None:
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.LayerNorm(input_dim),
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.SiLU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(hidden_dim, hidden_dim),
            torch.nn.SiLU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.net(inputs)


class ClassWiseBinaryMLP(torch.nn.Module):
    def __init__(
        self, input_dim: int, output_dim: int, *, hidden_dim: int = 192, dropout: float = 0.25
    ) -> None:
        super().__init__()
        self.heads = torch.nn.ModuleList(
            [
                torch.nn.Sequential(
                    torch.nn.LayerNorm(input_dim),
                    torch.nn.Linear(input_dim, hidden_dim),
                    torch.nn.SiLU(),
                    torch.nn.Dropout(dropout),
                    torch.nn.Linear(hidden_dim, hidden_dim),
                    torch.nn.SiLU(),
                    torch.nn.Dropout(dropout),
                    torch.nn.Linear(hidden_dim, 1),
                )
                for _ in range(int(output_dim))
            ]
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return torch.cat([head(inputs) for head in self.heads], dim=1)


def parameter_count(model: torch.nn.Module) -> int:
    return int(sum(parameter.numel() for parameter in model.parameters()))
