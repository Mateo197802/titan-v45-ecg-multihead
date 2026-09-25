from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.evaluation.release_evidence import verify_release_evidence


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recompute published release metrics from tracked record-level evidence."
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository checkout to verify.")
    parser.add_argument("--output", type=Path, help="Write the JSON verification report here.")
    args = parser.parse_args()

    try:
        report = verify_release_evidence(args.root)
    except (KeyError, OSError, ValueError) as exc:
        print(f"Release evidence verification failed: {exc}", file=sys.stderr)
        return 1

    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
        print(f"Verified release evidence; report written to {args.output}")
    else:
        sys.stdout.write(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
