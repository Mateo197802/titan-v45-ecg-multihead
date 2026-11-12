"""Build or check the deterministic, disclosure-limited scientific closure packet."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from verify_reviewer_november_delivery import protected_path, validate_public
from verify_reviewer_scientific_closure import PUBLIC_NAMES

DOC_ROOT = "docs/reviewer_closure_experiments"
DATA_ROOT = "outputs/results/reviewer_closure_experiments"
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
PRIOR = (
    "november_delivery_verification_33596.json", "population-contrast_33399_aggregate.json",
    "rhythm-other_33396_aggregate.json", "pathology-other_33390_aggregate.json",
    "auxiliary_33369_aggregate.json", "ptbxl-bridge_33410_aggregate.json",
    "joint-selective_33414_aggregate.json", "joint-selective_33414_joint-policy.json",
    "selective_33362_policy.json", "selective_33362_aggregate.json", "replay-contrast_33472_aggregate.json",
    "retrained-eval_33596_aggregate.json", "release_backbone_head_support.json",
)
ALLOWLIST = frozenset((
    *(f"{DOC_ROOT}/{name}" for name in REQUIRED_DOCS),
    *(f"{DATA_ROOT}/{name}" for name in PUBLIC_NAMES.values()),
    f"{DATA_ROOT}/native_closure_verification.json",
    *(f"outputs/results/reviewer_experiments/{name}" for name in PRIOR),
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
    "scripts/evaluation/build_reviewer_scientific_closure_zip.py",
    "scripts/evaluation/verify_reviewer_scientific_closure.py",
    "scripts/evaluation/verify_reviewer_november_delivery.py",
    "scripts/evaluation/score_reviewer_closure_ludb.py",
    "scripts/evaluation/compare_reviewer_baseline.py",
    "scripts/evaluation/freeze_reviewer_selective_policy.py",
))
MANIFEST = "SHA256SUMS.json"


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def member(z, name, content):
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (0o100644 << 16)
    info.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(info, content, compresslevel=9)


def build(root, output):
    blobs = {name: protected_path(root, name).read_bytes() for name in sorted(ALLOWLIST)}
    for name, data in blobs.items():
        if name.startswith(f"{DATA_ROOT}/") or (name.startswith(f"{DOC_ROOT}/") and name.endswith(".json")):
            validate_public(json.loads(data))
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
        if manifest.keys() != ALLOWLIST or any(digest_bytes(z.read(k)) != v for k, v in manifest.items()):
            raise ValueError("packet checksum mismatch")
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
