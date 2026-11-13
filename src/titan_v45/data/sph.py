"""Source-level SPH inventory contracts; no scores or clinical negative labels."""
from __future__ import annotations

import csv
import hashlib
import io
import re
import tarfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import numpy as np

LEADS = ("I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6")
FS_HZ = 500
RECORD_ID = re.compile(r"A[0-9]{5}")
METADATA_COLUMNS = ("ECG_ID", "AHA_Code", "Patient_ID", "Age", "Sex", "N", "Date")


@dataclass(frozen=True)
class SphMetadata:
    patient: str
    samples: int
    statements: tuple[tuple[int, tuple[int, ...]], ...]

    @property
    def primary_codes(self):
        return {code for code, _ in self.statements}


def _csv(text, columns):
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != columns:
        raise ValueError("unexpected SPH CSV header")
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("incomplete SPH CSV row")
        yield row


def read_sph_dictionary(text):
    primary, modifier = {}, {}
    for row in _csv(text, ("Category", "Code", "Description")):
        code = int(row["Code"])
        if code in primary or code in modifier or not row["Description"].strip():
            raise ValueError("duplicate code or missing description")
        group = modifier if row["Category"] == "Modifier" else primary
        group[code] = row["Description"]
    if not primary or not modifier:
        raise ValueError("SPH dictionary has no primary codes or modifiers")
    return primary, modifier


def read_sph_signal_index(text):
    """Read only ECG_ID and sample count for label-blind waveform processing."""
    records = {}
    for row in _csv(text, ("ECG_ID", "N")):
        record, samples = row["ECG_ID"], int(row["N"])
        if not RECORD_ID.fullmatch(record) or samples < 1:
            raise ValueError("invalid SPH signal index row")
        if record in records:
            raise ValueError("duplicate SPH ECG ID in signal index")
        records[record] = samples
    if not records:
        raise ValueError("empty SPH signal index")
    return records


def parse_aha(value, primary, modifier):
    statements = []
    for statement in value.split(";"):
        core, *extra = [int(token) for token in statement.split("+")]
        if (core not in primary or len(set(extra)) != len(extra)
                or any(code not in modifier for code in extra)):
            raise ValueError("invalid SPH primary code or modifier")
        statements.append((core, tuple(sorted(extra))))
    return tuple(statements)


def read_sph_metadata(text, primary, modifier):
    records = {}
    for row in _csv(text, METADATA_COLUMNS):
        record, patient, samples = row["ECG_ID"], row["Patient_ID"].strip(), int(row["N"])
        if record in records:
            raise ValueError("duplicate SPH ECG ID")
        if not RECORD_ID.fullmatch(record) or not patient or samples < 1:
            raise ValueError("invalid SPH ECG ID, patient or sample count")
        records[record] = SphMetadata(patient, samples, parse_aha(row["AHA_Code"], primary, modifier))
    if not records:
        raise ValueError("empty SPH metadata")
    return records


def open_sph_records(path):
    """Stream safe members; never extract archive paths or HDF5 files to disk."""
    with tarfile.open(path, mode="r|*") as archive:
        for member in archive:
            parsed = PurePosixPath(member.name)
            if (parsed.is_absolute() or ".." in parsed.parts or "\\" in member.name
                    or len(parsed.parts) > 2):
                raise ValueError("unexpected SPH archive path")
            if member.isdir():
                continue
            if not member.isfile() or parsed.suffix != ".h5" or not RECORD_ID.fullmatch(parsed.stem):
                raise ValueError("unexpected SPH archive member type")
            if not 0 < member.size <= 2 * 1024 * 1024:
                raise ValueError("unexpected SPH HDF5 member size")
            with archive.extractfile(member) as stream:
                yield parsed.stem, stream.read()


def read_sph_signal(content, samples):
    import h5py

    with h5py.File(io.BytesIO(content), "r") as handle:
        if (list(handle) != ["ecg"] or not isinstance(handle.get("ecg", getlink=True), h5py.HardLink)
                or not isinstance(handle["ecg"], h5py.Dataset)):
            raise ValueError("unexpected SPH HDF5 layout")
        dataset = handle["ecg"]
        if (dataset.is_virtual or dataset.external or dataset.shape != (12, samples)
                or dataset.dtype.kind not in "fi" or dataset.dtype.itemsize > 8):
            raise ValueError("unexpected SPH signal shape, storage or dtype")
        signal = dataset[:]
        if not np.isfinite(signal).all():
            raise ValueError("nonfinite SPH signal")
        return signal, dataset.dtype.str


def inspect_sph_signal_metadata(content, samples):
    """Inspect HDF5 units and raw amplitude without converting or scoring signals."""
    import h5py

    with h5py.File(io.BytesIO(content), "r") as handle:
        dataset = handle["ecg"]
        attrs = {}
        for prefix, values in (("file.", handle.attrs), ("ecg.", dataset.attrs)):
            for key, value in values.items():
                if isinstance(value, bytes):
                    value = value.decode("utf-8", errors="replace")
                elif isinstance(value, np.ndarray):
                    value = value.tolist()
                elif isinstance(value, np.generic):
                    value = value.item()
                attrs[prefix + str(key)] = value
        signal, dtype = read_sph_signal(content, samples)
        values = signal.astype(np.float64)
        return {
            "attributes": attrs,
            "dtype": dtype,
            "signal_sha256_canonical_f64": hashlib.sha256(
                values.astype("<f8", copy=False).tobytes()
            ).hexdigest(),
            "raw_min": float(values.min()),
            "raw_max": float(values.max()),
            "raw_abs_quantiles": np.quantile(np.abs(values), [0.5, 0.95, 0.999]).tolist(),
            "lead_std_median": float(np.median(values.std(axis=1))),
            "lead_std_min": float(values.std(axis=1).min()),
        }


def build_sph_inventory(directory: Path):
    """Summarize source records and repeated patients without exporting identities."""
    primary, modifier = read_sph_dictionary((directory / "code.csv").read_text(encoding="utf-8-sig"))
    metadata = read_sph_metadata((directory / "metadata.csv").read_text(encoding="utf-8-sig"),
                                 primary, modifier)
    patients = Counter(row.patient for row in metadata.values())
    archive = directory / "records.tar.gz"
    seen, by_dtype, flat_channels, duplicate_signals = set(), Counter(), Counter(), Counter()
    signals_ok = 0
    sample_counts = []
    with archive.open("rb") as handle:
        magic = handle.read(2)
    invalid = Counter()
    for key, content in open_sph_records(archive):
        if key in seen:
            raise ValueError("duplicate archive ECG ID")
        seen.add(key)
        if key not in metadata:
            invalid["no_metadata"] += 1
            continue
        try:
            signal, dtype = read_sph_signal(content, metadata[key].samples)
        except (ValueError, OSError):
            invalid["invalid_hdf5_shape_dtype_or_signal"] += 1
            continue
        signals_ok += 1
        by_dtype[dtype] += 1
        flat_channels[int(np.count_nonzero(np.ptp(signal.astype(np.float64), axis=1) == 0))] += 1
        canonical = signal.astype("<f8", copy=False)
        duplicate_signals[hashlib.sha256(canonical.tobytes()).digest()] += 1
        sample_counts.append(signal.shape[-1])
    return {
        "schema": "TITAN_V45_SPH_V1_SOURCE_INVENTORY",
        "scope": "source_integrity_and_statement_support_not_model_performance",
        "archive_format": "gzip_container" if magic == b"\x1f\x8b" else "non_gzip_tar_readable",
        "metadata_ecgs": len(metadata), "metadata_patients": len(patients),
        "patients_with_repeated_ecgs": sum(n > 1 for n in patients.values()),
        "archive_ecgs": len(seen), "valid_signal_ecgs": signals_ok,
        "metadata_without_signal": len(metadata.keys() - seen),
        "technical_failures": dict(sorted(invalid.items())),
        "signal_dtypes": dict(sorted(by_dtype.items())),
        "records_by_flat_lead_count": {str(k): v for k, v in sorted(flat_channels.items())},
        "exact_duplicate_signal_groups": sum(n > 1 for n in duplicate_signals.values()),
        "exact_duplicate_signal_excess_records": sum(n - 1 for n in duplicate_signals.values()),
        "native_fs_hz": FS_HZ, "lead_order": list(LEADS),
        "min_samples": min(sample_counts, default=None), "max_samples": max(sample_counts, default=None),
        "records_with_repeated_primary_statements": sum(
            len(row.statements) > len(row.primary_codes) for row in metadata.values()
        ),
        "repeated_primary_statement_excess": sum(
            len(row.statements) - len(row.primary_codes) for row in metadata.values()
        ),
        "primary_statement_counts": dict(sorted(Counter(
            str(code) for record in metadata.values() for code in record.primary_codes
        ).items(), key=lambda item: int(item[0]))),
        "primary_dictionary_entries": len(primary), "modifier_dictionary_entries": len(modifier),
        "record_or_patient_identifiers_exported": False,
        "model_inference_performed": False,
    }
