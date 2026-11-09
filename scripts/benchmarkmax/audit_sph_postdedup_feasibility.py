"""Audit aggregate SPH endpoint support after label-blind signal checks and exact deduplication."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tarfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.data.sph import (  # noqa: E402
    FS_HZ,
    RECORD_ID,
    read_sph_dictionary,
    read_sph_metadata,
    read_sph_signal,
)

SPLIT_NAMESPACE = "TITAN-V46-SPH-DEV-SPLIT-V1:"
SPLIT_SEED = "197802"
TARGETS = {
    "ASMI": (165, "Anteroseptal MI"),
    "IMI": (161, "Inferior MI"),
    "LVH": (142, "Left ventricular hypertrophy"),
    "PAC": (30, "Atrial premature complex(es)"),
    "PVC": (60, "Ventricular premature complex(es)"),
    "RBBB": (106, "Right bundle-branch block"),
}
SPLIT_NAMES = {
    "train": "train",
    "development": "development",
    "calibration": "exploratory_holdout",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_label_blind_signal_index(path: Path) -> dict[str, int]:
    """Read only ECG IDs and sample counts; diagnostic columns are not inspected."""
    output: dict[str, int] = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"ECG_ID", "N"}.issubset(reader.fieldnames or ()):
            raise ValueError("SPH metadata lacks the label-blind signal-index columns")
        for row in reader:
            record_id = row["ECG_ID"].strip()
            samples = int(row["N"])
            if not RECORD_ID.fullmatch(record_id) or samples < 1 or record_id in output:
                raise ValueError("invalid or duplicate ECG ID/sample count in signal index")
            output[record_id] = samples
    if not output:
        raise ValueError("SPH signal index is empty")
    return output


def scan_waveform_archive(
    waveform_path: Path, signal_index: dict[str, int]
) -> tuple[set[str], dict[str, object]]:
    """Return unique usable signal IDs after exact duplicate groups are removed."""
    seen: set[str] = set()
    valid_ids: set[str] = set()
    fingerprints: dict[str, list[str]] = defaultdict(list)
    counts: Counter[str] = Counter()

    with tarfile.open(waveform_path, mode="r|*") as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or ".." in path.parts or "\\" in member.name
                    or len(path.parts) > 2):
                raise ValueError("unsafe path in SPH waveform archive")
            if member.isdir():
                continue
            if (not member.isfile() or path.suffix != ".h5"
                    or not RECORD_ID.fullmatch(path.stem)):
                raise ValueError("unexpected member type in SPH waveform archive")
            record_id = path.stem
            if record_id not in signal_index or record_id in seen:
                raise ValueError("unknown or duplicate ECG ID in waveform archive")
            seen.add(record_id)
            if not 0 < member.size <= 2 * 1024 * 1024:
                counts["invalid_hdf5_member_size"] += 1
                continue
            samples = signal_index[record_id]
            if not 10 * FS_HZ <= samples <= 60 * FS_HZ:
                counts["duration_outside_10_to_60_seconds"] += 1
                continue
            raw = archive.extractfile(member)
            if raw is None:
                counts["unreadable_archive_member"] += 1
                continue
            try:
                signal, _ = read_sph_signal(raw.read(), samples)
            except (ValueError, OSError):
                counts["invalid_hdf5_shape_dtype_or_signal"] += 1
                continue
            canonical = np.asarray(signal, dtype="<f8")
            if not np.any(np.ptp(canonical, axis=1) > 0):
                counts["all_leads_flat"] += 1
                continue
            fingerprint = hashlib.sha256(canonical.tobytes(order="C")).hexdigest()
            fingerprints[fingerprint].append(record_id)
            valid_ids.add(record_id)

    if seen != signal_index.keys():
        raise ValueError(
            "waveform archive population differs from metadata index: "
            f"missing={len(signal_index.keys() - seen)}"
        )

    duplicate_groups = [group for group in fingerprints.values() if len(group) > 1]
    duplicate_ids = {record_id for group in duplicate_groups for record_id in group}
    unique_ids = valid_ids - duplicate_ids
    counts["source_records"] = len(signal_index)
    counts["archive_members_seen"] = len(seen)
    counts["valid_signal_records"] = len(valid_ids)
    counts["exact_duplicate_signal_groups"] = len(duplicate_groups)
    counts["exact_duplicate_signal_excess_records"] = sum(
        len(group) - 1 for group in duplicate_groups
    )
    counts["exact_duplicate_records_excluded"] = len(duplicate_ids)
    counts["unique_signal_records"] = len(unique_ids)
    return unique_ids, dict(sorted(counts.items()))


def assign_split(patient_id: str) -> str:
    patient_id = patient_id.strip()
    if not patient_id:
        raise ValueError("missing patient identifier")
    raw = f"{SPLIT_NAMESPACE}{SPLIT_SEED}:{patient_id}".encode()
    bucket = int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "development"
    return "calibration"


def aggregate_support(metadata, selected_ids: set[str]) -> dict[str, object]:
    if not selected_ids.issubset(metadata):
        raise ValueError("eligible ECG is not present in metadata")

    split_records = {name: 0 for name in SPLIT_NAMES.values()}
    split_patients = {name: set() for name in SPLIT_NAMES.values()}
    support = {
        split: {
            endpoint: {
                "positive_records": 0,
                "statement_not_recorded_records": 0,
                "positive_patients": set(),
            }
            for endpoint in TARGETS
        }
        for split in SPLIT_NAMES.values()
    }

    for record_id in selected_ids:
        entry = metadata[record_id]
        split = SPLIT_NAMES[assign_split(entry.patient)]
        split_records[split] += 1
        split_patients[split].add(entry.patient)
        for endpoint, (code, _) in TARGETS.items():
            target = support[split][endpoint]
            if code in entry.primary_codes:
                target["positive_records"] += 1
                target["positive_patients"].add(entry.patient)
            else:
                target["statement_not_recorded_records"] += 1

    patient_split_names = [set(values) for values in split_patients.values()]
    if any(
        left & right
        for index, left in enumerate(patient_split_names)
        for right in patient_split_names[index + 1:]
    ):
        raise AssertionError("patient assigned to multiple support splits")

    splits = {}
    for split in SPLIT_NAMES.values():
        endpoint_support = {}
        for endpoint, values in support[split].items():
            endpoint_support[endpoint] = {
                "positive_records": values["positive_records"],
                "statement_not_recorded_records": values["statement_not_recorded_records"],
                "positive_patients": len(values["positive_patients"]),
            }
        splits[split] = {
            "records": split_records[split],
            "patients": len(split_patients[split]),
            "endpoints": endpoint_support,
        }
    return {
        "record_denominator": len(selected_ids),
        "splits": splits,
        "individual_identifiers_exported": False,
    }


def _assert_outside(path: Path, roots: list[Path], label: str) -> None:
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            continue
        raise ValueError(f"{label} must remain outside all Git checkouts")


def _validate_config(config: dict[str, object]) -> None:
    if config.get("schema") != "TITAN_V46_SPH_POSTDEDUP_SUPPORT_V1":
        raise ValueError("unexpected frozen support-audit schema")
    if config.get("status") != "frozen_before_support_counts":
        raise ValueError("support configuration is not frozen")
    source = config.get("source")
    expected = config.get("expected_signal_audit")
    runtime = config.get("runtime")
    if (not isinstance(source, dict) or not isinstance(expected, dict)
            or not isinstance(runtime, dict)):
        raise ValueError("frozen source/support expectations are malformed")
    if (set(runtime) != {
            "python", "numpy", "h5py", "h5py_dependency_archive_sha256",
    } or not re.fullmatch(r"[0-9a-f]{64}", runtime["h5py_dependency_archive_sha256"])):
        raise ValueError("frozen runtime contract is malformed")
    hashes = source.get("input_sha256")
    if (not isinstance(hashes, dict)
            or set(hashes) != {"metadata", "dictionary", "waveform_archive"}
            or any(not re.fullmatch(r"[0-9a-f]{64}", value)
                   for value in hashes.values())):
        raise ValueError("frozen source hashes are malformed")
    if not re.fullmatch(r"[0-9a-f]{64}", source.get("source_inventory_reference_sha256", "")):
        raise ValueError("frozen source-inventory reference hash is malformed")
    inventory_expected = source.get("source_inventory_expected")
    statement_counts = source.get("source_statement_counts_before_signal_exclusions")
    if not isinstance(inventory_expected, dict) or set(inventory_expected) != {
        "schema", "metadata_ecgs", "metadata_patients", "archive_ecgs",
        "valid_signal_ecgs", "metadata_without_signal", "technical_failures",
        "exact_duplicate_signal_groups", "exact_duplicate_signal_excess_records",
    }:
        raise ValueError("frozen source-inventory expectations are malformed")
    if not isinstance(statement_counts, dict) or set(statement_counts) != set(TARGETS):
        raise ValueError("frozen source statement supports are malformed")
    if any(type(value) is not int or value < 0 for value in statement_counts.values()):
        raise ValueError("frozen source statement supports must be nonnegative integers")
    if set(expected) != {
        "records", "patients", "valid_signal_records", "exact_duplicate_signal_groups",
        "exact_duplicate_signal_excess_records", "exact_duplicate_records_excluded",
        "unique_signal_records",
    }:
        raise ValueError("frozen signal-audit expectations are malformed")
    if any(type(value) is not int or value < 0 for value in expected.values()):
        raise ValueError("frozen source counts must be nonnegative integers")
    if (expected["valid_signal_records"] - expected["exact_duplicate_records_excluded"]
            != expected["unique_signal_records"]):
        raise ValueError("frozen unique-signal count is internally inconsistent")
    endpoints = config.get("endpoints")
    if not isinstance(endpoints, dict) or endpoints != {
        name: {"code": code, "description": description}
        for name, (code, description) in TARGETS.items()
    }:
        raise ValueError("frozen endpoint contract differs from the audited labels")


def validate_source_inventory(path: Path, config: dict[str, object]) -> dict[str, object]:
    inventory = json.loads(path.read_text(encoding="utf-8"))
    expected = config["source"]["source_inventory_expected"]
    for field, value in expected.items():
        if inventory.get(field) != value:
            raise ValueError(f"source inventory differs from frozen expectation: {field}")
    expected_support = config["source"]["source_statement_counts_before_signal_exclusions"]
    inventory_support = inventory.get("primary_statement_counts")
    if not isinstance(inventory_support, dict):
        raise ValueError("source inventory lacks aggregate statement counts")
    for endpoint, (code, _) in TARGETS.items():
        if inventory_support.get(str(code)) != expected_support[endpoint]:
            raise ValueError(f"source inventory statement support differs for {endpoint}")
    return inventory


def run(args) -> None:
    metadata_path = args.metadata.resolve()
    dictionary_path = args.dictionary.resolve()
    waveform_path = args.waveforms.resolve()
    inventory_path = args.source_inventory.resolve()
    config_path = args.config.resolve()
    output_path = args.output.resolve()
    forbidden_roots = [ROOT, *(path.resolve() for path in args.forbidden_root)]
    for path, label in (
        (metadata_path, "metadata"), (dictionary_path, "dictionary"),
        (waveform_path, "waveform archive"), (inventory_path, "source inventory"),
        (output_path, "private output"),
    ):
        _assert_outside(path, forbidden_roots, label)
    if sha256_file(config_path) != args.expected_config_sha256:
        raise ValueError("frozen support configuration SHA-256 mismatch")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    _validate_config(config)
    runtime = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "h5py": h5py.__version__,
        "h5py_dependency_archive_sha256": config["runtime"]["h5py_dependency_archive_sha256"],
    }
    if runtime != config["runtime"]:
        raise ValueError("runtime versions differ from the frozen support protocol")
    actual_hashes = {
        "metadata": sha256_file(metadata_path),
        "dictionary": sha256_file(dictionary_path),
        "waveform_archive": sha256_file(waveform_path),
    }
    if actual_hashes != config["source"]["input_sha256"]:
        raise ValueError("SPH source hashes differ from the frozen support protocol")
    inventory_hash = sha256_file(inventory_path)
    if inventory_hash != config["source"]["source_inventory_reference_sha256"]:
        raise ValueError("historical SPH source-inventory reference hash mismatch")

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if commit != args.expected_commit:
        raise ValueError("BenchmarkMax checkout commit differs from the frozen job request")
    if subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, check=True,
                      capture_output=True, text=True).stdout.strip():
        raise ValueError("BenchmarkMax checkout must be clean before CEDIA support audit")

    signal_index = read_label_blind_signal_index(metadata_path)
    expected = config["expected_signal_audit"]
    if len(signal_index) != expected["records"]:
        raise ValueError("SPH signal-index record count differs from the frozen protocol")
    unique_ids, signal_audit = scan_waveform_archive(waveform_path, signal_index)
    for key in (
        "source_records", "valid_signal_records", "exact_duplicate_signal_groups",
        "exact_duplicate_signal_excess_records", "exact_duplicate_records_excluded",
        "unique_signal_records",
    ):
        expected_key = "records" if key == "source_records" else key
        if signal_audit[key] != expected[expected_key]:
            raise ValueError(f"SPH signal audit differs from the frozen expectation: {key}")
    validate_source_inventory(inventory_path, config)

    # Labels are joined only after signal eligibility and duplicate exclusion are fixed.
    primary, modifier = read_sph_dictionary(dictionary_path.read_text(encoding="utf-8-sig"))
    for endpoint, (code, description) in TARGETS.items():
        if primary.get(code) != description:
            raise ValueError(f"SPH source dictionary changed for {endpoint}")
    metadata = read_sph_metadata(
        metadata_path.read_text(encoding="utf-8-sig"), primary, modifier
    )
    if metadata.keys() != signal_index.keys():
        raise ValueError("label-bearing metadata population differs from signal index")
    if any(metadata[key].samples != samples for key, samples in signal_index.items()):
        raise ValueError("label-bearing metadata sample counts differ from signal index")
    patients = {entry.patient for entry in metadata.values()}
    if len(patients) != expected["patients"]:
        raise ValueError("SPH patient count differs from the frozen support protocol")
    actual_statement_counts = {
        endpoint: sum(code in entry.primary_codes for entry in metadata.values())
        for endpoint, (code, _) in TARGETS.items()
    }
    if actual_statement_counts != config["source"]["source_statement_counts_before_signal_exclusions"]:
        raise ValueError("SPH metadata statement supports differ from the frozen inventory")

    before = aggregate_support(metadata, set(metadata))
    after = aggregate_support(metadata, unique_ids)
    report = {
        "schema": "TITAN_V46_SPH_POSTDEDUP_SUPPORT_V1",
        "status": "completed_aggregate_support_audit",
        "scope": (
            "Exploratory SPH development-support counts only. SPH has been previously observed; "
            "this is not performance evaluation, independent validation, or model-specific input validation."
        ),
        "source": {
            "name": "SPH ECG dataset V1",
            "records": len(metadata),
            "patients": len(patients),
            "input_sha256": actual_hashes,
            "source_inventory_reference_sha256": inventory_hash,
        },
        "runtime": runtime,
        "signal_audit": {
            "eligibility": (
                "10-60 seconds at 500 Hz; readable finite 12-lead HDF5; at least one non-flat lead"
            ),
            "fingerprint": "SHA-256 of canonical little-endian float64 raw signal array bytes",
            "duplicate_policy": "exclude every record participating in an exact-signal duplicate group before label join",
            "near_duplicate_detection": False,
            "counts": signal_audit,
        },
        "split": {
            "namespace": SPLIT_NAMESPACE,
            "seed": SPLIT_SEED,
            "algorithm": "SHA-256(namespace + seed + patient ID); first 64 digest bits interpreted big-endian modulo 100",
            "assignment": {"train": "0-69", "development": "70-84", "exploratory_holdout": "85-99"},
            "labels_used_for_assignment": False,
            "patient_overlap_across_splits": 0,
            "third_partition_caveat": (
                "This bucket was used as the exploratory holdout in the PAC pilot; it is not an untouched or confirmatory test."
            ),
        },
        "reference": (
            "AHA code present on this ECG. Absence means statement not recorded, not adjudicated clinical absence."
        ),
        "endpoints": {
            name: {"code": code, "description": description}
            for name, (code, description) in TARGETS.items()
        },
        "support_before_signal_exclusions": before,
        "support_after_signal_and_duplicate_exclusions": after,
        "model_specific_preprocessing_assessed": False,
        "performance_metrics_computed": False,
        "individual_identifiers_exported": False,
        "execution": {
            "commit": commit,
            "slurm_job_id": os.environ.get("SLURM_JOB_ID", "not_slurm"),
            "script_sha256": sha256_file(Path(__file__)),
            "config_sha256": args.expected_config_sha256,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    os.chmod(output_path, 0o600)
    print(json.dumps(
        {"output": str(output_path), "sha256": sha256_file(output_path)}, sort_keys=True
    ))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--waveforms", required=True, type=Path)
    parser.add_argument("--source-inventory", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--expected-config-sha256", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--forbidden-root", action="append", default=[], type=Path)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
