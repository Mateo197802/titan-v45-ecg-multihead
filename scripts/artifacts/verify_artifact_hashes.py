from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.artifacts.manifest import verify_artifact_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify files listed in a release manifest.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    verify_artifact_manifest(args.root, payload["artifacts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
