from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a non-destructive CEDIA cleanup manifest.")
    parser.add_argument("--legacy-root", type=Path, required=True)
    parser.add_argument("--keep-list", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.legacy_root.resolve()
    keep = {
        (root / line.strip()).resolve()
        for line in args.keep_list.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    candidates = []
    for child in sorted(root.iterdir()):
        resolved = child.resolve()
        if resolved in keep:
            continue
        size = child.stat().st_size if child.is_file() else sum(
            file.stat().st_size for file in child.rglob("*") if file.is_file()
        )
        candidates.append({"path": str(resolved), "bytes": int(size)})
    payload = {"legacy_root": str(root), "candidates": candidates}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["confirmation_sha256"] = hashlib.sha256(canonical).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
