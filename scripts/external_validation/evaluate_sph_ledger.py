"""Join a sealed label-blind SPH scoring ledger to statement references."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.evaluation.sph_report import evaluate_sph_ledger


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(args):
    import numpy as np

    repo = args.repo.resolve()
    output, receipt_output = args.output.resolve(), args.receipt_output.resolve()
    if output.is_relative_to(repo) or receipt_output.is_relative_to(repo):
        raise ValueError("report files must be staged outside the Git checkout")
    protocol_path = repo / "configs/external_validation/sph_frozen.json"
    protocol_sha256 = _sha256(protocol_path)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if commit != args.expected_commit or status:
        raise ValueError("evaluation source tree is not the clean frozen protocol commit")
    scoring_receipt = json.loads(args.scoring_receipt.read_text(encoding="utf-8"))
    if (scoring_receipt["protocol_commit"] != commit
            or scoring_receipt["protocol_sha256"] != protocol_sha256
            or scoring_receipt["source_sha256"] != json.loads(
                protocol_path.read_text(encoding="utf-8")
            )["source_sha256"]):
        raise ValueError("scoring receipt does not match frozen protocol inputs")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    dependencies = {
        "python_deps_archive_sha256": _sha256(args.python_deps_archive),
    }
    if dependencies["python_deps_archive_sha256"] != protocol["environment"][
        "python_deps_archive_sha256"
    ]:
        raise ValueError("aggregation dependency archive differs from the frozen protocol")
    if (platform.python_version() != protocol["environment"]["versions"]["python"]
            or np.__version__ != protocol["environment"]["versions"]["numpy"]):
        raise ValueError("aggregation runtime version differs from the frozen protocol")
    implementation_hashes = {
        relative_path: _sha256(repo / relative_path)
        for relative_path in protocol["implementation_sha256"]
    }
    if implementation_hashes != protocol["implementation_sha256"]:
        raise ValueError("frozen evaluation implementation digest mismatch")
    started = time.monotonic()
    report = evaluate_sph_ledger(
        source=args.source,
        ledger=args.ledger,
        scoring_receipt=args.scoring_receipt,
        duplicate_index=args.duplicate_index,
        protocol=protocol,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt_output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    execution = {
        "schema": "TITAN_V45_SPH_AGGREGATION_RECEIPT_V1",
        "job_id": os.environ.get("SLURM_JOB_ID", "not_slurm"),
        "commit": commit,
        "protocol_sha256": protocol_sha256,
        "implementation_sha256": implementation_hashes,
        "dependency_archive_sha256": dependencies,
        "inputs": {
            "scoring_receipt_sha256": _sha256(args.scoring_receipt),
            "ledger_sha256": _sha256(args.ledger),
            "private_duplicate_index_sha256": _sha256(args.duplicate_index),
            "metadata_sha256": _sha256(args.source / "metadata.csv"),
            "code_dictionary_sha256": _sha256(args.source / "code.csv"),
        },
        "aggregate_sha256": _sha256(output),
        "environment": {"python": platform.python_version(), "numpy": np.__version__},
        "runtime_seconds": time.monotonic() - started,
        "record_or_patient_identifiers_exported": False,
    }
    with receipt_output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(execution, stream, indent=2, allow_nan=False)
        stream.write("\n")
    os.chmod(output, 0o600)
    os.chmod(receipt_output, 0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--scoring-receipt", type=Path, required=True)
    parser.add_argument("--duplicate-index", type=Path, required=True)
    parser.add_argument("--python-deps-archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
