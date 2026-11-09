"""Independently verify the private aggregate-only SPH PAC-head receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from titan_v45.benchmarkmax.pac import validate_pac_aggregate

ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_report(
    report_path: Path,
    config_path: Path,
    protocol_path: Path,
    artifact_path: Path,
) -> dict[str, object]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    validate_pac_aggregate(report)

    config_sha = sha256_file(config_path)
    protocol_sha = sha256_file(protocol_path)
    protocol = report.get("protocol")
    if not isinstance(protocol, dict):
        raise ValueError("protocol provenance is missing from the aggregate")
    if protocol.get("config_sha256") != config_sha:
        raise ValueError("protocol configuration hash does not match the frozen file")
    if protocol.get("protocol_sha256") != protocol_sha:
        raise ValueError("protocol document hash does not match the frozen file")
    expected_code_hashes = {
        "runner_sha256": sha256_file(ROOT / "scripts/benchmarkmax/run_sph_pac_head_comparison.py"),
        "verifier_sha256": sha256_file(Path(__file__).resolve()),
        "slurm_wrapper_sha256": sha256_file(ROOT / "scripts/cedia/run_sph_pac_head_comparison.sbatch"),
    }
    if any(protocol.get(key) != digest for key, digest in expected_code_hashes.items()):
        raise ValueError("executed PAC code hashes differ from the current verified files")
    if not isinstance(protocol.get("git_commit"), str) or not re.fullmatch(
        r"[0-9a-f]{40}", protocol["git_commit"]
    ):
        raise ValueError("execution commit is malformed")
    if report.get("inputs") != config.get("input_sha256"):
        raise ValueError("report input checksums differ from the frozen configuration")
    baseline = report.get("p8_baseline")
    expected_baseline = config.get("p8_baseline")
    baseline_fields = ("job_id", "ledger_sha256", "receipt_sha256", "checkpoint_sha256", "threshold")
    if (not isinstance(baseline, dict) or not isinstance(expected_baseline, dict)
            or any(baseline.get(key) != expected_baseline.get(key) for key in baseline_fields)):
        raise ValueError("frozen V4.5 P8 baseline linkage differs from the committed configuration")
    if report.get("runtime_archives_sha256") != config.get("runtime_archives_sha256"):
        raise ValueError("runtime dependency archive hashes differ from the frozen configuration")
    runtime = report.get("runtime")
    expected_runtime = config.get("runtime")
    if not isinstance(runtime, dict) or not isinstance(expected_runtime, dict):
        raise ValueError("runtime provenance is missing")
    for key in ("python", "numpy", "scipy", "torch", "cuda", "h5py"):
        if runtime.get(key) != expected_runtime.get(key):
            raise ValueError(f"runtime {key} differs from the frozen protocol")
    execution = report.get("execution")
    if not isinstance(execution, dict) or execution.get("device_name") != expected_runtime.get("device"):
        raise ValueError("runtime device differs from the frozen protocol")
    bootstrap = report["paired_patient_cluster_bootstrap"]
    expected_bootstrap = config["metrics"]["confidence_intervals"]
    for key, config_key in (("replicates", "replicates"), ("seed", "seed")):
        if bootstrap.get(key) != expected_bootstrap[config_key]:
            raise ValueError(f"bootstrap {key} differs from the frozen protocol")
    if bootstrap.get("method") != expected_bootstrap["method"]:
        raise ValueError("bootstrap method differs from the frozen protocol")
    artifact = report.get("private_model_artifact")
    if not isinstance(artifact, dict) or not re.fullmatch(
        r"[0-9a-f]{64}", str(artifact.get("sha256", ""))
    ):
        raise ValueError("private model artifact checksum is missing or malformed")
    if artifact.get("filename") != artifact_path.name or artifact.get("sha256") != sha256_file(artifact_path):
        raise ValueError("private model artifact hash does not match the aggregate")

    return {
        "schema": report["schema"],
        "status": "aggregate_schema_hash_denominator_and_privacy_checks_passed",
        "report_sha256": sha256_file(report_path),
        "config_sha256": config_sha,
        "protocol_sha256": protocol_sha,
        **expected_code_hashes,
        "git_commit": protocol["git_commit"],
        "source_records": report["cohort"]["source_records"],
        "eligible_records": report["cohort"]["eligible_records"],
        "holdout_records": report["cohort"]["split_support"]["exploratory_holdout"]["records"],
        "private_artifact_sha256": artifact["sha256"],
        "individual_identifiers_exported": False,
        "record_level_scores_exported": False,
        "raw_signals_exported": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--model-artifact", required=True, type=Path)
    parser.add_argument(
        "--config", type=Path,
        default=ROOT / "configs/benchmarkmax/sph_pac_head_comparison.json",
    )
    parser.add_argument(
        "--protocol", type=Path,
        default=ROOT / "docs/benchmarkmax/SPH_PAC_HEAD_COMPARISON_PROTOCOL.md",
    )
    args = parser.parse_args()
    result = verify_report(
        args.report.resolve(), args.config.resolve(), args.protocol.resolve(),
        args.model_artifact.resolve(),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
