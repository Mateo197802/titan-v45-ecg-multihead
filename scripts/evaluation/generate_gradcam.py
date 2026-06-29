from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one-dimensional Grad-CAM from a TorchScript model.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--signal", type=Path, required=True, help="NPY shaped [1, 12, time].")
    parser.add_argument("--target-index", type=int, required=True)
    parser.add_argument("--target-layer", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    import numpy as np
    import torch

    from titan_v45.explainability.gradcam import gradcam_1d

    model = torch.jit.load(str(args.model), map_location="cpu")
    signal = torch.from_numpy(np.load(args.signal)).float()
    result = gradcam_1d(
        model, signal, target_index=args.target_index, target_layer=args.target_layer
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        time_attribution=result.time_attribution,
        lead_attribution=result.lead_attribution,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
