"""Recompute revision analyses from saved evidence; no model or waveform loads."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.evaluation.revision_report import build_revision_report, write_revision_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="Checkout containing the saved evidence CSVs."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Destination for JSON, CSV and integrity hashes.",
    )
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--n-bootstrap", type=int, default=2000, help="ECG cluster replicates; 0 disables CIs."
    )
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--ece-bins", type=int, default=10)
    parser.add_argument(
        "--figures",
        action="store_true",
        help="Also write revision PNG/PDF from these metrics (requires matplotlib).",
    )
    args = parser.parse_args()
    try:
        # Guard against accidentally replacing evidence while exporting.
        output = args.output_dir.resolve()
        evidence = (args.root / "outputs/results/external_dev/evidence").resolve()
        if output == evidence or evidence in output.parents:
            raise ValueError("output directory must not be inside prediction evidence")
        report = build_revision_report(
            args.root,
            seed=args.seed,
            n_bootstrap=args.n_bootstrap,
            confidence=args.confidence,
            ece_bins=args.ece_bins,
        )
        write_revision_report(report, output, figures=args.figures)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"Revision report failed: {exc}", file=sys.stderr)
        return 1
    print(f"Saved-prediction revision report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
