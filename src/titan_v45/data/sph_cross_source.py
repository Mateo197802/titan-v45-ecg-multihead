"""Label-blind signal-signature comparison with retained release waveforms."""
from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from titan_v45.data.reconstructed import prepare_p4_record
from titan_v45.data.sph import open_sph_records, read_sph_signal, read_sph_signal_index
from titan_v45.data.sph_waveform import prepare_sph_waveform


def _signature_morphology(_signal, *, fs):
    if fs != 125:
        raise ValueError("unexpected signature preprocessing sample rate")
    return np.zeros(10, dtype=np.float32)


def normalized_signature(signal):
    """Hash quantized, source-preprocessed first ten seconds without class data."""
    values = np.asarray(signal, dtype="<f4")
    if values.shape != (12, 1250) or not np.isfinite(values).all():
        raise ValueError("unexpected normalized waveform signature input")
    quantized = np.round(values, decimals=3).astype("<f4", copy=False)
    return hashlib.sha256(quantized.tobytes()).hexdigest()


def _signal_index(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"ECG_ID", "N"}.issubset(reader.fieldnames or ()):
            raise ValueError("signal metadata lacks ECG_ID or N")
        text = "ECG_ID,N\n" + "".join(f"{row['ECG_ID']},{row['N']}\n" for row in reader)
    return read_sph_signal_index(text)


def _record_bases(root):
    for header in sorted(Path(root).rglob("*.hea")):
        base = header.with_suffix("")
        if base.with_suffix(".dat").is_file() or base.with_suffix(".mat").is_file():
            yield base


def audit_cross_source_signatures(source: Path, release_root: Path):
    """Screen SPH against only the retained Chapman/Shaoxing and PTB-XL releases."""
    source_index = _signal_index(source / "metadata.csv")
    signatures = defaultdict(list)
    failures = Counter()
    sph_records = 0
    for record_id, content in open_sph_records(source / "records.tar.gz"):
        samples = source_index.get(record_id)
        if samples is None:
            failures["sph_no_metadata"] += 1
            continue
        try:
            signal, _ = read_sph_signal(content, samples)
            prepared = prepare_sph_waveform(
                signal, _signature_morphology, branch="P4"
            )[0][0]
            signatures[normalized_signature(prepared)].append({
                "source": "SPH",
                "record_id": record_id,
            })
            sph_records += 1
        except (ValueError, OSError) as exc:
            failures[f"sph_{type(exc).__name__}"] += 1

    retained = {
        "Chapman-Shaoxing-Ningbo": (
            release_root / "data/external_dev/extracted/rhythm/"
            "external-dev-rhythm-chapman-shaoxing/records"
        ),
        "PTB-XL-fold10": (
            release_root / "data/external_dev/extracted/pathology/"
            "external-dev-pathology-ptbxl-fold10/records"
        ),
    }
    source_counts = {}
    for source_name, directory in retained.items():
        if not directory.is_dir():
            raise FileNotFoundError(f"retained waveform source is unavailable: {source_name}")
        count = 0
        for base in _record_bases(directory):
            try:
                prepared, _, _ = prepare_p4_record(base, _signature_morphology)
                signatures[normalized_signature(prepared)].append({
                    "source": source_name,
                    "record_id": base.name,
                })
                count += 1
            except (ValueError, OSError) as exc:
                failures[f"{source_name}_{type(exc).__name__}"] += 1
        source_counts[source_name] = count

    cross_pairs = Counter()
    candidate_rows = []
    candidate_groups = 0
    for digest, rows in signatures.items():
        present = sorted({row["source"] for row in rows})
        if len(present) < 2:
            continue
        candidate_groups += 1
        for index, left in enumerate(present):
            for right in present[index + 1:]:
                cross_pairs[f"{left}|{right}"] += sum(
                    row["source"] == left for row in rows
                ) * sum(row["source"] == right for row in rows)
        candidate_rows.append({
            "signature_sha256": digest,
            "matches": rows,
        })

    return {
        "schema": "TITAN_V45_SPH_RETAINED_SOURCE_SIGNATURE_AUDIT_V1",
        "scope": "label_blind_quantized_preprocessed_waveform_signature_screen",
        "signature": "source-backed first 10 seconds, 12x1250, per-lead standardized, rounded to 0.001",
        "sph_records_compared": sph_records,
        "retained_source_records_compared": source_counts,
        "candidate_signature_groups_crossing_sources": candidate_groups,
        "cross_source_record_pairs_by_source": dict(sorted(cross_pairs.items())),
        "technical_failures": dict(sorted(failures.items())),
        "record_or_patient_identifiers_exported": False,
        "candidate_pairs_need_manual_signal_level_confirmation": bool(candidate_rows),
        "not_compared": [
            "historical V3F/V3AG pretraining and fine-tuning inputs",
            "unreleased ECGs outside retained Chapman/Shaoxing/Ningbo and PTB-XL fold-10 packages",
        ],
        "independence_certified": False,
    }, candidate_rows
