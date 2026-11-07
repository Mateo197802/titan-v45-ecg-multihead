"""Audit score-only routing over the union of the released P8 and P4 manifests."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.evaluation.workflow import route_record, summarize_routes

MANIFESTS = Path("data/manifests/external_dev")
RESULTS = Path("outputs/results/external_dev")
P4 = ("ASMI", "LVH", "IMI", "ISC_")


def audit(root: Path) -> tuple[dict, dict]:
    fingerprints = {}

    def read(path: Path) -> bytes:
        raw = (root / path).read_bytes().replace(b"\r\n", b"\n")
        fingerprints[path.as_posix()] = hashlib.sha256(raw).hexdigest()
        return raw

    def rows(path: Path):
        yield from csv.DictReader(read(path).decode("utf-8").splitlines(keepends=True))

    def keys(path: Path, *, panel: bool = False) -> set:
        values = set()
        for row in rows(path):
            key = (row["record_base"], row["pathology"]) if panel else row["record_base"]
            if not row["record_base"] or key in values or (panel and row["pathology"] not in P4):
                raise ValueError("empty, duplicate or unexpected manifest identity")
            values.add(key)
        if not values:
            raise ValueError("empty profile manifest")
        return values

    rhythm_ids = keys(MANIFESTS / "rhythm_primary8_records.csv")
    panels = keys(MANIFESTS / "pathology_primary4_panels.csv", panel=True)
    path_ids = {identity for identity, _ in panels}
    metrics = json.loads(read(RESULTS / "rhythm_primary8_metrics.json"))
    classes = metrics["classes"]
    if len(classes) != 8 or len(set(classes)) != 8 or "NSR" not in classes:
        raise ValueError("invalid P8 class contract")
    thresholds = dict(zip(classes, metrics["thresholds"], strict=True))
    rhythm = {}
    for row in rows(RESULTS / "evidence/rhythm_primary8_record_predictions.csv"):
        identity = row["record_base"]
        if identity not in rhythm_ids or identity in rhythm:
            raise ValueError("P8 score outside inventory or duplicated")
        rhythm[identity] = {name: float(row["membership_prob_" + name]) for name in classes}

    pathology: dict[str, dict] = {}
    for name in P4:
        for row in rows(RESULTS / f"evidence/pathology_primary4_{name}_record_predictions.csv"):
            identity = row["record_base"]
            scores = pathology.setdefault(identity, {})
            if row["pathology"] != name or (identity, name) not in panels or name in scores:
                raise ValueError("P4 score outside panel inventory or duplicated")
            scores[name] = (float(row["probability"]), float(row["threshold"]))

    routes = {key: route_record(rhythm.get(key, {}), thresholds, pathology.get(key, {}))
              for key in sorted(rhythm_ids | path_ids)}
    rhythm_calls = Counter(row["rhythm"]["top1"] for row in routes.values() if row["rhythm"])
    report = {
        "schema": "TITAN_V45_SAVED_WORKFLOW_AUDIT_V1",
        "scope": "released_selected_manifest_union_not_historical_all_input_population",
        "unit": "exact released record_base; not a deduplicated waveform or patient count",
        "denominators": {"p8_records": len(rhythm_ids), "p4_records": len(path_ids),
                         "p4_panel_pairs": len(panels), "exact_overlap": len(rhythm_ids & path_ids)},
        **summarize_routes(routes),
        "p8_pre_top1_counts": dict(sorted(rhythm_calls.items())),
        "p8_nsr_in_predicted_set": sum(bool(row["rhythm"] and "NSR" in row["rhythm"]["labels"])
                                      for row in routes.values()),
        "p8_empty_membership_fallbacks": sum(bool(row["rhythm"] and row["rhythm"]["used_fallback"])
                                            for row in routes.values()),
        "p4_scored_panel_pairs": sum(len(scores) for scores in pathology.values()),
        "p4_records_with_all_four_scores": sum(len(scores) == len(P4) for scores in pathology.values()),
        "other_arrhythmia": "not assessed: no released Other classifier scores",
        "other_pathologies": "not assessed: missing panel scores are not negative or Other",
        "reference_labels_used": False,
        "historical_quarantine_recovered": False,
        "full_workflow_validated": False,
        "independent_validation": False,
        "input_sha256_lf_normalized": fingerprints,
    }
    return report, routes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--private-ledger", type=Path, help="Optional record-level output; keep private")
    args = parser.parse_args()
    report, ledger = audit(args.root)
    args.output.write_bytes((json.dumps(report, indent=2) + "\n").encode())
    if args.private_ledger:
        with args.private_ledger.open("xb") as handle:
            for record, route in ledger.items():
                handle.write((json.dumps({"record_base": record, **route}) + "\n").encode())


if __name__ == "__main__":
    main()
