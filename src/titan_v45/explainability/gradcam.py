from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import torch.nn.functional as functional


@dataclass(frozen=True)
class GradCamResult:
    time_attribution: np.ndarray
    lead_attribution: np.ndarray


def _resolve_module(model: torch.nn.Module, path: str) -> torch.nn.Module:
    module: torch.nn.Module = model
    for part in path.split("."):
        module = getattr(module, part)
    return module


def gradcam_1d(
    model: torch.nn.Module,
    signal: torch.Tensor,
    *,
    target_index: int,
    target_layer: str,
) -> GradCamResult:
    layer = _resolve_module(model, target_layer)
    activations: list[torch.Tensor] = []
    gradients: list[torch.Tensor] = []

    def capture_activation(_module, _inputs, output):
        activations.append(output)

    def capture_gradient(_module, _grad_input, grad_output):
        gradients.append(grad_output[0])

    forward_handle = layer.register_forward_hook(capture_activation)
    backward_handle = layer.register_full_backward_hook(capture_gradient)
    was_training = model.training
    model.eval()
    model.zero_grad(set_to_none=True)
    prepared = signal.detach().clone().requires_grad_(True)
    try:
        logits = model(prepared)
        logits[:, int(target_index)].sum().backward()
        if not activations or not gradients or prepared.grad is None:
            raise RuntimeError("Grad-CAM hooks did not capture activations and gradients")
        weights = gradients[-1].mean(dim=-1, keepdim=True)
        cam = torch.relu((weights * activations[-1]).sum(dim=1, keepdim=True))
        cam = functional.interpolate(cam, size=prepared.shape[-1], mode="linear", align_corners=False)
        time_map = cam[0, 0]
        maximum = time_map.max()
        if maximum > 0:
            time_map = time_map / maximum
        lead_map = prepared.grad[0].abs().mean(dim=-1)
        lead_total = lead_map.sum()
        if lead_total > 0:
            lead_map = lead_map / lead_total
        return GradCamResult(
            time_attribution=time_map.detach().cpu().numpy(),
            lead_attribution=lead_map.detach().cpu().numpy(),
        )
    finally:
        forward_handle.remove()
        backward_handle.remove()
        model.train(was_training)
