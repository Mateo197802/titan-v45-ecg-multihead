"""Build a deterministic archive of approved public evidence, without running inference."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from external_evidence_tables import (
    PRIMARY,
    SOURCE_FILES,
    csv_bytes,
    git_blob,
    sha,
    tables,
    verified_sources,
)
from verify_external_evidence import (
    MANIFEST,
    MEMBERS,
    PAYLOAD,
    REPO_URL,
    SUMS,
    TECH,
    TRACE,
    VERIFIERS,
    ZIP_NAME,
    checksums,
    snapshot_path,
    verify,
)

ROOT = Path(__file__).resolve().parents[2]
SUPPLEMENT = {
    "6": ("85d673ac04986fe1c50a8cf39d8279344a708647", (
        "docs/external_validation_20261111/CODE15_FULL_EVALUATION.md",
        "docs/external_validation_20261111/FROZEN_EXTERNAL_EVALUATION_PROTOCOL.json",
        "outputs/results/external_validation_20261111/code15-full/CODE15_FULL_DELIVERY_RECEIPT.json",
    )),
    "10": (PRIMARY, (
        "docs/domain_adaptation/DOMAIN_ADAPTATION_IMPLEMENTATION.md",
        "docs/domain_adaptation/CODE_DURATION_CORRECTION_REPORT.md",
        "docs/domain_adaptation/evidence/TRAINING_EXPERIMENTS_COMPLETE.csv",
        "docs/domain_adaptation/evidence/FINETUNING_LEARNING_CURVES.csv",
        "docs/domain_adaptation/evidence/SOURCE_GENERALIZATION_MATRIX.csv",
        "scripts/domain_adaptation/evaluate_new_holdout.py",
        "scripts/domain_adaptation/train_duration_aware.py",
        "scripts/domain_adaptation/audit_private_holdout.py",
    )),
    "11": ("4fddf0de37c0a5768dd39994cdcfdf283dfde131", (
        "docs/performance_recovery/FINAL_MODEL_TECHNICAL_ASSESSMENT.md",
        "docs/performance_recovery/evidence/PUBLIC_VERIFICATION_RECEIPT.json",
        "docs/performance_recovery/evidence/FINETUNING_EXPERIMENTS.csv",
        "docs/performance_recovery/evidence/SLURM_EXECUTION_LEDGER.csv",
    )),
    "12": ("608b8c1be17e4dd15a3e73a75be69bc49ac4b003", (
        "docs/reviewer_two_comment_rigorous/FINAL_TWO_COMMENT_SCIENTIFIC_VERDICT.md",
        "docs/reviewer_two_comment_rigorous/R2_3F_MORPHOLOGY_FINAL_VALIDATION.md",
        "docs/reviewer_two_comment_rigorous/R2_4K_SELECTIVE_PREDICTION_FINAL_VALIDATION.md",
    )),
    "15": ("732ecb1c8e697997cdedf85f67db70d38bd765ed", (
        "docs/performance_recovery/CORRECTIVE_TECHNICAL_ASSESSMENT.md",
        "docs/performance_recovery/corrective_evidence/CORRECTIVE_DECISION.json",
        "docs/performance_recovery/corrective_evidence/CORRECTIVE_SLURM.csv",
    )),
    "16": ("0e1480b15739581e69f672df349cc3f86244d0f8", (
        "docs/performance_recovery/AUTONOMOUS_LOOP_RESULTS.md",
        "docs/performance_recovery/autonomous_evidence/MODEL_PROMOTION_DECISION.json",
        "docs/performance_recovery/autonomous_evidence/AUTONOMOUS_LOOP_EXECUTION_LEDGER.csv",
    )),
    "historical": ("6f50a6337fc3e8b518655b05916ced7447598b47", (
        "docs/evidence-status.md", "docs/reviewer_closure/HISTORICAL_CALIBRATION_AND_SPLIT_UPDATE.md",
        "docs/reviewer_closure/CHECKPOINT_JOB_MANIFEST_VERIFICATION_FINAL.md",
    )),
}


def trace(src):
    def record(tier, pr, commit, path, data, disposition):
        return {"tier": tier, "pr": pr, "commit": commit, "source_path": path, "sha256": sha(data),
                "url": f"{REPO_URL}/blob/{commit}/{path}", "disposition": disposition}

    records = [record("A", "10", PRIMARY, path, src[name], snapshot_path(name))
               for name, path in sorted(SOURCE_FILES.items())]
    for pr, (commit, paths) in SUPPLEMENT.items():
        records.extend(record("B", pr, commit, path, git_blob(ROOT, commit, path), "reference_only") for path in paths)
    prep = json.loads(src["PREPROCESSING_REPRODUCIBILITY.json"])
    for path, expected in prep["source_hashes"].items():
        commit = prep["code_development_commit"]
        data = git_blob(ROOT, commit, path)
        if sha(data) != expected:
            raise ValueError(f"historical preprocessing code SHA differs: {path}")
        records.append(record("B", "10", commit, path, data, "reference_only"))
    return csv_bytes(records)


def archive(payload):
    if set(payload) != MEMBERS:
        raise ValueError("archive must contain only approved payload files")
    stream = io.BytesIO()
    with ZipFile(stream, "w", compression=ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(payload.items()):
            info = ZipInfo(name, (2026, 11, 13, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=9)
    return stream.getvalue()


def build(folder):
    def write(name, data):
        file = folder / name
        if not file.resolve().is_relative_to(folder.resolve()) or file.is_symlink():
            raise ValueError(f"unsafe output: {name}")
        file.parent.mkdir(exist_ok=True, parents=True)
        file.write_bytes(data)

    src = verified_sources(ROOT)
    for name, data in tables(src).items():
        write(f"manuscript_core/{name}", data)
    for name, data in src.items():
        write(snapshot_path(name), data)
    for name in VERIFIERS:
        write(f"{TECH}/{name}", (Path(__file__).parent / name).read_bytes())
    write(TRACE, trace(src))
    payload = {name: (folder / name).read_bytes() for name in PAYLOAD}
    manifest = {
        "schema": "TITAN_V45_EXTERNAL_EVIDENCE_V1", "primary_commit": PRIMARY, "scope": "WITHIN_CODE_HELD_OUT",
        "status": {"WITHIN_CODE_HELD_OUT_EVALUATION": "COMPLETED",
                   "INDEPENDENT_INSTITUTIONAL_VALIDATION": "NOT_EVALUATED", "P4_EXTERNAL_VALIDATION": "NOT_EVALUATED",
                   "MODEL_PROMOTION": "NOT_AUTHORIZED", "MANUSCRIPT_MODIFIED": False},
        "files": {name: {"sha256": sha(data), "bytes": len(data), "role": name.split("/")[0]}
                  for name, data in sorted(payload.items())},
    }
    payload[MANIFEST] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    payload[SUMS] = checksums(payload)
    write(MANIFEST, payload[MANIFEST])
    write(SUMS, payload[SUMS])
    raw = archive(payload)
    write(ZIP_NAME, raw)
    write(ZIP_NAME + ".sha256", f"{sha(raw)}  {ZIP_NAME}\n".encode())
    return verify(folder, ROOT)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("folder", type=Path, nargs="?", default=ROOT / "docs/external_evidence")
    print(json.dumps(build(cli.parse_args().folder), sort_keys=True))
