import hashlib

import numpy as np
import torch
from torch import nn

import titan_v45.models.v3f_embeddings as v3f_embeddings


class TinyTokenBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        self.projection = nn.Linear(12, 640, bias=False)
        self.transformer = nn.Identity()

    def forward_features(self, signals, lead_mask=None):
        tokens = self.projection(signals.transpose(1, 2)[:, ::100, :])
        if lead_mask is not None:
            tokens = tokens * lead_mask.any(dim=1, keepdim=True).unsqueeze(-1)
        return self.transformer(tokens).mean(dim=1)


def test_v3f_extractor_captures_transformer_tokens_with_frozen_checkpoint(tmp_path, monkeypatch):
    template = TinyTokenBackbone()
    checkpoint = tmp_path / "checkpoint.pt"
    torch.save({"state_dict": template.state_dict()}, checkpoint)
    expected_sha256 = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    monkeypatch.setattr(v3f_embeddings, "build_titan_v45_backbone", TinyTokenBackbone)
    samples = [
        (np.ones((12, 1250), dtype=np.float32), np.ones(12, dtype=bool), np.zeros(10)),
        (np.zeros((12, 1250), dtype=np.float32), np.ones(12, dtype=bool), np.zeros(10)),
    ]

    with v3f_embeddings.V3FTokenEmbeddingExtractor(
        checkpoint, expected_sha256=expected_sha256, device="cpu"
    ) as extractor:
        tokens = extractor.extract_windows(samples, batch_size=1)
        assert not extractor.model.training
        assert all(not parameter.requires_grad for parameter in extractor.model.parameters())

    assert tokens.shape == (2, 13, 640)
    assert np.isfinite(tokens).all()
