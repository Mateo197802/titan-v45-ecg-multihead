"""Audit MIMIC source integrity and PAC-reference contracts without model inference."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.data.mimic_ecg_reports import (
    iter_mimic_machine_reports,
    verify_mimic_sha256_manifest,
)
from titan_v45.data.mimic_ecg_waveform import (
    prepare_mimic_waveform,
    resolve_mimic_record_base,
)
from titan_v45.evaluation.provenance import (
    read_required_sha256_environment,
    verify_implementation_sha256,
    verify_runtime_versions,
)

CONFIG_RELATIVE = "configs/external_validation/pac_v3f_embedding_probe.json"


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_tree(repo, expected_commit, expected_config_sha256):
    config_path = repo / CONFIG_RELATIVE
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True,
                            capture_output=True, text=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo, check=True,
                            capture_output=True, text=True).stdout.strip()
    if commit != expected_commit or status:
        raise ValueError("protocol checkout must be clean and match the frozen commit")
    config_hash = sha256_file(config_path)
    if config_hash != expected_config_sha256:
        raise ValueError("PAC protocol configuration SHA-256 mismatch")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    verify_implementation_sha256(repo, config.get("implementation_sha256", {}))
    return config, config_hash, commit


def _failure_reason(exc):
    message = str(exc).lower()
    if "500 hz" in message or "10-second" in message:
        return "mimic_duration_or_sample_rate_mismatch"
    if "mV units" in message:
        return "mimic_physical_unit_mismatch"
    if "canonical 12-lead" in message or "mapped" in message:
        return "mimic_lead_mapping_failure"
    if "nonfinite" in message or "finite" in message:
        return "mimic_nonfinite_signal"
    if "wfdb" in message or "header" in message or "record" in message:
        return "mimic_wfdb_read_failure"
    return "mimic_preprocessing_failure"


def _write_exclusive(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def run(args):
    import wfdb

    repo, source = args.repo.resolve(), args.source.resolve()
    output = args.output.resolve()
    if (source.is_relative_to(repo) or repo.is_relative_to(source)
            or not output.is_relative_to(repo)):
        raise ValueError("MIMIC source must stay outside Git; source-control output must be in Git")
    config, config_hash, commit = _verify_tree(
        repo, args.expected_commit, args.expected_config_sha256
    )
    dependency_hashes = read_required_sha256_environment({
        "python_deps": "TITAN_PYTHON_DEPS_SHA256",
    }, expected_hashes=config["environment"]["dependency_archive_sha256"])
    runtime_versions = verify_runtime_versions({
        "python": platform.python_version(),
        "numpy": np.__version__,
        "wfdb": wfdb.__version__,
    }, config["environment"]["versions"])
    mimic = config["mimic_iv_ecg_v1"]
    if mimic["complete_download_authorized"] is not True:
        raise PermissionError("MIMIC source audit is blocked pending CEDIA quota/storage approval")
    integrity = verify_mimic_sha256_manifest(source)

    total = 0
    patients = set()
    report_states = Counter()
    waveform_statuses = Counter()
    signal_max_abs_mv = []
    hash_counts = Counter()
    first_patient_by_hash = {}
    cross_patient_hashes = set()
    report_labels_by_hash = defaultdict(set)
    for row in iter_mimic_machine_reports(
        source / "machine_measurements.csv", source / "record_list.csv"
    ):
        total += 1
        patient = row["subject_id"]
        patients.add(patient)
        report_state = row["report_state"]
        report_states[report_state] += 1
        try:
            record_base = resolve_mimic_record_base(source, row["record_path"])
            prepared = prepare_mimic_waveform(record_base, wfdb_module=wfdb)
        except (OSError, RuntimeError, ValueError) as exc:
            waveform_statuses[_failure_reason(exc)] += 1
            continue
        waveform_statuses["eligible"] += 1
        digest = prepared["signal_sha256"]
        signal_max_abs_mv.append(prepared["max_abs_mv"])
        hash_counts[digest] += 1
        first_patient = first_patient_by_hash.setdefault(digest, patient)
        if first_patient != patient:
            cross_patient_hashes.add(digest)
        if report_state == "positive_mention":
            report_labels_by_hash[digest].add(1)
        elif report_state == "explicit_negative_mention":
            report_labels_by_hash[digest].add(0)

    if total == 0 or len(report_states) == 0:
        raise ValueError("MIMIC source audit produced no paired records")
    if total != sum(report_states.values()) or total != sum(waveform_statuses.values()):
        raise RuntimeError("MIMIC source audit denominator failed reconciliation")
    duplicate_hashes = {digest for digest, count in hash_counts.items() if count > 1}
    discordant_hashes = {
        digest for digest, labels in report_labels_by_hash.items()
        if hash_counts[digest] > 1 and len(labels) > 1
    }
    amplitudes = np.asarray(signal_max_abs_mv, dtype=np.float64)
    source_control = {
        "schema": "TITAN_V45_MIMIC_PAC_SOURCE_PREFLIGHT_V1",
        "status": "preperformance_source_audit_only",
        "protocol_commit": commit,
        "protocol_config_sha256": config_hash,
        "implementation_sha256": config.get("implementation_sha256", {}),
        "dependency_archive_sha256": dependency_hashes,
        "dataset_doi": mimic["dataset_doi"],
        "dataset_version": mimic["version"],
        "license": mimic["license"],
        "source_integrity": integrity,
        "denominators": {
            "paired_record_list_and_machine_report_rows": total,
            "unique_subjects": len(patients),
            "waveforms_with_valid_contract": int(len(amplitudes)),
            "report_state_counts": {name: int(report_states[name]) for name in (
                "positive_mention", "explicit_negative_mention", "not_mentioned",
                "ambiguous_mention", "missing_report_text",
            )},
            "waveform_status_counts": dict(sorted(
                (name, int(count)) for name, count in waveform_statuses.items()
            )),
        },
        "physical_amplitude_millivolt_per_waveform_max_abs_quantiles": {
            "p50": float(np.quantile(amplitudes, 0.50)) if len(amplitudes) else None,
            "p95": float(np.quantile(amplitudes, 0.95)) if len(amplitudes) else None,
            "p99": float(np.quantile(amplitudes, 0.99)) if len(amplitudes) else None,
            "p999": float(np.quantile(amplitudes, 0.999)) if len(amplitudes) else None,
            "records_excluded_by_amplitude_threshold": 0,
        },
        "duplicate_audit": {
            "exact_canonical_waveform_duplicate_groups": len(duplicate_hashes),
            "cross_patient_exact_duplicate_groups": len(cross_patient_hashes),
            "exact_duplicate_groups_with_conflicting_explicit_report_mentions": len(
                discordant_hashes
            ),
        },
        "preperformance_controls": {
            "waveform_inference_performed": False,
            "model_performance_metrics_computed": False,
            "machine_reports_used_as_clinical_labels": False,
            "backbone_pretraining_independence_certified": False,
        },
        "privacy": {
            "subject_or_study_identifiers_exported": False,
            "signal_hashes_exported": False,
            "waveforms_or_report_text_exported": False,
        },
        "runtime": runtime_versions,
    }
    _write_exclusive(output, source_control)
    return source_control


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    args = parser.parse_args()
    receipt = run(args)
    print(json.dumps({
        "record_count": receipt["denominators"]["paired_record_list_and_machine_report_rows"],
        "valid_waveforms": receipt["denominators"]["waveforms_with_valid_contract"],
        "source_manifest_sha256": receipt["source_integrity"]["source_manifest_sha256"],
        "output_sha256": sha256_file(args.output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
