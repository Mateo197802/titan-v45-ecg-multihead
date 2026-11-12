"""Keep archived-vs-current and previous-native-vs-current replay evidence separate."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path

from titan_v45.contracts.profiles import CANONICAL_PROFILES
from titan_v45.evaluation.replay_diagnostics import (
    _drift,
    _probability_pair,
    binary_residuals,
    ranking_residuals,
)
from titan_v45.evaluation.waveform_reference import (
    _flag,
    _read_private_ledger,
    _unique,
    summarize_selected_union,
)

TAGS = {"P4": "pathology_primary4", "P6": "rhythm_primary6_diagnostic", "P8": "rhythm_primary8"}
NATIVE = {
    "P4": (32448, "02019b832fafecd0c263ea556c70f16fa0a50ccf",
           "592e2bbab96cd03e23caf5ba4c29b746293a0f6e7584ed4b6fc069160c2d5f46"),
    "rhythm": (32461, "cfe6d59fa5cc4be10de0d7c6803fa5208fae0072",
               "123d21f4512b988eb24bcff90b971c62510c547b7f766e059137f072c2d871b4"),
}
ASSETS = {
    "P4": ("backbone-v3ag-pathology.pt", "specialists-v3ag-primary4-calibrated.pt",
           "external-dev-pathology-ptbxl-fold10.tar.zst"),
    "rhythm": ("backbone-v3f-original.pt", "specialists-v3p-e008-primary6-diagnostic.pt",
               "specialists-v3q-primary8-best-candidate.pt", "external-dev-rhythm-chapman-shaoxing.tar.zst"),
}
BASELINE_SHA = "d8e5603a8e3090c17a223ba80f397cee8d99c6f713465ceb9660ce4e17c2566d"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_csv(path, expected):
    raw = path.read_bytes()
    if digest(raw.replace(b"\r\n", b"\n")) != expected:
        raise ValueError("archived table failed its frozen checksum")
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))


def named_scores(old, new, key):
    names = old[0][key].keys()
    if any(row[key].keys() != names for row in (*old, *new)):
        raise ValueError("score class contract changed")
    return {c: _drift(*_probability_pair([r[key][c] for r in old], [r[key][c] for r in new]))
            for c in names}


def native_compare(old, new, branch):
    if old.keys() != new.keys():
        raise ValueError("native replay source-record universe differs")
    comparisons = {}
    specs = {"P4": "primary_scores"} if branch == "P4" else {"P6": "scores", "P8": "scores"}
    for profile, field in specs.items():
        keys = [k for k in old if (field in old[k] if branch == "P4" else profile in old[k])]
        matches = [k for k in keys if (field in new[k] if branch == "P4" else profile in new[k])]
        a, b = ([ledger[k] if branch == "P4" else ledger[k][profile] for k in matches] for ledger in (old, new))
        fields = ("pathology",) if branch == "P4" else ("top1", "labels", "used_fallback")
        comparisons[profile] = {
            "previous_scored": len(keys), "matched_scored": len(matches),
            "previously_scored_missing_now": len(keys)-len(matches),
            "newly_scored": sum((field in v if branch == "P4" else profile in v) for v in new.values())-len(matches),
            "score_differences_by_class": named_scores(a, b, field) if matches else {},
            "decision_changes_by_field": {
                k: sum((set(x[k]) != set(y[k])) if k == "labels" else x[k] != y[k]
                       for x, y in zip(a, b, strict=True)) for k in fields},
        }
    keys = [k for k in old if "auxiliary_scores" in old[k] and "auxiliary_scores" in new[k]]
    comparisons["auxiliary"] = {"matched_scored": len(keys), "score_differences_by_class": named_scores(
        [old[k] for k in keys], [new[k] for k in keys], "auxiliary_scores") if keys else {}}
    return {"source_records": len(old), "workflow_state_changes": sum(
        any(old[k][field] != new[k][field] for field in ("pre", "post")) for k in old),
        "comparisons": comparisons}


def pathology_archived(rows, current, label, threshold):
    old, new = [], []
    for row, key in zip(rows, _unique(rows), strict=True):
        p = float(row["probability"])
        if abs(float(row["threshold"]) - threshold) > 1e-12 or (p >= threshold) != bool(_flag(row["predicted"])):
            raise ValueError("archived P4 call differs from its threshold")
        item = current[key]
        if "primary_scores" not in item:
            continue
        q = item["primary_scores"][label]
        if (q >= threshold) != item["pathology"][label]:
            raise ValueError("current P4 call differs from its threshold")
        old.append(p)
        new.append(q)
    return {"archived_rows": len(rows), "matched_rows": len(old), "missing_scores": len(rows)-len(old),
            "diagnostics": binary_residuals(old, new, threshold) if old else None}


def rhythm_archived(rows, current, profile):
    contract = CANONICAL_PROFILES[TAGS[profile]]
    classes = contract.classes
    p6 = profile == "P6"
    top, prefix = ("pred_label", "prob_") if p6 else ("predicted_label", "membership_prob_")
    keys = _unique(rows)
    matched = [(row, current[key]) for row, key in zip(rows, keys, strict=True) if profile in current[key]]
    if not matched:
        return {"archived_rows": len(rows), "matched_rows": 0, "missing_scores": len(rows), "diagnostics": None}
    old, new, ia, ib = [], [], [], []
    changed_sets = changed_windows = 0
    for r, native in matched:
        item = native[profile]
        if set(item["scores"]) != set(classes) or not set(item["labels"]) <= set(classes):
            raise ValueError("current rhythm decision classes differ from contract")
        historical = {c for c in classes if _flag(r["threshold_pass_"+c])} if p6 else set(
            filter(None, r["predicted_labels"].split("|")))
        if not historical <= set(classes):
            raise ValueError("archived rhythm decision classes differ from contract")
        old.append([float(r[prefix+c]) for c in classes])
        new.append([item["scores"][c] for c in classes])
        ia.append(classes.index(r[top]))
        ib.append(classes.index(item["top1"]))
        changed_sets += historical != set(item["labels"])
        changed_windows += int(r["window_count"]) != native["windows"]
    return {"archived_rows": len(rows), "matched_rows": len(matched), "missing_scores": len(rows)-len(matched),
            "binary_set_changes": changed_sets, "window_count_changes": changed_windows,
            "diagnostics": ranking_residuals(old, new, ia, ib)}


def lineage(directory, branch, expected_assets, expected_manifests, commit):
    runtime = (directory / "commit.txt").read_text().strip()
    raw = (directory / "aggregate.json").read_bytes()
    receipt = json.loads(raw)
    if branch == "P4":
        manifests = {"pathology_primary4_panels.csv": receipt["manifest_sha256_lf"]}
    else:
        manifests = receipt["manifest_sha256_lf"]
    if (runtime != commit or receipt["release_sha256"] != expected_assets
            or manifests != expected_manifests or receipt["weights_or_thresholds_modified"] is not False):
        raise ValueError("replay runner or immutable input contract differs")
    thresholds = receipt["thresholds"]
    thresholds = {"P4": thresholds} if branch == "P4" else thresholds
    profiles = ("P4",) if branch == "P4" else ("P6", "P8")
    expected = {p: dict(zip(CANONICAL_PROFILES[TAGS[p]].classes, CANONICAL_PROFILES[TAGS[p]].thresholds,
                            strict=True)) for p in profiles}
    if thresholds.keys() != expected.keys() or any(
        thresholds[p].keys() != table.keys() or any(
            not abs(thresholds[p][c]-t) <= 1e-12 for c, t in table.items()) for p, table in expected.items()
    ):
        raise ValueError("replay threshold differs from canonical profile")
    return {"runner_commit": runtime, "runner_aggregate_sha256": digest(raw), "release_assets": expected_assets,
            "manifest_sha256_lf": manifests, "device": receipt["device"], "torch": receipt["torch"],
            "morphology_candidate_sha256_lf": receipt["morphology_candidate_sha256_lf"]}


def build(repo, previous_dirs, current_dirs):
    raw = (repo / "outputs/results/revision_20261107/matched_reference_metrics.json").read_bytes()
    if digest(raw.replace(b"\r\n", b"\n")) != BASELINE_SHA:
        raise ValueError("archived comparison anchor mismatch")
    baseline = json.loads(raw)
    assets = {r["name"]: r["sha256"] for r in json.loads((repo / "release-manifest.json").read_bytes())["assets"]}
    refs, manifests = baseline["archived_reference_sha256_lf"], baseline["manifest_sha256_lf"]
    seen, provenance, native = {}, {}, {}
    for branch, (old_job, commit, old_receipt_sha) in NATIVE.items():
        expected_assets = {name: assets[name] for name in ASSETS[branch]}
        expected_manifests = {n: h for n, h in manifests.items() if n.startswith("pathology") == (branch == "P4")}
        previous, now = (d[branch] for d in (previous_dirs, current_dirs))
        old_source = lineage(previous, branch, expected_assets, expected_manifests, commit)
        new_source = lineage(now, branch, expected_assets, expected_manifests, commit)
        if old_source["runner_aggregate_sha256"] != old_receipt_sha:
            raise ValueError("previous replay receipt differs from its published digest")
        if old_source["morphology_candidate_sha256_lf"] != new_source["morphology_candidate_sha256_lf"]:
            raise ValueError("morphology candidate changed between replays")
        old, old_sha = _read_private_ledger(previous/"ledger.jsonl")
        new, new_sha = _read_private_ledger(now/"ledger.jsonl")
        if old_sha != baseline["private_ledger_sha256"][branch]:
            raise ValueError("previous native ledger differs from the sealed reference")
        seen[branch] = new
        provenance[branch] = {
            "previous_job": old_job, "previous": {**old_source, "ledger_sha256": old_sha},
            "current": {**new_source, "ledger_sha256": new_sha},
            "native_ledgers_byte_identical": old_sha == new_sha}
        native[branch] = native_compare(old, new, branch)
    evidence = repo / "outputs/results/external_dev/evidence"

    def read(name):
        return checked_csv(evidence/name, refs[name])

    p4 = CANONICAL_PROFILES[TAGS["P4"]]
    panels = {c: pathology_archived(
        read(f"pathology_primary4_{c}_record_predictions.csv"), seen["P4"], c, t)
        for c, t in zip(p4.classes, p4.thresholds, strict=True)}
    rhythm = {p: rhythm_archived(read(f"rhythm_primary{p[-1]}_record_predictions.csv"), seen["rhythm"], p)
              for p in ("P6", "P8")}
    return {"schema": "TITAN_V45_NOVEMBER_REPLAY_CONTRAST_V1", "job": os.environ.get("SLURM_JOB_ID"),
            "scope": "selected retrospective panels; never a reproduction of the missing original loader",
            "archived_comparison_anchor_sha256": BASELINE_SHA, "archived_reference_sha256_lf": refs,
            "provenance": provenance, "previous_native_versus_current_native": native,
            "archived_predictions_versus_current_native": {"P4": panels, **rhythm},
            "matched_p4_panel_observations": sum(e["matched_rows"] for e in panels.values()),
            "scored_route_union": summarize_selected_union(seen["P4"], seen["rhythm"]),
            "historical_preprocessing_certified": False, "record_identifiers_exported": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ("repo", "previous-p4", "previous-rhythm", "current-p4", "current-rhythm", "output"):
        p.add_argument(f"--{n}", type=Path, required=True)
    a = p.parse_args()
    report = build(a.repo, {"P4": a.previous_p4, "rhythm": a.previous_rhythm},
                   {"P4": a.current_p4, "rhythm": a.current_rhythm})
    with a.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
