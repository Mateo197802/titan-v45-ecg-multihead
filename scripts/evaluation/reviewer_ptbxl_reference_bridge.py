"""Score and evaluate the authorized PTB-XL cache without class-based enrollment."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from compare_reviewer_baseline import digest
from freeze_reviewer_selective_policy import components, jsonl
from reviewer_pathology_other import identity, read_references, reference, write_new


def enrollment(metadata, expected):
    result = {}
    with metadata.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            fold = int(row["strat_fold"])
            if fold == 10:
                continue
            path = PurePosixPath(row["filename_lr"])
            if (not 1 <= fold <= 9 or len(path.parts) != 3 or path.parts[0] != "records100"
                    or ".." in path.parts or "\\" in str(path)):
                raise ValueError("invalid fold or record path")
            key = identity("ptbxl", path.as_posix())
            if key in result:
                raise ValueError("duplicate eligible metadata row")
            result[key] = (path.as_posix(), fold)
    if len(result) != expected:
        raise ValueError("unfiltered metadata denominator changed")
    return result


def inventory_rows(inventory, enrolled):
    rows = {}
    for row in inventory["rows"]:
        if row["task"] != "pathology" or row["source"] != "ptbxl":
            continue
        key = row["identity_hash"]
        if key in rows or enrolled.get(key) != (row["relative_record"], row["fold"]):
            raise ValueError("inventory contains a duplicate, wrong or forbidden fold")
        rows[key] = row
    return rows


def score_stage(a, protocol, enrolled, inventory, hashes):
    import torch

    from titan_v45.data.reconstructed import prepare_p4_record, prepare_rhythm_record
    from titan_v45.models.frozen_pathology import BACKBONE as P4_BACKBONE
    from titan_v45.models.frozen_pathology import SPECIALIST as P4_SPECIALIST
    from titan_v45.models.frozen_pathology import FrozenPathology, verified_assets
    from titan_v45.models.frozen_rhythm import (
        BACKBONE,
        HEADS,
        FrozenRhythm,
        aggregate_rhythm,
        load_recorded_event_extractor,
    )

    if not torch.cuda.is_available():
        raise RuntimeError("CEDIA GPU allocation is required for scoring")
    src = a.repo / "scripts/specialist_experiments/extract_features.py"
    spec = importlib.util.spec_from_file_location("reviewer_ptbxl_extract", src)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load pinned extractor")
    stage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage)
    device = "cuda"
    assets, asset_sha = verified_assets(a.repo, a.assets, {BACKBONE, *HEADS.values(), P4_BACKBONE, P4_SPECIALIST})
    contract = json.loads((a.repo / "outputs/models/heads/global_head_contracts.json").read_bytes())
    morphology = stage._safe_morphology(a.repo)
    path = FrozenPathology(assets, contract, device)
    event = load_recorded_event_extractor(a.repo / "docs/provenance/recovered-original-sources-20261029.zip")
    rhythm = FrozenRhythm(assets, contract, event, device)
    thresholds = stage._baseline_thresholds(a.repo, path)
    raw = a.data_root / "00_FUENTES_FISICAS_RAW" / "ptb-xl"
    flow = {name: Counter() for name in ("P6", "P8", "P4")}
    pending = []

    def emit(stream, key, profiles):
        for name, value in profiles.items():
            flow[name][value["status"]] += 1
        stream.write(json.dumps({"key": key, "profiles": profiles}, separators=(",", ":"), allow_nan=False)+"\n")

    def flush(stream):
        available_p4 = [(key, p4) for key, p4, _ in pending if p4 is not None]
        p4_scores = dict(zip((k for k, _ in available_p4), path([v for _, v in available_p4]), strict=True)
                         ) if available_p4 else {}
        r_windows = [sample for _, _, windows in pending if windows for sample in windows]
        r_logits = rhythm(r_windows)[0] if r_windows else None
        offset = 0
        for key, p4, windows in pending:
            profiles = {}
            if p4 is None:
                profiles["P4"] = {"status": "technical_exclusion"}
            else:
                scores, auxiliary = p4_scores[key]
                profiles["P4"] = {"status": "scored", "scores": scores, "auxiliary": auxiliary,
                                  "labels": [c for c, p in scores.items() if p >= thresholds["P4"][c]]}
            for r in ("P6", "P8"):
                result = aggregate_rhythm(r_logits[r][offset:offset+len(windows)], thresholds[r], profile=r) if windows else {}
                profiles[r] = {"status": "scored" if windows else "technical_exclusion", **result}
            offset += len(windows) if windows else 0
            emit(stream, key, profiles)
        pending.clear()

    with a.ledger.open("x", encoding="utf-8") as stream:
        for completed, (key, (relative, _)) in enumerate(enrolled.items(), start=1):
            row = inventory.get(key)
            if row is None or row["excluded_reason"]:
                status = "not_in_authorized_preflight" if row is None else "preflight_excluded"
                emit(stream, key, {name: {"status": status} for name in flow})
            else:
                signal = stage._signal_path(raw, relative)
                if digest(signal) != row["signal_sha256"]:
                    raise ValueError("waveform checksum differs from authorized preflight")
                record = signal.with_suffix("")
                try:
                    p4 = prepare_p4_record(record, morphology)
                except (OSError, ValueError):
                    p4 = None
                try:
                    windows = prepare_rhythm_record(record, morphology)
                except (OSError, ValueError):
                    windows = None
                pending.append((key, p4, windows))
                if len(pending) >= protocol["waveform_batch_ecgs"]:
                    flush(stream)
            if completed % 1000 == 0:
                print(json.dumps({"eligible_metadata_processed": completed, "flow": flow}), flush=True)
        flush(stream)
    if any(sum(c.values()) != len(enrolled) or c["scored"] == 0 for c in flow.values()):
        raise ValueError("incomplete scoring denominator or no scored records")
    write_new(a.receipt, {"job": os.environ.get("SLURM_JOB_ID"), "scope": protocol["scope"],
                          "input_hashes": hashes, "immutable_model_assets_sha256": asset_sha,
                          "ledger_sha256": digest(a.ledger), "metadata_ecgs": len(enrolled), "flow": flow,
                          "thresholds": thresholds, "references_accessed_for_scoring": False, "fold10_scored": False,
                          "preprocessor_sha256": digest(a.repo / "src/titan_v45/data/reconstructed.py"),
                          "runtime": {"torch": torch.__version__, "gpu": torch.cuda.get_device_name(0)}})


def observe_endpoint(rows, refs, clusters, profile, label, code, auxiliary, seed, metrics, bootstrap, rank, threshold):
    flow, truth, probs, calls, group_ids = Counter(), [], [], [], []
    for key, ref in refs.items():
        r = rows[key][profile]
        state = reference(ref, {code})
        flow[f'{state}:{r["status"]}'] += 1
        if r["status"] != "scored" or state not in {"positive", "control"}:
            continue
        truth.append(int(state == "positive"))
        probs.append(r["auxiliary" if auxiliary else "scores"][label])
        if not auxiliary:
            calls.append(int(label in r["labels"]))
        group_ids.append(clusters[key])
    result = {"scp_statement": code, "reference_and_scoring_flow": dict(flow), "known_scored": len(truth)}
    if not truth or sum(truth) in {0, len(truth)}:
        return {**result, "status": "insufficient_matched_polarities"}
    if auxiliary:
        return {**result, "status": "rank_only", "metrics": rank(zip(probs, truth, strict=True))}
    if profile != "P8" and calls != [int(p >= threshold) for p in probs]:
        raise ValueError("stored threshold decision disagrees")
    values = metrics(truth, calls, probs)
    n = values["tn"] + values["fn"]
    return {**result, "status": "evaluated", "metrics": {**values, "npv": values["tn"]/n if n else None},
            "intervals": bootstrap(truth, calls, probs, group_ids, seed=seed["seed"],
                                   n_bootstrap=seed["replicates"], confidence=seed["confidence"])}


def evaluate_stage(a, protocol, enrolled, inventory, hashes):
    from audit_reviewer_auxiliary_support import rank_metrics

    from titan_v45.evaluation.revision_report import binary_metrics
    from titan_v45.evaluation.specialist_heads import bootstrap_binary_metrics

    receipt = json.loads(a.receipt.read_bytes())
    if (not a.expected_receipt_sha256 or digest(a.receipt) != a.expected_receipt_sha256
            or receipt["ledger_sha256"] != digest(a.ledger) or receipt["input_hashes"] != hashes
            or receipt["references_accessed_for_scoring"] is not False or receipt["fold10_scored"] is not False):
        raise ValueError("missing or invalid frozen score seal")
    refs, groups, reserved = read_references(a.source / "ptbxl_database.csv", protocol["metadata_rows_total"])
    raw = list(jsonl(a.ledger))
    rows = {r["key"]: r["profiles"] for r in raw}
    if len(rows) != len(raw) or rows.keys() != enrolled.keys() or refs.keys() != enrolled.keys():
        raise ValueError("eligible ECG denominator mismatch")
    if {p: dict(Counter(r[p]["status"] for r in rows.values())) for p in ("P6", "P8", "P4")} != receipt["flow"]:
        raise ValueError("profile scoring flow disagrees with sealed receipt")
    clusters = components({"ecg_id": k, "patient_id": g[1], "signal_sha256_canonical_f64":
                          inventory[k]["signal_sha256"] if k in inventory else "absent:"+k} for k, g in groups.items())
    by_fold = defaultdict(Counter)
    for key, (fold, _) in groups.items():
        by_fold[str(fold)]["metadata"] += 1
        for p, r in rows[key].items():
            by_fold[str(fold)][f'{p}:{r["status"]}'] += 1
    endpoints = {}
    for p, subset, auxiliary in (("P6", "p6_p8_reference_bridge", False), ("P8", "p6_p8_reference_bridge", False),
                                 ("P4", "p4_statement_endpoints", False), ("P4", "p4_auxiliary_rank_only", True)):
        for label, code in protocol[subset].items():
            endpoints[f"{p}:{label}"] = observe_endpoint(
                rows, refs, clusters, p, label, code, auxiliary, protocol["statistics"], binary_metrics,
                bootstrap_binary_metrics, rank_metrics, receipt["thresholds"][p].get(label))
    write_new(a.output, {"job": os.environ.get("SLURM_JOB_ID"), "scope": protocol["scope"],
                         "scoring_receipt_sha256": a.expected_receipt_sha256, "metadata_ecgs": len(enrolled),
                         "metadata_patient_ids_unique": len({g for _, g in groups.values()}),
                         "fold10_metadata_rows_count_only": reserved, "available_preflight_rows": len(inventory),
                         "flow_by_official_fold": dict(by_fold), "endpoints": endpoints, "reference": protocol["reference"],
                         "independent_validation": False, "record_identifiers_exported": False})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=("score", "evaluate"))
    for n in ("repo", "source", "data-root", "assets", "protocol", "inventory", "ledger", "receipt", "output"):
        p.add_argument(f"--{n}", type=Path, required=True)
    p.add_argument("--expected-receipt-sha256")
    a = p.parse_args()
    protocol = json.loads(a.protocol.read_bytes())
    meta = a.source / "ptbxl_database.csv"
    hashes = {"protocol_sha256": digest(a.protocol)}
    for field, path in (("metadata_sha256", meta), ("dictionary_sha256", a.source/"scp_statements.csv"),
                        ("inventory_sha256", a.inventory)):
        if digest(path) != protocol[field]:
            raise ValueError(f"authorized source seal differs: {field}")
        hashes[field] = protocol[field]
    enrolled = enrollment(meta, protocol["eligible_metadata_rows"])
    inventory = inventory_rows(json.loads(a.inventory.read_bytes()), enrolled)
    (score_stage if a.stage == "score" else evaluate_stage)(a, protocol, enrolled, inventory, hashes)


if __name__ == "__main__":
    main()
