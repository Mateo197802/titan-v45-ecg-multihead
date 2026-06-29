from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.artifacts.publication_audit import audit_public_tree


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a repository for private publication residue.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    findings = [finding.__dict__ for finding in audit_public_tree(args.root)]
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"findings": findings}, indent=2) + "\n", encoding="utf-8")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
