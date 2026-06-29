from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.cascade.policy import CASCADE_PATHOLOGIES, CASCADE_RHYTHMS, cascade_evidence_role


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the secondary TITAN cascade evidence contract.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = {
        "evidence_role": cascade_evidence_role(),
        "rhythm_classes": CASCADE_RHYTHMS,
        "pathology_classes": CASCADE_PATHOLOGIES,
        "eligible_for_primary_gate": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
