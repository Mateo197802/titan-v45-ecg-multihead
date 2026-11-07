"""Account for P4 selected records against official PTB-XL metadata, not run history."""
from __future__ import annotations

import csv
import hashlib
import io
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation

from titan_v45.evaluation.revision_report import _load

PTBXL_METADATA_SHA256 = "7600de9c1b27d181d850b3c6038a35d7c3ddb6bb33b702e3a20252a6859d216b"
P4_PANELS = ("ASMI", "LVH", "IMI", "ISC_")


def _positive_integer(value):
    try:
        number = Decimal(value)
        if number.is_finite() and 0 < number <= 10**12 and number == number.to_integral_value():
            return int(number)
    except (InvalidOperation, TypeError):
        pass
    raise ValueError("invalid official ECG, patient or fold field")


def compare_fold_coverage(metadata, panels):
    records, folds, patient_folds = {}, defaultdict(set), defaultdict(set)
    for row in metadata:
        record = f"ptbxl_{_positive_integer(row['ecg_id'])}"
        patient = _positive_integer(row["patient_id"])
        fold = _positive_integer(row["strat_fold"])
        if fold > 10 or record in records:
            raise ValueError("invalid official fold or duplicate ECG")
        records[record] = (patient, fold)
        folds[fold].add(record)
        patient_folds[patient].add(fold)
    if not panels or any(not keys or len(set(keys)) != len(keys) for keys in panels.values()):
        raise ValueError("empty panel or duplicate ECG within panel")
    selected = Counter(key for keys in panels.values() for key in keys)
    if not selected.keys() <= records.keys():
        raise ValueError("selected ECG missing from official metadata")
    if not selected.keys() <= folds[10]:
        raise ValueError("selected ECG outside official fold 10")

    def patient_set(keys):
        return {records[key][0] for key in keys}

    selected_patients = patient_set(selected)
    other_fold10 = folds[10] - selected.keys()
    fold10_patients = patient_set(folds[10])
    return {
        "official_dataset": {"ecgs": len(records), "patients": len(patient_folds)},
        "official_folds": {
            str(fold): {"ecgs": len(folds[fold]), "patients": len(patient_set(folds[fold]))}
            for fold in range(1, 11)
        },
        "selected_p4": {"ecgs": len(selected), "patients": len(selected_patients),
                        "panel_observations": sum(selected.values())},
        "selected_panels": {name: {"ecgs": len(keys), "patients": len(patient_set(keys))}
                            for name, keys in panels.items()},
        "selected_ecg_counts_by_panel_memberships": {
            str(n): count for n, count in sorted(Counter(selected.values()).items())
        },
        "official_fold10_not_in_selected_p4": {
            "ecgs": len(other_fold10),
            "patients_with_no_selected_ecg": len(fold10_patients - selected_patients),
            "ecgs_from_already_selected_patients": sum(
                records[key][0] in selected_patients for key in other_fold10
            ),
        },
        "selected_patient_overlap_with_official_folds_1_to_9": sum(
            bool(patient_folds[patient] - {10}) for patient in selected_patients
        ),
        "patients_assigned_multiple_official_folds": sum(
            len(patient_fold_set) > 1 for patient_fold_set in patient_folds.values()
        ),
        "historical_exclusion_reasons_known": False,
        "historical_checkpoint_training_isolation_established": False,
        "historical_parent_population_recovered": False,
    }


def build_fold_coverage(repo, metadata):
    data = metadata.read_bytes()
    fingerprint = hashlib.sha256(data).hexdigest()
    if fingerprint != PTBXL_METADATA_SHA256:
        raise ValueError("unexpected PTB-XL v1.0.3 metadata SHA-256")
    references = {}
    panels = {label: tuple(row["record_id"] for row in _load(
        repo, f"pathology_primary4_{label}_record_predictions.csv", references,
    )) for label in P4_PANELS}
    rows = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""))
    return {
        "schema": "TITAN_V45_P4_OFFICIAL_FOLD_COVERAGE_V1",
        "scope": "official_ptbxl_fold_universe_not_historical_candidate_or_training_manifest",
        "metadata_sha256": fingerprint,
        "reference_sha256_lf": {
            name: values["sha256_lf_normalized"] for name, values in references.items()
        },
        **compare_fold_coverage(rows, panels),
    }
