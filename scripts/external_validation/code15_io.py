"""Dependency-free paths and hashing for CODE-15% custody checks."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/external_validation_20261111/FROZEN_CODE15_PROTOCOL.json"


def digest(path):
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()
