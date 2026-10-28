"""Compute a patient-cluster sensitivity analysis using upstream PTB-XL metadata."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.evaluation.revision_report import BinaryPanel, cluster_bootstrap


def patient_sensitivity(root: Path, metadata: Path, *, n_bootstrap: int, seed: int) -> dict:
    with metadata.open(encoding="utf-8", newline="") as handle:
        source = list(csv.DictReader(handle))
    by_record = {}
    for row in source:
        key = "ptbxl_" + row["ecg_id"]
        if key in by_record:
            raise ValueError("duplicate ecg_id in patient metadata")
        by_record[key] = row
    panels, cluster_ids, selected, fingerprints = {}, {}, {}, {}
    for label in ("ASMI", "LVH", "IMI", "ISC_"):
        relative = f"outputs/results/external_dev/evidence/pathology_primary4_{label}_record_predictions.csv"
        path = root / relative
        fingerprints[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        keys = []
        for row in rows:
            record_id = row["record_id"]
            if record_id not in by_record or not by_record[record_id]["patient_id"]:
                raise ValueError("all evaluated ECGs require an upstream patient mapping")
            key = (row["source"], record_id)
            keys.append(key)
            cluster_ids[key] = by_record[record_id]["patient_id"]
            selected[record_id] = by_record[record_id]
        panels[label] = BinaryPanel(
            tuple(keys), np.array([int(row["target"]) for row in rows]),
            np.array([int(row["predicted"]) for row in rows]),
        )
    return {
        "schema": "TITAN_V45_P4_PATIENT_CLUSTER_SENSITIVITY_V1",
        "scope": "saved_predictions_with_recovered_upstream_patient_metadata",
        "panel_rows": sum(len(panel.keys) for panel in panels.values()),
        "unique_ecgs": len(selected),
        "unique_patients": len(set(cluster_ids.values())),
        "fold_counts": dict(Counter(row["strat_fold"] for row in selected.values())),
        "metadata_sha256": hashlib.sha256(metadata.read_bytes()).hexdigest(),
        "prediction_sha256": fingerprints,
        "bootstrap": cluster_bootstrap(panels, cluster_ids=cluster_ids, n_bootstrap=n_bootstrap, seed=seed),
        "limitations": [
            "Patient identifiers originate from the supplied upstream metadata, not from names inferred from ECGs.",
            "This does not certify patient-level training/calibration isolation; original manifests remain required.",
            "Sensitivity analysis preserves selected-panel sampling; it does not restore natural prevalence.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--ptbxl-metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    payload = patient_sensitivity(args.root, args.ptbxl_metadata, n_bootstrap=args.n_bootstrap, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {payload['unique_ecgs']} ECG mappings / {payload['unique_patients']} patients")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
