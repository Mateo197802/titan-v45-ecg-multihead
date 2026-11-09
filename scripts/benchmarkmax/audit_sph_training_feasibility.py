"""Summarize SPH statement-label support for exploratory patient-level development splits."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPLIT_NAMESPACE = "TITAN-V46-SPH-DEV-SPLIT-V1:"
SPLIT_SEED = "197802"
SPLIT_BOUNDARIES = (("train", 70), ("development", 85), ("calibration", 100))
TARGETS = {"ASMI": 165, "IMI": 161, "LVH": 142, "PAC": 30, "PVC": 60, "RBBB": 106}
TARGET_DESCRIPTIONS = {
    "ASMI": "Anteroseptal MI",
    "IMI": "Inferior MI",
    "LVH": "Left ventricular hypertrophy",
    "PAC": "Atrial premature complex(es)",
    "PVC": "Ventricular premature complex(es)",
    "RBBB": "Right bundle-branch block",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assign_split(patient_id: str) -> str:
    if not patient_id.strip():
        raise ValueError("missing patient identifier")
    raw = f"{SPLIT_NAMESPACE}{SPLIT_SEED}:{patient_id.strip()}".encode()
    bucket = int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") % 100
    for name, upper_bound in SPLIT_BOUNDARIES:
        if bucket < upper_bound:
            return name
    raise AssertionError("split boundaries do not cover [0, 100)")


def parse_codes(raw: str) -> set[int]:
    codes = set()
    for token in raw.split(";"):
        token = token.strip()
        if not token:
            continue
        base_code = token.split("+", maxsplit=1)[0].strip()
        if not base_code.isdecimal():
            raise ValueError("invalid code in AHA_Code")
        codes.add(int(base_code))
    return codes


def load_code_dictionary(path: Path) -> dict[int, str]:
    mapping = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"Code", "Description"}.issubset(reader.fieldnames or []):
            raise ValueError("code dictionary is missing required columns")
        for row in reader:
            code = int(row["Code"])
            if code in mapping:
                raise ValueError("duplicate code in source dictionary")
            mapping[code] = row["Description"].strip()
    return mapping


def validate_target_dictionary(code_dictionary: dict[int, str]) -> None:
    for target, code in TARGETS.items():
        if code_dictionary.get(code) != TARGET_DESCRIPTIONS[target]:
            raise ValueError(f"source code {code} does not match frozen endpoint {target}")


def build_report(
    rows,
    metadata_sha256: str,
    dictionary_sha256: str,
    script_sha256: str,
    code_dictionary: dict[int, str],
) -> dict:
    if not rows:
        raise ValueError("metadata is empty")
    if any(len(value) != 64 for value in (metadata_sha256, dictionary_sha256, script_sha256)):
        raise ValueError("SHA-256 declarations must contain 64 hexadecimal characters")
    validate_target_dictionary(code_dictionary)

    split_patients = {name: set() for name, _ in SPLIT_BOUNDARIES}
    split_positive_patients = {
        name: {target: set() for target in TARGETS} for name, _ in SPLIT_BOUNDARIES
    }
    split_records = {
        name: {"records": 0, "positive_records": {target: 0 for target in TARGETS}}
        for name, _ in SPLIT_BOUNDARIES
    }
    assignments = {}
    seen_records = set()

    for row in rows:
        record_id = row.get("ECG_ID", "").strip()
        patient_id = row.get("Patient_ID", "").strip()
        if not record_id:
            raise ValueError("missing ECG identifier")
        if record_id in seen_records:
            raise ValueError("duplicate ECG identifier")
        seen_records.add(record_id)
        split = assign_split(patient_id)
        prior = assignments.setdefault(patient_id, split)
        if prior != split:
            raise AssertionError("patient assigned to multiple splits")
        split_patients[split].add(patient_id)
        split_records[split]["records"] += 1
        codes = parse_codes(row.get("AHA_Code", ""))
        for target, code in TARGETS.items():
            if code in codes:
                split_records[split]["positive_records"][target] += 1
                split_positive_patients[split][target].add(patient_id)

    splits = {}
    for name, _ in SPLIT_BOUNDARIES:
        record_count = split_records[name]["records"]
        endpoint_support = {}
        for target in TARGETS:
            positives = split_records[name]["positive_records"][target]
            endpoint_support[target] = {
                "positive_records": positives,
                "statement_not_recorded_records": record_count - positives,
                "positive_patients": len(split_positive_patients[name][target]),
            }
        splits[name] = {
            "records": record_count,
            "patients": len(split_patients[name]),
            "endpoints": endpoint_support,
        }

    return {
        "schema": "TITAN_V46_SPH_TRAINING_FEASIBILITY_V1",
        "scope": (
            "Exploratory development support only. SPH is previously observed and is not a locked "
            "or confirmatory external test."
        ),
        "source": {
            "records": len(seen_records),
            "patients": len(assignments),
            "metadata_sha256": metadata_sha256,
            "code_dictionary_sha256": dictionary_sha256,
        },
        "split": {
            "namespace": SPLIT_NAMESPACE,
            "seed": SPLIT_SEED,
            "algorithm": "SHA-256 of namespace, seed, and patient ID; first 64 bits modulo 100",
            "assignment": {"train": "0-69", "development": "70-84", "calibration": "85-99"},
            "labels_used_for_assignment": False,
            "patient_overlap_across_splits": 0,
            "locked_test_split": False,
        },
        "reference": (
            "AHA code present on this ECG. Absence means statement not recorded, not adjudicated "
            "clinical absence."
        ),
        "endpoint_codes": TARGETS,
        "endpoint_descriptions": TARGET_DESCRIPTIONS,
        "splits": splits,
        "individual_identifiers_exported": False,
        "script_sha256": script_sha256,
    }


def _assert_outside(path: Path, roots: list[Path], label: str) -> None:
    resolved = path.resolve()
    if any(resolved == root or resolved.is_relative_to(root) for root in roots):
        raise ValueError(f"{label} must remain outside all Git checkouts")


def run(args) -> None:
    metadata = args.metadata.resolve()
    dictionary = args.dictionary.resolve()
    output = args.output.resolve()
    forbidden_roots = [ROOT, *(path.resolve() for path in args.forbidden_root)]
    _assert_outside(metadata, forbidden_roots, "metadata")
    _assert_outside(dictionary, forbidden_roots, "source dictionary")
    _assert_outside(output, forbidden_roots, "private output")
    code_dictionary = load_code_dictionary(dictionary)

    with metadata.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"ECG_ID", "Patient_ID", "AHA_Code"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("metadata is missing required columns")
        report = build_report(
            list(reader),
            sha256_file(metadata),
            sha256_file(dictionary),
            sha256_file(Path(__file__)),
            code_dictionary,
        )
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                            capture_output=True, text=True).stdout.strip()
    if subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, check=True,
                      capture_output=True, text=True).stdout.strip():
        raise ValueError("BenchmarkMax checkout must be clean before CEDIA audit")
    report["execution"] = {
        "commit": commit,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID", "not_slurm"),
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    os.chmod(output, 0o600)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--forbidden-root", action="append", default=[], type=Path)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
