"""Count CODE signal boundary patterns without loading labels or probabilities."""
from __future__ import annotations

import argparse
import csv
import json
import tempfile
from collections import Counter
from pathlib import Path

import h5py
import numpy as np
from code15_io import PROTOCOL, digest
from evaluate_code15 import selected, verified_hdf5

LIMB_NAMES = ("III", "aVR", "aVL", "aVF")
LIMB_COEFFICIENTS = np.array([[-1, 1], [-.5, -.5], [1, -.5], [-.5, 1]]).T


def border_counts(trace):
    if not np.isfinite(trace).all():
        return "nonfinite", None, None
    nonzero = np.flatnonzero(np.any(trace, axis=1))
    if not nonzero.size:
        return "all_zero", None, None
    left, right = int(nonzero[0]), len(trace) - 1 - int(nonzero[-1])
    return "finite_nonzero", left, right


def limb_consistency(trace):
    lead_i, lead_ii, lead_iii, avr, avl, avf = trace[:, :6].astype(np.float64).T
    derived = np.stack((lead_ii - lead_i, -(lead_i + lead_ii) / 2,
                        (lead_i - lead_iii) / 2, (lead_ii + lead_iii) / 2), axis=1)
    residual = np.max(np.abs(trace[:, 2:6] - derived), axis=0)
    scale = np.max(np.abs(trace[:, :6]))
    return residual <= (1e-9 + 1e-6 * scale)


def limb_order_diagnostic(trace):
    observed = trace[:, 2:6].astype(np.float64)
    inputs = trace[:, :2].astype(np.float64)
    coefficients = np.linalg.lstsq(inputs, observed, rcond=None)[0].T
    predicted = inputs @ LIMB_COEFFICIENTS
    denom = np.linalg.norm(observed, axis=0).clip(1e-8)
    hypotheses = np.column_stack((predicted, -predicted))
    residual = np.linalg.norm(hypotheses[:, :, None] - observed[:, None, :], axis=0) / denom
    return coefficients, residual[np.arange(4), np.arange(4)], np.argmin(residual, axis=0)


def run(code, evaluation, output):
    protocol = json.loads(PROTOCOL.read_bytes())
    if (digest(code / "record.json") != protocol["catalog_sha256"]
            or digest(code / "exams.csv") != protocol["metadata_sha256"]):
        raise ValueError("frozen publisher input mismatch")
    receipt = evaluation / "code15_evaluation_receipt.json"
    scores = evaluation / "private_scores.npz"
    results = json.loads(receipt.read_bytes())
    if digest(scores) != results["private_scores_sha256"]:
        raise ValueError("scored ECG membership checksum mismatch")
    with np.load(scores, allow_pickle=False) as membership:
        scored = set(map(int, membership["exams"]))
    catalog = json.loads((code / "record.json").read_bytes())
    summaries, amplitude, total_scored = {}, {}, 0
    for name, expected in results["archive_sha256"].items():
        if digest(code / name) != expected:
            raise ValueError("scored archive checksum mismatch")
        trace_name = Path(name).with_suffix(".hdf5").name
        with (code / "exams.csv").open(encoding="utf-8-sig", newline="") as stream:
            keys = {int(row["exam_id"]) for row in csv.DictReader(stream)
                    if row["trace_file"] == trace_name and selected(row["patient_id"].strip())}
        summary, limb_rows, amplitudes = Counter(), Counter(), {False: [], True: []}
        coefficients, normalized, best = [], [], Counter()
        with tempfile.TemporaryDirectory() as temp:
            h5path = verified_hdf5(code, name, catalog, Path(temp))
            with h5py.File(h5path, "r") as h5:
                id_key, trace_key = next(pair for pair in (("exam_id", "tracings"), ("id_exam", "signal"))
                                         if set(pair) <= h5.keys())
                for index, exam in enumerate(np.asarray(h5[id_key]).reshape(-1)):
                    if int(exam) not in keys:
                        continue
                    in_scores = int(exam) in scored
                    total_scored += in_scores
                    trace = h5[trace_key][index]
                    state, left, right = border_counts(trace)
                    summary[(in_scores, state, left, right)] += 1
                    if state == "finite_nonzero":
                        consistent = limb_consistency(trace)
                        limb_rows[(in_scores, "all_four_relations")] += bool(consistent.all())
                        for lead, passed in zip(LIMB_NAMES, consistent, strict=True):
                            limb_rows[(in_scores, lead)] += bool(passed)
                        amplitudes[in_scores].append(float(np.max(np.ptp(trace, axis=0))))
                        if in_scores:
                            fitted, residual, nearest = limb_order_diagnostic(trace)
                            coefficients.append(fitted)
                            normalized.append(residual)
                            for index, choice in enumerate(nearest):
                                best[(LIMB_NAMES[index], ("-" if choice >= 4 else "") + LIMB_NAMES[choice % 4])] += 1
        if sum(summary.values()) != len(keys):
            raise ValueError("padding-audit cohort membership mismatch")
        summaries[name] = [
            {"scored": included, "status": status, "zero_left": left, "zero_right": right, "n_ecg": count}
            for (included, status, left, right), count in sorted(summary.items(), key=lambda item: (-item[1], item[0]))
        ]
        amplitude[name] = {"groups": [
            {"scored": included, "n_finite_nonzero": len(values),
             "n_limb_relation_consistent": {lead: limb_rows[(included, lead)]
                                            for lead in (*LIMB_NAMES, "all_four_relations")},
             "max_lead_peak_to_peak_p05_p50_p95_native_units": np.quantile(values, [.05, .5, .95]).tolist()}
            for included, values in amplitudes.items() if values
        ]}
        if coefficients:
            amplitude[name]["scored_limb_hypothesis_test"] = {
                "ordered_targets": LIMB_NAMES,
                "median_fitted_coefficients_from_I_II": np.median(coefficients, axis=0).tolist(),
                "normalized_identity_residual_p05_p50_p95": np.quantile(normalized, [.05, .5, .95], axis=0).tolist(),
                "nearest_signed_limb_hypothesis_counts": {
                    name: {target: count for (source, target), count in best.items() if source == name}
                    for name in LIMB_NAMES
                },
            }
    if total_scored != results["n_ecg"] or len(scored) != results["n_ecg"]:
        raise ValueError("padding-audit scored membership mismatch")
    report = {"scope": "SIGNAL_BOUNDARY_AUDIT_NO_OUTCOMES", "labels_or_probabilities_loaded": False,
              "evaluation_receipt_sha256": digest(receipt), "n_scored_verified": total_scored,
              "per_archive_boundary_counts": summaries, "per_archive_limb_and_amplitude": amplitude,
              "physical_units_certified": False}
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("code", "evaluation", "output"):
        parser.add_argument(field, type=Path)
    args = parser.parse_args()
    run(args.code, args.evaluation, args.output)
