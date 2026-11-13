"""Frozen V3F token embeddings with a feature-only, label-blind interface."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import torch

from titan_v45.models.factory import build_titan_v45_backbone


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class V3FTokenEmbeddingExtractor:
    """Extract post-transformer temporal tokens from the frozen V3F backbone."""

    def __init__(self, checkpoint_path: Path, *, expected_sha256: str, device: str):
        checkpoint_path = Path(checkpoint_path)
        actual_sha256 = sha256_file(checkpoint_path)
        if actual_sha256 != expected_sha256:
            raise ValueError("V3F checkpoint SHA-256 does not match the frozen protocol")
        self.device = torch.device(device)
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get("state_dict"), dict):
            raise ValueError("unexpected V3F checkpoint structure")
        self.model = build_titan_v45_backbone().to(self.device).eval()
        self.model.load_state_dict(checkpoint["state_dict"], strict=True)
        self.model.requires_grad_(False)
        self._tokens = None
        self._hook = self.model.transformer.register_forward_hook(self._capture_tokens)

    def _capture_tokens(self, _module, _inputs, output):
        self._tokens = output.detach()

    @torch.inference_mode()
    def extract_windows(self, samples, *, batch_size=32):
        """Return one token tensor per preprocessed window, on CPU as float32."""
        if batch_size < 1 or not samples:
            raise ValueError("at least one preprocessed window and positive batch size are required")
        collected = []
        for start in range(0, len(samples), batch_size):
            batch = samples[start:start + batch_size]
            signals = torch.as_tensor(
                np.stack([sample[0] for sample in batch]), dtype=torch.float32, device=self.device
            )
            masks = torch.as_tensor(
                np.stack([sample[1] for sample in batch]), dtype=torch.bool, device=self.device
            )
            self._tokens = None
            self.model.forward_features(signals, lead_mask=masks)
            if self._tokens is None or self._tokens.ndim != 3 or self._tokens.shape[0] != len(batch):
                raise RuntimeError("V3F transformer did not emit the expected token tensor")
            collected.append(self._tokens.to(device="cpu", dtype=torch.float32).numpy())
        return np.concatenate(collected, axis=0)

    def close(self):
        self._hook.remove()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        self.close()
