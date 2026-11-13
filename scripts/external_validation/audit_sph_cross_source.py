"""Compare source-preprocessed signals against retained release waveforms."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.data.sph_cross_source import audit_cross_source_signatures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--release-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--private-candidates", required=True, type=Path)
    args = parser.parse_args()
    if (args.source.resolve().is_relative_to(ROOT)
            or args.output.resolve().is_relative_to(ROOT)
            or args.private_candidates.resolve().is_relative_to(ROOT)):
        parser.error("SPH data, reports and candidate links must stay outside Git")
    report, candidates = audit_cross_source_signatures(
        args.source, args.release_root
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    with args.private_candidates.open("x", encoding="utf-8", newline="\n") as stream:
        for candidate in candidates:
            stream.write(json.dumps(candidate, sort_keys=True, separators=(",", ":")) + "\n")
    args.output.chmod(0o600)
    args.private_candidates.chmod(0o600)


if __name__ == "__main__":
    main()
