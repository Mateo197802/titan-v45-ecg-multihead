from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.cascade.policy import CASCADE_PATHOLOGIES, CASCADE_RHYTHMS, cascade_evidence_role


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the cascade contract or run frozen P4 on ECGs.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", choices=("contract", "pathology_primary4"), default="contract")
    parser.add_argument("--release-root", type=Path)
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--private-ledger", type=Path)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    args = parser.parse_args()
    if args.profile == "pathology_primary4":
        if args.release_root is None or args.scratch is None:
            parser.error("waveform mode requires --release-root and --scratch")
        if args.private_ledger and args.private_ledger.resolve().is_relative_to(ROOT.resolve()):
            parser.error("the private ledger must be outside the repository")
        from titan_v45.cascade.run_pathology import run_pathology_release

        report, ledger = run_pathology_release(ROOT, args.release_root, args.scratch, args.device)
        if args.private_ledger:
            with args.private_ledger.open("x", encoding="utf-8", newline="\n") as handle:
                for (source, record_id), route in ledger.items():
                    handle.write(json.dumps({"source": source, "record_id": record_id, **route}) + "\n")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(report, indent=2) + "\n")
        return 0
    if args.release_root or args.scratch or args.private_ledger or args.device != "cpu":
        parser.error("waveform options require --profile pathology_primary4")
    payload = {
        "evidence_role": cascade_evidence_role(),
        "rhythm_classes": CASCADE_RHYTHMS,
        "pathology_classes": CASCADE_PATHOLOGIES,
        "primary_profile_evidence": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
