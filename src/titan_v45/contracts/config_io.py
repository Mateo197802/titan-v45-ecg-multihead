from __future__ import annotations

import json
from pathlib import Path

from titan_v45.contracts.profiles import ModelProfile


def load_profile_config(path: str | Path) -> ModelProfile:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in (
        "classes",
        "thresholds",
        "artifact_classes",
        "backbone_rhythm_classes",
        "backbone_pathology_classes",
    ):
        payload[key] = tuple(payload.get(key, ()))
    return ModelProfile(**payload)
