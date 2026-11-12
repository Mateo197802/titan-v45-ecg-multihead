"""Run a frozen, enriched-cohort clinical territory comparison on CEDIA."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from compare_reviewer_baseline import digest
from evaluate_reviewer_closure_ludb import endpoint_metrics
from freeze_reviewer_selective_policy import components, jsonl
from reviewer_pathology_other import probabilities
from score_reviewer_closure_ludb import sha256, source_manifest, write_new

TRANSPORT_SHA256 = "3975bb5a8f2bcade7f559146d1c3f30a5553728b8ac94d84f40c4cec3c4d9db2"
ARCHIVE_SHA256 = "61e00fc9f38a391fc2a0d757dfa6a02a3f915ad7f0095f747e9c44df395371d3"
ENDPOINTS = ("ASMI", "IMI", "ALMI", "ILMI")


def verify_inputs(args):
    if digest(args.config) != TRANSPORT_SHA256:
        raise ValueError("unsealed PTB Diagnostic transport config")
    config = json.loads(args.config.read_bytes())
    if digest(args.audit / "aggregate.json") != config["reference_eligibility_receipt_sha256"]:
        raise ValueError("unsealed source eligibility audit")
    if digest(args.other_model) != config["pathology_other_model_sha256"]:
        raise ValueError("PTB-XL head fit checksum mismatch")
    fit = json.loads(args.other_fit_receipt.read_bytes())
    model = json.loads(args.other_model.read_bytes())
    if (fit["private_model_sha256"] != config["pathology_other_model_sha256"]
            or str(fit["job"]) != str(config["pathology_other_fit_job"])
            or fit["held_outcomes_evaluated"] is not False or fit["binding"] != model["binding"]):
        raise ValueError("different or unsealed complementary model fit")
    names = (args.audit / "RECORDS").read_bytes()
    manifest = (args.audit / "publisher-SHA256SUMS.txt").read_bytes()
    checks = source_manifest(manifest.decode("ascii"))
    entries = names.decode("ascii").splitlines()
    if (sha256(names) != checks["RECORDS"] or len(entries) != config["all_source_records"]
            or len(set(entries)) != len(entries)
            or any(not re.fullmatch(r"patient[0-9]{3}/[A-Za-z0-9_-]+", k) for k in entries)):
        raise ValueError("invalid publisher cohort index")
    return config, model, entries, checks, names, manifest


def verified_record(z, prefix, key, checks, work):
    head = key + ".hea"
    header = z.read(prefix + head)
    if sha256(header) != checks[head]:
        raise ValueError("publisher header digest differs")
    count = int(header.splitlines()[0].split()[1])
    if count != 15:
        raise ValueError("unexpected PTB channel count")
    names = sorted({row.split()[0].decode("ascii") for row in header.splitlines()[1:count+1]})
    if any(not re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9]+", x) for x in names):
        raise ValueError("unsafe waveform filename in provider header")
    directory = key.split("/")[0]
    files = {head: header}
    for name in names:
        rel = f"{directory}/{name}"
        files[rel] = z.read(prefix + rel)
        if sha256(files[rel]) != checks[rel]:
            raise ValueError("publisher signal digest differs")
    target = work / directory
    target.mkdir(mode=0o700, exist_ok=True)
    paths = []
    for name, payload in files.items():
        path = work / name
        with path.open("xb") as stream:
            stream.write(payload)
        paths.append(path)
    raw_digest = sha256("".join(sha256(files[f"{directory}/{n}"]) for n in names).encode("ascii"))
    return paths, raw_digest


def score(args, config, other, entries, checks, names, manifest):
    import torch

    from titan_v45.data.reconstructed import prepare_p4_record
    from titan_v45.models import frozen_pathology as fp

    if not torch.cuda.is_available():
        raise RuntimeError("frozen P4 scoring requires a CEDIA GPU allocation")
    if digest(args.archive) != ARCHIVE_SHA256:
        raise ValueError("PTB Diagnostic provider archive digest differs")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    spec = importlib.util.spec_from_file_location(
        "native_stage_a", args.repo / "scripts/specialist_experiments/extract_features.py")
    if spec is None or spec.loader is None:
        raise ValueError("invalid pinned feature module")
    stage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage)
    morph = stage._safe_morphology(args.repo)
    assets, asset_hashes = fp.verified_assets(args.repo, args.assets, {fp.BACKBONE, fp.SPECIALIST})
    contract = json.loads((args.repo / "outputs/models/heads/global_head_contracts.json").read_bytes())
    model = fp.FrozenPathology(assets, contract, "cuda")
    features = []

    def collect(_, values):
        x = values[0].detach().cpu().numpy()
        if x.ndim != 2 or x.shape[1] != 670 or not np.isfinite(x).all():
            raise ValueError("private PTB-XL heads require the pinned P4 feature layout")
        features.append(x)

    handle = model.head.register_forward_pre_hook(collect)
    failures, status = Counter(), Counter()
    args.output.mkdir(mode=0o700)
    scores = args.output / "private-scores.jsonl"
    work = args.scratch / "ptb-source-record"
    work.mkdir(mode=0o700)
    pending = []

    def flush(stream):
        samples = [r[2] for r in pending if r[2] is not None]
        if samples:
            output = iter(model(samples))
            if len(features) != 1 or len(features[0]) != len(samples):
                raise ValueError("P4 feature hook row mismatch")
            representations = iter(features.pop())
        for key, raw_hash, sample in pending:
            row = {"key": key, "exact_signal_file_digest": raw_hash}
            if sample is None:
                row["status"] = "technical_unscored"
            else:
                published, auxiliary = next(output)
                feature = next(representations)
                row.update(status="scored", published_scores=published, auxiliary_scores=auxiliary,
                           published_labels=[k for k, v in published.items() if v >= model.thresholds[k]],
                           transported_head_scores={}, transported_head_labels=[])
                for label in ("ALMI", "ILMI"):
                    spec = other["endpoints"][label]
                    if spec["status"] != "calibrated":
                        raise ValueError("no sealed calibrated PTB-XL head")
                    p = float(probabilities(spec["model"], feature))
                    row["transported_head_scores"][label] = p
                    if p >= spec["threshold"]:
                        row["transported_head_labels"].append(label)
            status[row["status"]] += 1
            stream.write(json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n")
        pending.clear()

    with zipfile.ZipFile(args.archive) as z, scores.open("x", encoding="utf-8") as stream:
        files = z.namelist()
        index = [x for x in files if x.endswith("/RECORDS")]
        if len(index) != 1 or len(set(files)) != len(files):
            raise ValueError("ambiguous official PTB archive")
        prefix = index[0].removesuffix("RECORDS")
        if z.read(index[0]) != names or z.read(prefix + "SHA256SUMS.txt") != manifest:
            raise ValueError("PTB archive is not the reference-audited release")
        for key in entries:
            paths, raw_hash = verified_record(z, prefix, key, checks, work)
            try:
                sample = prepare_p4_record(work / key, morph)
            except (ValueError, OSError, IndexError) as exc:
                failures[type(exc).__name__] += 1
                sample = None
            finally:
                for path in paths:
                    path.unlink()
            pending.append((key, raw_hash, sample))
            if len(pending) == 16:
                flush(stream)
        flush(stream)
    handle.remove()
    if sum(status.values()) != len(entries) or status["scored"] == 0:
        raise ValueError("incomplete or empty provider scoring")
    write_new(args.output / "scoring-receipt.json", {
        "schema": config["schema"], "stage": "score", "job": os.environ.get("SLURM_JOB_ID"),
        "protocol_sha256": TRANSPORT_SHA256, "source_archive_sha256": ARCHIVE_SHA256,
        "record_index_sha256": sha256(names), "publisher_manifest_sha256": sha256(manifest),
        "all_source_records": len(entries), "flow": status, "technical_failure_types": failures,
        "native_model_assets_sha256": asset_hashes, "published_thresholds": model.thresholds,
        "transported_model_sha256": config["pathology_other_model_sha256"],
        "transported_thresholds": {c: other["endpoints"][c]["threshold"] for c in ("ALMI", "ILMI")},
        "private_scores_sha256": digest(scores), "reference_labels_used_for_scoring": False,
        "no_individual_records_exported": True,
    })


def evaluate(args, config, entries, names, manifest):
    from titan_v45.evaluation.specialist_heads import bootstrap_binary_metrics

    from titan_v45.evaluation.revision_report import binary_metrics

    scores = args.output / "private-scores.jsonl"
    receipt = args.output / "scoring-receipt.json"
    result = json.loads(receipt.read_bytes())
    if (not args.score_receipt_sha256 or digest(receipt) != args.score_receipt_sha256
            or result["private_scores_sha256"] != digest(scores) or result["protocol_sha256"] != TRANSPORT_SHA256
            or result["source_archive_sha256"] != ARCHIVE_SHA256
            or result["record_index_sha256"] != sha256(names)
            or result["publisher_manifest_sha256"] != sha256(manifest)
            or result["reference_labels_used_for_scoring"] is not False):
        raise ValueError("PTB scoring must be sealed before reference access")
    eligibility = json.loads((args.audit / "aggregate.json").read_bytes())
    reference = args.audit / "private-reference-manifest.jsonl"
    if (digest(reference) != eligibility["reference_manifest_sha256"]
            or any(not eligibility["endpoints"][c]["eligible_for_territory_control_comparison"] for c in ENDPOINTS)):
        raise ValueError("reference eligibility or private manifest changed")
    rows, audit = list(jsonl(scores)), list(jsonl(reference))
    if [r["key"] for r in rows] != entries or [r["record"] for r in audit] != entries:
        raise ValueError("private score/reference order differs from all enrolled ECGs")
    refs = {r["record"]: {k: ("negative" if v == "explicit_control" else v) for k, v in r["references"].items()}
            for r in audit}
    groups = components({"ecg_id": r["key"], "patient_id": r["key"].split("/")[0],
                         "signal_sha256_canonical_f64": r["exact_signal_file_digest"]} for r in rows)
    if Counter(r["status"] for r in rows) != Counter(result["flow"]):
        raise ValueError("score denominator mismatch")
    for label in ENDPOINTS:
        per_group = {}
        for key, group in groups.items():
            per_group.setdefault(group, set()).add(refs[key][label])
        discordant = {g for g, states in per_group.items() if {"positive", "negative"} <= states}
        for key, group in groups.items():
            if group in discordant:
                refs[key][label] = "discordant_patient_signal_component"
    endpoints = {}
    for label in ENDPOINTS:
        if label in ("ASMI", "IMI"):
            sources = {"released_P4_threshold": ("published_scores", "published_labels")}
        else:
            sources = {"released_V3AG_rank_only": ("auxiliary_scores", None),
                       "separately_trained_PTBXL_head": ("transported_head_scores", "transported_head_labels")}
        endpoints[label] = {}
        for name, (field, calls) in sources.items():
            def decision(r, target=label, scores_field=field, calls_field=calls):
                return r.get(scores_field, {}).get(target), (
                    int(target in r.get(calls_field, ())) if calls_field else None)

            endpoints[label][name] = endpoint_metrics(
                rows, refs, groups, label, decision, {"all_source_ecgs": lambda _: True},
                config["statistical_design"], binary_metrics, bootstrap_binary_metrics)["all_source_ecgs"]
    write_new(args.output / "aggregate.json", {
        "schema": config["schema"], "stage": "evaluate", "job": os.environ.get("SLURM_JOB_ID"),
        "score_receipt_sha256": args.score_receipt_sha256, "scope": config["scope"],
        "reference_eligibility_sha256": digest(args.audit / "aggregate.json"),
        "private_reference_manifest_sha256": digest(reference), "all_source_ecgs": len(entries),
        "source_subjects": len({r["source_subject"] for r in audit}),
        "patient_exact_signal_components": len(set(groups.values())), "scored_flow": result["flow"],
        "endpoints": endpoints, "fit_or_calibration_performed": False,
        "historical_independence_certified": False, "no_individual_records_exported": True,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("score", "evaluate"))
    for name in ("config", "audit", "other-model", "other-fit-receipt", "archive", "repo", "assets", "scratch", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--score-receipt-sha256")
    args = parser.parse_args()
    config, model, entries, checks, names, manifest = verify_inputs(args)
    if args.stage == "score":
        score(args, config, model, entries, checks, names, manifest)
    else:
        evaluate(args, config, entries, names, manifest)


if __name__ == "__main__":
    main()
