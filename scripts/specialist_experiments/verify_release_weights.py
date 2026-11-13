"""Verify release asset hashes and restricted PyTorch deserialization without inference."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.models.frozen_pathology import BACKBONE as P4_BACKBONE  # noqa: E402
from titan_v45.models.frozen_pathology import SPECIALIST as P4_SPECIALIST
from titan_v45.models.frozen_pathology import verified_assets
from titan_v45.models.frozen_rhythm import BACKBONE as RHYTHM_BACKBONE  # noqa: E402
from titan_v45.models.frozen_rhythm import HEADS as RHYTHM_HEADS  # noqa: E402


def _tensor_summary(value: Any) -> tuple[int, int]:
    if isinstance(value, torch.Tensor):
        return 1, value.numel()
    if isinstance(value, dict):
        items = value.values()
    elif isinstance(value, (list, tuple)):
        items = value
    else:
        return 0, 0
    summaries = [_tensor_summary(item) for item in items]
    return sum(item[0] for item in summaries), sum(item[1] for item in summaries)


def verify(repo: Path, asset_root: Path) -> dict[str, Any]:
    repo, asset_root = repo.resolve(), asset_root.resolve()
    manifest = json.loads((repo / "release-manifest.json").read_text(encoding="utf-8"))
    names = {RHYTHM_BACKBONE, *RHYTHM_HEADS.values(), P4_BACKBONE, P4_SPECIALIST}
    assets, hashes = verified_assets(repo, asset_root, names)
    results = []
    for name in sorted(names):
        payload = torch.load(assets[name], map_location="cpu", weights_only=True)
        if not isinstance(payload, dict):
            raise ValueError(f"restricted load returned an unexpected root type: {name}")
        tensor_count, element_count = _tensor_summary(payload)
        if tensor_count == 0 or element_count == 0:
            raise ValueError(f"restricted load returned no tensor weights: {name}")
        results.append({
            "name": name,
            "bytes": assets[name].stat().st_size,
            "sha256": hashes[name],
            "tensor_count": tensor_count,
            "tensor_elements": element_count,
            "weights_only_load": True,
        })
        del payload
    return {
        "schema": "TITAN_SPECIALIST_RELEASE_WEIGHT_SMOKE_V1",
        "release_tag": manifest["tag"],
        "assets": results,
        "model_inference_performed": False,
        "performance_metrics_computed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo, asset_root, output = args.repo.resolve(), args.asset_root.resolve(), args.output.resolve()
    if output.is_relative_to(repo) or output.is_relative_to(asset_root):
        raise ValueError("smoke receipt must be outside the repository and asset cache")
    report = verify(repo, asset_root)
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output.parent, 0o700)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(output, 0o600)
    print(json.dumps({
        "schema": report["schema"],
        "release_tag": report["release_tag"],
        "asset_count": len(report["assets"]),
        "all_weights_only_loaded": all(item["weights_only_load"] for item in report["assets"]),
        "model_inference_performed": False,
        "performance_metrics_computed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
