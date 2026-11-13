"""Extract paired release-backed features in a fresh private CEDIA directory."""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path

import torch
from compare_reviewer_baseline import digest
from run_reviewer_morphology_perturbation import neutralize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for n in ("protocol", "upstream", "data-root", "preflight", "assets", "output"):
        parser.add_argument(f"--{n}", type=Path, required=True)
    a = parser.parse_args()
    protocol = json.loads(a.protocol.read_bytes())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=a.upstream, text=True).strip()
    if commit != protocol["upstream_feature_commit"] or subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=a.upstream,
    ).strip():
        raise ValueError("wrong Stage A source tree")
    src = a.upstream / "scripts/specialist_experiments/extract_features.py"
    spec = importlib.util.spec_from_file_location("reviewer_morph_features", src)
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    a.output.mkdir(mode=0o700)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    original = extractor._safe_morphology
    calls = [0]
    receipts = {}
    try:
        for arm in ("with_morphology", "without_morphology"):
            if arm == "without_morphology":
                extractor._safe_morphology = lambda repo: neutralize(original(repo), calls)
            dest = a.output / arm
            meta = extractor.run(a.data_root, a.preflight, dest, a.upstream, "cuda", a.assets)
            receipts[arm] = {
                "feature_sha256": meta["feature_cache_sha256"],
                "metadata_sha256": digest(dest / "private_feature_metadata.json"),
                "asset_hashes": meta["baseline_asset_hashes"],
            }
    finally:
        extractor._safe_morphology = original
    if not calls[0] or receipts["with_morphology"]["asset_hashes"] != receipts["without_morphology"]["asset_hashes"]:
        raise ValueError("arms did not share original weights or intervention was not exercised")
    out = {
        "source_commit": commit, "protocol_sha256": digest(a.protocol), "upstream_extractor_sha256": digest(src),
        "zeroed_morphology_calls": calls[0], "arms": receipts, "performance_metrics_computed": False,
    }
    with (a.output / "extraction-receipt.json").open("x", encoding="utf-8") as f:
        json.dump(out, f, indent=2, allow_nan=False)
        f.write("\n")


if __name__ == "__main__":
    main()
