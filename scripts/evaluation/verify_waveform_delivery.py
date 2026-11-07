"""Verify aggregate receipts and exact tracked checkout bytes without private data."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "outputs/results/revision_20261107"


def verify():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT)

    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("delivery checkout is not clean")
    revision = git("rev-parse", "HEAD").decode().strip()
    files = {}
    with tarfile.open(fileobj=io.BytesIO(git("archive", revision)), mode="r:") as archive:
        for member in archive:
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError("unexpected tracked non-regular file")
            path = ROOT / member.name
            if not path.resolve().is_relative_to(ROOT) or path.is_symlink():
                raise ValueError("tracked file escapes checkout or is a symlink")
            expected = archive.extractfile(member).read()
            if path.read_bytes() != expected:
                raise ValueError(f"tracked byte mismatch: {member.name}")
            files[member.name] = hashlib.sha256(expected).hexdigest()
    outputs = json.loads((EVIDENCE / "execution.json").read_bytes())["outputs"]
    for name, entry in outputs.items():
        path = (EVIDENCE / name).relative_to(ROOT).as_posix()
        if files.get(path) != entry["sha256"] or (entry["state"], entry["exit_code"]) != (
            "COMPLETED", "0:0"
        ):
            raise ValueError(f"aggregate does not match its native receipt: {name}")
    return {
        "git_revision": revision,
        "git_tree": git("rev-parse", "HEAD^{tree}").decode().strip(),
        "tracked_files_exact_byte_matches": len(files),
        "tracked_inventory_sha256": hashlib.sha256(
            json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "native_aggregate_sha256": {name: item["sha256"] for name, item in outputs.items()},
        "physical_asset_verification": "separate_check",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(verify(), indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(result)
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
