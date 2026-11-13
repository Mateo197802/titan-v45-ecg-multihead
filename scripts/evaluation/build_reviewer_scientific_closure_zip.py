"""Build or check the deterministic, disclosure-limited scientific closure packet."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

from render_reviewer_closure_tables import TABLES, render
from verify_reviewer_november_delivery import protected_path, validate_public
from verify_reviewer_scientific_closure import (
    JOBS,
    PUBLIC_NAMES,
    check_ludb_detail,
    check_ptb,
    check_ptbxl_rhythm,
    check_ptbxl_support,
    check_scientific,
)

DOC_ROOT = "docs/reviewer_closure_experiments"
DATA_ROOT = "outputs/results/reviewer_closure_experiments"
PRIOR_ROOT = "outputs/results/reviewer_experiments"
REQUIRED_DOCS = (
    "FOUR_REVIEWER_FINAL_SCIENTIFIC_CLOSURE.md",
    "FOUR_REVIEWER_CLOSURE_MATRIX.csv",
    "FULL_WORKFLOW_VALIDATION.md",
    "OTHER_CLASS_VALIDATION.md",
    "MORPHOLOGY_REPRODUCIBILITY_AND_ABLATION.md",
    "SELECTIVE_PREDICTION_VALIDATION.md",
    "PATIENT_SIGNAL_SPLIT_AUDIT.json",
    "EXPERIMENT_PROVENANCE_AND_HASHES.json",
    "REVIEWER_EVIDENCE_GAP_RESOLUTION.md",
    "SCIENTIFIC_READINESS_FOR_MANUSCRIPT.json",
    "PROTOCOL_FREEZE.md",
    "CLOSURE_EXECUTION_REGISTER.md",
)
PRIOR_NATIVE = {
    "sph_baseline_scoring_receipt_33355.json": ("33355", "scoring-receipt.json"),
    "sph_repeat_audit_33356.json": ("33356", "aggregate.json"),
    "sph-ece-report_33357_aggregate.json": ("33357", "aggregate.json"),
    "selective_33362_policy.json": ("33362", "policy.json"),
    "selective_33362_aggregate.json": ("33362", "aggregate.json"),
    "auxiliary_33369_aggregate.json": ("33369", "aggregate.json"),
    "pathology-other_33390_aggregate.json": ("33390", "aggregate.json"),
    "rhythm-other_33396_aggregate.json": ("33396", "aggregate.json"),
    "population-contrast_33399_aggregate.json": ("33399", "aggregate.json"),
    "ptbxl-bridge_33410_aggregate.json": ("33410", "aggregate.json"),
    "joint-selective_33414_aggregate.json": ("33414", "aggregate.json"),
    "joint-selective_33414_joint-policy.json": ("33414", "joint-policy.json"),
    "replay-contrast_33472_aggregate.json": ("33472", "aggregate.json"),
    "morph-sensitivity_33473_p4-aggregate.json": ("33473", "p4-aggregate.json"),
    "morph-sensitivity_33473_rhythm-aggregate.json": ("33473", "rhythm-aggregate.json"),
    "retrained-eval_33596_aggregate.json": ("33596", "aggregate.json"),
}
PRIOR_RECEIPT = "november_delivery_verification_33596.json"
PRIOR_RECEIPT_SHA256 = "a4c54f5480145bf1a3bfae5dea9a5aa2b530850146f1dadbe3f33046888ebde8"
PRIOR_HEAD_SUPPORT = "release_backbone_head_support.json"
PRIOR_HEAD_SUPPORT_SHA256 = "7afa919842ba850d8b8544c9cc2d4b52046bab87e42e2fff13a8b7d857193513"
ALLOWLIST = frozenset((
    *(f"{DOC_ROOT}/{name}" for name in REQUIRED_DOCS),
    f"{DOC_ROOT}/{TABLES}",
    *(f"{DATA_ROOT}/{name}" for name in PUBLIC_NAMES.values()),
    f"{DATA_ROOT}/native_closure_verification.json",
    *(f"{PRIOR_ROOT}/{name}" for name in (*PRIOR_NATIVE, PRIOR_RECEIPT, PRIOR_HEAD_SUPPORT)),
    "docs/reviewer_experiments/MORPHOLOGY_INPUT_CONTRACT.md",
    "docs/reviewer_experiments/RELEASE_HEAD_SUPPORT.md",
    "docs/reviewer_experiments/NOVEMBER_FINDINGS.md",
    "docs/reviewer_experiments/NOVEMBER_EXECUTION.md",
    "docs/replay-residual-diagnostics.md",
    "configs/reviewer_experiments/scientific_closure_v1.json",
    "configs/reviewer_experiments/morphology_posthoc_robustness_v1.json",
    "configs/reviewer_experiments/ptb_diagnostic_eligibility_v1.json",
    "configs/reviewer_experiments/ptb_diagnostic_eligibility_v2.json",
    "configs/reviewer_experiments/ptb_diagnostic_transport_v1.json",
    *(f"configs/reviewer_experiments/november_{name}.json" for name in (
        "joint_selective", "pathology_other", "phase1", "population_contrast", "ptbxl_reference_bridge", "rhythm_other",
    )),
    "scripts/evaluation/build_reviewer_scientific_closure_zip.py",
    "scripts/evaluation/render_reviewer_closure_tables.py",
    "scripts/evaluation/verify_reviewer_scientific_closure.py",
    "scripts/evaluation/verify_reviewer_november_delivery.py",
    "scripts/evaluation/score_reviewer_closure_ludb.py",
    "scripts/evaluation/audit_reviewer_ptbxl_other_support.py",
    "scripts/evaluation/evaluate_reviewer_ptbxl_cached_rhythm.py",
    "scripts/cedia/reviewer_closure_ptbxl_cached_rhythm.sbatch",
    "scripts/cedia/reviewer_private_scratch.sh",
    "scripts/evaluation/compare_reviewer_baseline.py",
    "scripts/evaluation/freeze_reviewer_selective_policy.py",
))
MANIFEST = "SHA256SUMS.json"
FINAL_STATUS = "FINAL_NATIVE_VERIFIED"
COMMENTS = {"R1-2", "R2-general", "R2-3f", "R2-4k"}
DISPOSITIONS = {
    "SCIENTIFICALLY_SATISFIED", "SCIENTIFICALLY_SATISFIED_WITH_LIMITATIONS",
    "PARTIAL_EVIDENCE", "NOT_DEMONSTRATED", "BLOCKED_BY_REFERENCE_OR_DATA",
}


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def check_prior_evidence(blobs):
    receipt_data = blobs[f"{PRIOR_ROOT}/{PRIOR_RECEIPT}"]
    if digest_bytes(receipt_data) != PRIOR_RECEIPT_SHA256:
        raise ValueError("historical November verification receipt changed")
    receipt = json.loads(receipt_data)
    if receipt["verified_jobs"] != 16 or receipt["required_jobs"] != 16 or receipt["verification_errors"]:
        raise ValueError("historical November verification is incomplete")
    for name, (job, artifact) in PRIOR_NATIVE.items():
        native = receipt["jobs"][job]
        expected = native["aggregate_candidates"][artifact]
        if (native["result_status"] != "verified" or not expected["producer_checksum_verified"]
                or digest_bytes(blobs[f"{PRIOR_ROOT}/{name}"]) != expected["sha256"]):
            raise ValueError(f"historical November evidence differs from the producer seal: {name}")
    if digest_bytes(blobs[f"{PRIOR_ROOT}/{PRIOR_HEAD_SUPPORT}"]) != PRIOR_HEAD_SUPPORT_SHA256:
        raise ValueError("historical released-head support audit changed")


def member(z, name, content):
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (0o100644 << 16)
    info.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(info, content, compresslevel=9)


def validate_final(blobs):
    for name, data in blobs.items():
        if name.startswith(f"{DATA_ROOT}/") or (name.startswith(f"{DOC_ROOT}/") and name.endswith(".json")):
            validate_public(json.loads(data))
    for name in ("PATIENT_SIGNAL_SPLIT_AUDIT", "EXPERIMENT_PROVENANCE_AND_HASHES",
                 "SCIENTIFIC_READINESS_FOR_MANUSCRIPT"):
        if json.loads(blobs[f"{DOC_ROOT}/{name}.json"])["status"] != FINAL_STATUS:
            raise ValueError(f"working document cannot enter a final packet: {name}")
    readiness = json.loads(blobs[f"{DOC_ROOT}/SCIENTIFIC_READINESS_FOR_MANUSCRIPT.json"])
    matrix = list(csv.DictReader(io.StringIO(blobs[f"{DOC_ROOT}/FOUR_REVIEWER_CLOSURE_MATRIX.csv"].decode("utf-8"))))
    dispositions = {row["comment"]: row["scientific_status"] for row in matrix}
    if (len(matrix) != len(COMMENTS) or set(dispositions) != COMMENTS
            or set(dispositions.values()) - DISPOSITIONS
            or dispositions != {k: v["scientific_status"] for k, v in readiness["comments"].items()}):
        raise ValueError("final closure matrix and scientific dispositions differ")
    receipt = json.loads(blobs[f"{DATA_ROOT}/native_closure_verification.json"])
    scheduler = receipt["scheduler"]
    checks = receipt["public_sha256"]
    if (receipt["science_consistency_verified"] is not True
            or receipt["record_level_export_performed"] is not False
            or receipt["public_files"] != PUBLIC_NAMES or set(checks) != set(PUBLIC_NAMES)
            or any((scheduler[j]["state"], scheduler[j]["exit_code"]) != ("COMPLETED", "0:0")
                   for j in JOBS.values())):
        raise ValueError("final native receipt is incomplete")
    content = {}
    for key, name in PUBLIC_NAMES.items():
        raw = blobs[f"{DATA_ROOT}/{name}"]
        if digest_bytes(raw) != checks[key]:
            raise ValueError(f"artifact does not match native SHA-256: {name}")
        content[key] = json.loads(raw)
        if key in JOBS and str(content[key]["job"]) != JOBS[key]:
            raise ValueError(f"artifact producer does not match native receipt: {name}")
    check_scientific(content["score"], content["evaluate"], content["morphology"], content["sph"], checks["score"])
    check_ludb_detail(content["score"], content["evaluate"])
    check_ptb(content["ptb_score"], content["ptb_evaluate"], content["ptb_eligibility"], checks["ptb_score"])
    fit = json.loads(blobs[f"{PRIOR_ROOT}/pathology-other_33390_aggregate.json"])["endpoints"]
    if (content["ptb_score"]["published_thresholds"] != content["score"]["thresholds"]["P4"]
            or content["ptb_score"]["transported_thresholds"] != {c: fit[c]["threshold"] for c in ("ALMI", "ILMI")}):
        raise ValueError("PTB Diagnostic used different published or development cutoffs")
    check_ptbxl_support(content["ptbxl_support"], checks["ptbxl_support"])
    check_ptbxl_rhythm(content["ptbxl_rhythm_score"], content["ptbxl_rhythm_evaluate"],
                     content["ptbxl_support"], checks["ptbxl_rhythm_score"])
    if blobs[f"{DOC_ROOT}/{TABLES}"] != render(content):
        raise ValueError("endpoint and route tables differ from verified aggregates")
    check_prior_evidence(blobs)


def build(root, output):
    blobs = {name: protected_path(root, name).read_bytes() for name in sorted(ALLOWLIST)}
    validate_final(blobs)
    manifest = {name: digest_bytes(data) for name, data in blobs.items()}
    with zipfile.ZipFile(output, "x") as z:
        for name, data in blobs.items():
            member(z, name, data)
        member(z, MANIFEST, (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("ascii"))
    return verify(output)


def verify(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if set(names) != ALLOWLIST | {MANIFEST} or len(names) != len(set(names)):
            raise ValueError("packet includes missing, duplicate or unapproved members")
        manifest = json.loads(z.read(MANIFEST))
        blobs = {name: z.read(name) for name in ALLOWLIST}
        if manifest.keys() != ALLOWLIST or any(digest_bytes(blobs[k]) != v for k, v in manifest.items()):
            raise ValueError("packet checksum mismatch")
        validate_final(blobs)
    return {"files_verified": len(manifest), "zip_sha256": digest_bytes(path.read_bytes())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "verify"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--repo", type=Path, default=Path("."))
    args = parser.parse_args()
    result = build(args.repo.resolve(), args.packet) if args.mode == "build" else verify(args.packet)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
