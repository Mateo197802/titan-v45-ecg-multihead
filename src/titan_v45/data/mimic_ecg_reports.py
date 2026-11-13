"""Safe, report-only PAC label parsing for public MIMIC-IV-ECG v1.0 metadata."""
from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter
from pathlib import Path, PurePosixPath

_REPORT_COLUMNS = tuple(f"report_{index}" for index in range(18))
_PAC_TERM = (
    r"(?:premature\s+atrial\s+(?:complex(?:es)?|contractions?|beats?)|"
    r"atrial\s+premature\s+(?:complex(?:es)?|contractions?|beats?)|"
    r"atrial\s+ectop(?:y|ic\s+beats?)|(?:PAC|APC)s?)"
)
_PAC_RE = re.compile(rf"\b{_PAC_TERM}\b", re.IGNORECASE)
_NEGATION_RE = re.compile(
    r"\b(?:no|not|without|absent|absence\s+of|negative\s+for|"
    r"no\s+evidence\s+(?:of|for))\b(?:\W+\w+){0,5}\W*$",
    re.IGNORECASE,
)
_POST_NEGATION_RE = re.compile(
    r"^\W*(?:(?:are|is|was|were|have\s+been|has\s+been)\s+)?"
    r"(?:absent\b|absence\b|none\b|negative\b|"
    r"not\s+(?:seen|observed|detected|present|identified|recorded)\b)",
    re.IGNORECASE,
)
_ID_RE = re.compile(r"^[0-9]{8}$")


def classify_machine_pac_report(reports):
    """Classify explicit machine-report mentions; absence of a mention is not negative."""
    text = " ".join(str(value or "").strip() for value in reports).strip()
    if not text:
        return "missing_report_text"
    positive = negative = False
    for match in _PAC_RE.finditer(text):
        context = text[max(0, match.start() - 80):match.start()]
        context = re.split(r"[;.!?\n]", context)[-1]
        following = text[match.end():match.end() + 80]
        following = re.split(r"[;.!?\n]", following)[0]
        if _NEGATION_RE.search(context) or _POST_NEGATION_RE.search(following):
            negative = True
        else:
            positive = True
    if positive and negative:
        return "ambiguous_mention"
    if positive:
        return "positive_mention"
    if negative:
        return "explicit_negative_mention"
    return "not_mentioned"


def _read_record_list(path: Path):
    records = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"subject_id", "study_id", "path"}
        if (not required.issubset(reader.fieldnames or ())
                or len(reader.fieldnames or ()) != len(set(reader.fieldnames or ()))):
            raise ValueError("MIMIC record list lacks subject_id, study_id or path")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("malformed MIMIC record_list row")
            subject, study = row["subject_id"].strip(), row["study_id"].strip()
            if not _ID_RE.fullmatch(subject) or not _ID_RE.fullmatch(study):
                raise ValueError("invalid MIMIC subject_id or study_id")
            path_value = PurePosixPath(row["path"].strip())
            if (path_value.is_absolute() or ".." in path_value.parts or "\\" in row["path"]
                    or len(path_value.parts) != 5 or path_value.parts[0] != "files"
                    or path_value.parts[1] != f"p{subject[:4]}"
                    or path_value.parts[2] != f"p{subject}"
                    or path_value.parts[3] != f"s{study}"
                    or path_value.parts[4] != study):
                raise ValueError("unsafe or inconsistent MIMIC waveform path")
            key = (subject, study)
            if key in records:
                raise ValueError("duplicate waveform key in MIMIC record list")
            records[key] = path_value.as_posix()
    if not records:
        raise ValueError("empty MIMIC record list")
    return records


def iter_mimic_machine_reports(machine_measurements_path, record_list_path):
    """Yield private ID/path joins and frozen report states without reading ECG waveforms."""
    paths = _read_record_list(Path(record_list_path))
    seen = set()
    with Path(machine_measurements_path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fieldnames = set(reader.fieldnames or ())
        report_columns = tuple(column for column in _REPORT_COLUMNS if column in fieldnames)
        if (not {"subject_id", "study_id"}.issubset(fieldnames) or not report_columns
                or len(reader.fieldnames or ()) != len(fieldnames)):
            raise ValueError("MIMIC machine measurements lack required report columns")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("malformed MIMIC machine-measurement row")
            subject, study = row["subject_id"].strip(), row["study_id"].strip()
            if not _ID_RE.fullmatch(subject) or not _ID_RE.fullmatch(study):
                raise ValueError("invalid MIMIC machine-measurement identifiers")
            key = (subject, study)
            if key in seen:
                raise ValueError("duplicate machine-measurement waveform key")
            if key not in paths:
                raise ValueError("machine-measurement key is not present in record_list")
            seen.add(key)
            yield {
                "subject_id": subject,
                "study_id": study,
                "record_path": paths[key],
                "report_state": classify_machine_pac_report(row[column] for column in report_columns),
            }
    missing = set(paths) - seen
    if missing:
        raise ValueError("record_list has missing machine-measurement rows")


def audit_mimic_metadata_source(dataset_root):
    """Return aggregate metadata-join evidence without opening ECG waveforms."""
    root = Path(dataset_root).resolve()
    integrity = verify_mimic_metadata_sha256_manifest(root)
    subjects = set()
    report_states = Counter()
    total = 0
    for row in iter_mimic_machine_reports(
        root / "machine_measurements.csv", root / "record_list.csv"
    ):
        total += 1
        subjects.add(row["subject_id"])
        report_states[row["report_state"]] += 1
    if total == 0 or total != sum(report_states.values()):
        raise ValueError("MIMIC metadata preflight has no reconciled report rows")
    state_names = (
        "positive_mention", "explicit_negative_mention", "not_mentioned",
        "ambiguous_mention", "missing_report_text",
    )
    return {
        "schema": "TITAN_V45_MIMIC_PAC_METADATA_PREFLIGHT_V1",
        "status": "metadata_only_preflight_no_waveform_read",
        "metadata_source_integrity": integrity,
        "denominators": {
            "paired_metadata_records": total,
            "unique_subjects": len(subjects),
            "report_state_counts": {name: int(report_states[name]) for name in state_names},
        },
        "preperformance_controls": {
            "waveform_files_read": False,
            "waveform_inference_performed": False,
            "model_performance_metrics_computed": False,
            "machine_reports_used_as_clinical_labels": False,
        },
        "privacy": {
            "subject_or_study_identifiers_exported": False,
            "waveform_paths_or_hashes_exported": False,
            "waveforms_or_report_text_exported": False,
        },
    }


def verify_mimic_metadata_sha256_manifest(dataset_root):
    """Verify metadata files against the supplied manifest, without opening waveforms."""
    root = Path(dataset_root).resolve()
    manifest = root / "SHA256SUMS.txt"
    if not manifest.is_file() or manifest.is_symlink():
        raise ValueError("MIMIC source lacks a regular SHA256SUMS.txt")
    manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    required = {
        "LICENSE.txt", "RECORDS", "record_list.csv", "machine_measurements.csv",
        "machine_measurements_data_dictionary.csv", "waveform_note_links.csv",
    }
    entries = {}
    with manifest.open(encoding="ascii", newline="") as stream:
        for line_number, raw_line in enumerate(stream, 1):
            line = raw_line.rstrip("\r\n")
            if len(line) < 67 or not re.fullmatch(r"[0-9a-fA-F]{64}", line[:64]):
                raise ValueError(f"invalid MIMIC SHA256SUMS entry at line {line_number}")
            if line[64:66] not in {"  ", " *"}:
                raise ValueError(f"invalid MIMIC SHA256SUMS separator at line {line_number}")
            name = line[66:]
            if name.startswith("./"):
                name = name[2:]
            relative = PurePosixPath(name)
            if (relative.is_absolute() or ".." in relative.parts or "\\" in name
                    or not relative.parts or name in entries):
                raise ValueError("unsafe or duplicate path in MIMIC SHA256SUMS")
            entries[name] = line[:64].lower()
    if not required.issubset(entries):
        raise ValueError("MIMIC SHA256SUMS lacks required metadata entries")
    metadata_hashes = {}
    verified_bytes = 0
    for name in sorted(required):
        path = root / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError(f"MIMIC metadata file is missing or unsafe: {name}")
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
                size += len(block)
        actual = digest.hexdigest()
        if actual != entries[name]:
            raise ValueError(f"MIMIC metadata hash mismatch: {name}")
        metadata_hashes[name] = actual
        verified_bytes += size
    return {
        "schema": "TITAN_V45_MIMIC_IV_ECG_V1_METADATA_INTEGRITY_V1",
        "dataset_version": "MIMIC-IV-ECG 1.0",
        "source_manifest_sha256": manifest_hash,
        "manifest_entries": len(entries),
        "metadata_files_verified": len(metadata_hashes),
        "metadata_bytes_verified": verified_bytes,
        "metadata_file_sha256": metadata_hashes,
        "waveform_files_verified": False,
        "manifest_origin_independently_authenticated": False,
        "subject_or_study_identifiers_exported": False,
    }


def verify_mimic_sha256_manifest(dataset_root):
    """Verify every path in the official MIMIC-IV-ECG v1.0 SHA256SUMS file."""
    root = Path(dataset_root).resolve()
    manifest = root / "SHA256SUMS.txt"
    if not manifest.is_file() or manifest.is_symlink():
        raise ValueError("MIMIC source lacks a regular SHA256SUMS.txt")
    manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    seen = set()
    verified_bytes = 0
    required_files = {
        "LICENSE.txt", "RECORDS", "record_list.csv", "machine_measurements.csv",
        "machine_measurements_data_dictionary.csv", "waveform_note_links.csv",
    }
    required_hashes = {}
    verified = 0
    with manifest.open(encoding="ascii", newline="") as stream:
        for line_number, raw_line in enumerate(stream, 1):
            line = raw_line.rstrip("\r\n")
            if len(line) < 67 or not re.fullmatch(r"[0-9a-fA-F]{64}", line[:64]):
                raise ValueError(f"invalid MIMIC SHA256SUMS entry at line {line_number}")
            separator = line[64:66]
            if separator not in {"  ", " *"}:
                raise ValueError(f"invalid MIMIC SHA256SUMS separator at line {line_number}")
            name = line[66:]
            if name.startswith("./"):
                name = name[2:]
            relative = PurePosixPath(name)
            if (relative.is_absolute() or ".." in relative.parts or "\\" in name
                    or not relative.parts or name in seen):
                raise ValueError("unsafe or duplicate path in MIMIC SHA256SUMS")
            seen.add(name)
            path = root
            for part in relative.parts:
                path = path / part
                if path.is_symlink():
                    raise ValueError("MIMIC manifest path traverses a symlink")
            if not path.is_file() or not path.resolve().is_relative_to(root):
                raise ValueError("MIMIC manifest path is missing, nonregular or outside the source")
            digest = hashlib.sha256()
            size = 0
            with path.open("rb") as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
                    size += len(block)
            if digest.hexdigest() != line[:64].lower():
                raise ValueError(f"MIMIC source hash mismatch at manifest line {line_number}")
            verified += 1
            verified_bytes += size
            if name in required_files:
                required_hashes[name] = digest.hexdigest()
    if not verified or set(required_hashes) != required_files:
        raise ValueError("MIMIC manifest does not cover the required v1.0 source files")
    return {
        "schema": "TITAN_V45_MIMIC_IV_ECG_V1_SOURCE_INTEGRITY_V1",
        "dataset_version": "MIMIC-IV-ECG 1.0",
        "source_manifest_sha256": manifest_hash,
        "verified_files": verified,
        "verified_bytes": verified_bytes,
        "required_file_sha256": dict(sorted(required_hashes.items())),
        "waveform_records_exported": False,
        "subject_or_study_identifiers_exported": False,
    }
