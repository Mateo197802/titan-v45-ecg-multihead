"""Validate the aggregate-only receipt from the label-blind SPH scale probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

EXPECTED_PROTOCOL_SHA256 = "d788ad8cca94793cebb738496acc131e82b1ca1900976f11020b99a79a5fc366"
EXPECTED_LEDGER_SHA256 = "4a3a1e61b1784e06190d5caaa089fca04ef84792acb3a5f9fc1af3f9c1173462"
EXPECTED_SCRIPT_SHA256 = "2228d242e001af7f40893ae8589556ee8cdce398665584cdfcfa079b76e3cd10"
EXPECTED_MODELS = {
    "backbone-v3f-original.pt": "ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8",
    "backbone-v3ag-pathology.pt": "bf71e4cf8acc34031cb3611c7031e0649822e705fd7dcea354a3ea583ce920ee",
    "specialists-v3ag-primary4-calibrated.pt": "cf5091e962fffb3254b1a71fe57236dd82ea0139093df192511499d931391dbc",
    "specialists-v3p-e008-primary6-diagnostic.pt": "9c5a9265a7155e1206c551cc4e6d645b86363ba3dbdeb7baf7b9f173c314be3d",
    "specialists-v3q-primary8-best-candidate.pt": "b30cb2bbb45f1231c93ff1c196aa966b57b49831cadb296131c0283e7b0ceb02",
}
PROFILE_CLASSES = {
    "P4": {"ASMI", "IMI", "ISC_", "LVH"},
    "P6": {"1AVB", "AFIB", "PVC", "RBBB", "SB", "STACH"},
    "P8": {"1AVB", "AFIB", "NSR", "PAC", "PVC", "RBBB", "SB", "STACH"},
}
FORBIDDEN_KEY_PARTS = (
    "record_id",
    "record_ids",
    "ecg_id",
    "patient_id",
    "patient_ids",
    "raw_signal",
    "record_level_prediction",
)


def _fail(message: str) -> None:
    raise ValueError(message)


def _reject_private_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in FORBIDDEN_KEY_PARTS):
                _fail("aggregate contains a record-level field")
            _reject_private_keys(child)
    elif isinstance(value, list):
        for child in value:
            _reject_private_keys(child)


def _check_count(value: object, name: str, maximum: int) -> None:
    if type(value) is not int or not 0 <= value <= maximum:
        _fail(f"{name} must be an integer in [0, {maximum}]")


def _check_comparison(value: object, name: str, expected_records: int) -> None:
    if not isinstance(value, dict) or value.get("records") != expected_records:
        _fail(f"{name} denominator differs from the selected sample")
    profiles = value.get("profiles")
    if not isinstance(profiles, dict) or set(profiles) != set(PROFILE_CLASSES):
        _fail(f"{name} profile set is incomplete")
    for profile, classes in PROFILE_CLASSES.items():
        item = profiles[profile]
        changes = item.get("score_changes") if isinstance(item, dict) else None
        if not isinstance(changes, dict) or set(changes) != classes:
            _fail(f"{name}.{profile} class set is incomplete")
        for class_name, scores in changes.items():
            if not isinstance(scores, dict):
                _fail(f"{name}.{profile}.{class_name} score summary is malformed")
            mean = scores.get("mean_absolute")
            maximum = scores.get("max_absolute")
            if any(
                not isinstance(number, (int, float))
                or not math.isfinite(number)
                or not 0 <= number <= 1
                for number in (mean, maximum)
            ):
                _fail(f"{name}.{profile}.{class_name} score changes are invalid")
            if mean > maximum:
                _fail(f"{name}.{profile}.{class_name} mean exceeds its maximum")
            _check_count(scores.get("label_changes"), f"{name}.{profile}.{class_name}.label_changes", expected_records)
        _check_count(item.get("top1_changes"), f"{name}.{profile}.top1_changes", expected_records)
        _check_count(item.get("fallback_changes"), f"{name}.{profile}.fallback_changes", expected_records)


def validate_report(
    report: object,
    *,
    expected_job_id: str,
    expected_experiment_commit: str,
) -> dict[str, object]:
    if not isinstance(report, dict):
        _fail("aggregate root must be an object")
    _reject_private_keys(report)
    if report.get("schema") != "TITAN_V46_SPH_AMPLITUDE_SENSITIVITY_V1":
        _fail("unexpected scale-sensitivity schema")
    if report.get("selected_records") != 128 or report.get("factors") != [0.5, 1.0, 2.0]:
        _fail("sample size or scale factors differ from the frozen probe")
    if report.get("individual_records_exported") is not False:
        _fail("individual records must not be exported")
    if report.get("labels_used_for_selection_or_inference") is not False:
        _fail("reference labels must not be used by the scale probe")
    if report.get("job_id") != expected_job_id:
        _fail("SLURM job ID differs from the expected execution")
    if report.get("experiment_commit") != expected_experiment_commit:
        _fail("experiment commit differs from the expected execution")
    if "A100" not in str(report.get("gpu", "")):
        _fail("scale probe did not identify the required A100 device")
    if report.get("model_sha256") != EXPECTED_MODELS:
        _fail("checkpoint hashes differ from the frozen protocol")
    if report.get("frozen_protocol_sha256") != EXPECTED_PROTOCOL_SHA256:
        _fail("frozen protocol hash differs")
    if report.get("frozen_ledger_sha256") != EXPECTED_LEDGER_SHA256:
        _fail("frozen ledger hash differs")
    if report.get("script_sha256") != EXPECTED_SCRIPT_SHA256:
        _fail("scale runner hash differs")

    _check_comparison(report.get("baseline_replay_vs_archived"), "baseline", 128)
    perturbations = report.get("perturbations_vs_factor_1")
    if not isinstance(perturbations, dict) or set(perturbations) != {"0.5", "2.0"}:
        _fail("perturbation factors are incomplete")
    for factor, comparison in perturbations.items():
        _check_comparison(comparison, f"factor_{factor}", 128)
    return {"job_id": expected_job_id, "records": 128, "profiles": ["P4", "P6", "P8"]}


def verify_file(path: Path, *, expected_job_id: str, expected_experiment_commit: str) -> str:
    report = json.loads(path.read_text(encoding="utf-8"))
    validate_report(
        report,
        expected_job_id=expected_job_id,
        expected_experiment_commit=expected_experiment_commit,
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(
        f"Verified aggregate-only SPH scale probe: job={expected_job_id} "
        f"records=128 profiles=P4,P6,P8 sha256={digest}"
    )
    return digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-job-id", required=True)
    parser.add_argument("--expected-experiment-commit", required=True)
    args = parser.parse_args()
    verify_file(
        args.report,
        expected_job_id=args.expected_job_id,
        expected_experiment_commit=args.expected_experiment_commit,
    )


if __name__ == "__main__":
    main()
