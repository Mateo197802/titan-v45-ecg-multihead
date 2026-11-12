"""Paired, locked evaluation of published and frozen residual rhythm models."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import tarfile
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

import numpy as np
from code15_io import PROTOCOL, ROOT, digest
from fit_code_transfer import residual_logits
from scipy.special import expit

sys.path.insert(0, str(ROOT / "scripts/specialist_experiments"))
from extract_features import _rhythm_batch, _safe_morphology

from titan_v45.data.external_ecg import physical_mv, prepare_external, unpad_code
from titan_v45.evaluation.external_metrics import from_confusion
from titan_v45.evaluation.revision_report import binary_metrics
from titan_v45.models.frozen_rhythm import P8_CLASSES

METRICS = ("sensitivity", "specificity", "ppv", "npv", "f1", "auroc", "auprc", "brier", "ece")


def label(value):
    return {"true": 1, "1": 1, "false": 0, "0": 0}.get((value or "").strip().lower(), -1)


def selected(patient):
    return hashlib.sha256(f"20261112|pr6-code15|{patient}".encode()).digest()[0] < 32


def signature(x):
    block = x.reshape(12, 250, 5).mean(axis=2)
    block -= block.mean(axis=1, keepdims=True)
    norms = np.linalg.norm(block, axis=1, keepdims=True).clip(1e-8)
    return (block / norms).reshape(-1).astype(np.float32) / np.sqrt(np.float32(12))


def historical_signatures(archive: Path, scratch: Path):
    import wfdb
    import zstandard

    entry = next(a for a in json.loads((ROOT / "release-manifest.json").read_bytes())["assets"]
                 if a["name"] == archive.name)
    if digest(archive) != entry["sha256"] or archive.stat().st_size != entry["bytes"]:
        raise ValueError("historical waveform release archive mismatch")
    directory = scratch / "historical"
    directory.mkdir()
    names = set()
    with archive.open("rb") as handle, zstandard.ZstdDecompressor().stream_reader(handle) as decoded:
        with tarfile.open(fileobj=decoded, mode="r|") as tar:
            for info in tar:
                parts = PurePosixPath(info.name).parts
                if parts and parts[0] == "external-dev-rhythm-chapman-shaoxing":
                    parts = parts[1:]
                if (parts[:2] != ("records", "codetest") or len(parts) < 3
                        or Path(info.name).suffix not in (".hea", ".dat", ".mat")):
                    continue
                name = parts[-1]
                if (not info.isfile() or info.size > 2 * 1024 ** 2 or name in names
                        or ".." in parts or "\\" in info.name):
                    raise ValueError("unexpected historical component")
                names.add(name)
                with tar.extractfile(info) as inp, (directory / name).open("wb") as out:
                    shutil.copyfileobj(inp, out)
    signatures, unavailable = [], Counter()
    for header in sorted(directory.glob("*.hea")):
        try:
            base = header.with_suffix("")
            metadata = wfdb.rdheader(str(base))
            expected = [{base.name + extension} for extension in (".dat", ".mat")]
            if set(metadata.file_name) not in expected or metadata.sig_len < 10 * metadata.fs:
                raise ValueError("invalid historical header")
            if metadata.fs == 400 and metadata.sig_len == 4096:
                trace = wfdb.rdrecord(str(base))
                values = unpad_code(trace.p_signal)
            else:
                trace = wfdb.rdrecord(str(base), sampto=int(10 * metadata.fs))
                values = trace.p_signal
            signal = physical_mv(values, trace.sig_name, trace.units, int(metadata.fs))
            x, _, _ = prepare_external(signal, int(metadata.fs), lambda *_args, **_kwargs: None)
            signatures.append(signature(x))
        except (ValueError, OSError, RuntimeError) as error:
            reason = str(error)
            if reason not in {"invalid historical header", "unexpected_code_padding", "flat_lead", "invalid_code_array",
                              "short_or_ambiguous_code_duration", "unknown_physical_unit",
                              "invalid_canonical_leads", "invalid_rate_or_duration"}:
                reason = type(error).__name__
            unavailable[reason] += 1
    return np.asarray(signatures, dtype=np.float32).reshape(-1, 3000), dict(unavailable)


def publisher_test_signatures(source: Path, scratch: Path):
    """Compare with original CODE-test signals, never its annotations."""
    import h5py

    archive = source / "data.zip"
    if archive.stat().st_size != 218189452:
        raise ValueError("publisher CODE-test archive size mismatch")
    md5 = hashlib.md5(usedforsecurity=False)
    with archive.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(block)
    if md5.hexdigest() != "cef8fe457abf4b8f66a34dc1269b4ced":
        raise ValueError("publisher CODE-test archive checksum mismatch")
    checksum = digest(archive)
    target = scratch / "publisher-code-test.hdf5"
    with zipfile.ZipFile(archive) as package:
        members = [item for item in package.infolist()
                   if PurePosixPath(item.filename).name == "ecg_tracings.hdf5"]
        if len(members) != 1 or members[0].file_size > 400 * 1024 ** 2:
            raise ValueError("invalid publisher CODE-test signal member")
        with package.open(members[0]) as inp, target.open("xb") as out:
            shutil.copyfileobj(inp, out, length=1024 * 1024)
    signatures, failures = [], Counter()
    with h5py.File(target, "r") as h5:
        traces = h5["tracings"]
        if traces.shape != (827, 4096, 12):
            raise ValueError("invalid publisher CODE-test signal shape")
        for trace in traces:
            try:
                signal = unpad_code(trace).T.astype(np.float32)
                if np.any(np.ptp(signal, axis=1) <= 1e-6):
                    raise ValueError("flat_lead")
                x, _, _ = prepare_external(signal, 400, lambda *_args, **_kwargs: None)
                signatures.append(signature(x))
            except ValueError as error:
                failures[str(error)] += 1
    target.unlink()
    if not signatures or len(signatures) + sum(failures.values()) != 827:
        raise ValueError("publisher CODE-test comparison reference incomplete")
    return np.stack(signatures), {"doi": "10.5281/zenodo.3765780", "archive_sha256": checksum,
                                  "aligned_signatures": len(signatures), "excluded": dict(failures),
                                  "annotations_opened": False}


def verified_hdf5(code, name, catalog, scratch):
    path = code / name
    entry = next(item for item in catalog["files"] if item["key"] == name)
    md5 = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(block)
    if path.stat().st_size != entry["size"] or "md5:" + md5.hexdigest() != entry["checksum"]:
        raise ValueError("publisher CODE archive mismatch")
    member = path.with_suffix(".hdf5").name
    dest = scratch / member
    with zipfile.ZipFile(path) as archive:
        if archive.namelist() != [member] or archive.getinfo(member).file_size > 8 * 1024 ** 3:
            raise ValueError("unexpected CODE archive member")
        with archive.open(member) as source, dest.open("xb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
    return dest


def estimates(y, pred, score):
    values = binary_metrics(y, pred, score)
    table = from_confusion(*(values[key] for key in ("tp", "fp", "tn", "fn")))
    return {**{key: values[key] for key in ("tp", "tn", "fp", "fn")},
            **{key: table[key] for key in ("sensitivity", "specificity", "f1")},
            "ppv": table["precision"], "npv": table["npv"], "ece": values["ece"],
            "auroc": values["auroc"], "auprc": values["average_precision"], "brier": values["brier_score"]}


def paired_metrics(labels, old, new, patients, threshold, endpoints, config):
    rng = np.random.default_rng(config["bootstrap_seed"])
    names, inverse = np.unique(patients, return_inverse=True)
    groups = [np.flatnonzero(inverse == idx) for idx in range(len(names))]
    supports = []
    for col in range(len(endpoints)):
        supports.append(tuple(len(np.unique(patients[labels[:, col] == y])) for y in (0, 1)))
    supported = [min(count) >= config["minimum_distinct_positive_and_negative_patients"] for count in supports]

    def paired(indices):
        result = []
        for col, valid in enumerate(supported):
            ix = indices[labels[indices, col] >= 0]
            y = labels[ix, col]
            if not valid or len(set(y)) != 2:
                result.append((None, None))
                continue
            result.append(tuple(estimates(y, scores[ix, col] >= threshold[col], scores[ix, col])
                                for scores in (old, new)))
        return result

    observed = paired(np.arange(len(patients)))
    samples = [[{name: [] for name in METRICS} for _ in range(2)] for _ in endpoints]
    paired_samples = [dict((name, []) for name in METRICS) for _ in endpoints]
    macro_samples = [[], []]
    deltas = []
    for _ in range(config["bootstrap_replicates"]):
        chosen = rng.integers(0, len(groups), len(groups))
        stats = paired(np.concatenate([groups[i] for i in chosen]))
        for col, pair in enumerate(stats):
            for model, values in enumerate(pair):
                if values is not None:
                    for metric in METRICS:
                        if values[metric] is not None:
                            samples[col][model][metric].append(values[metric])
            if pair[0] is not None:
                for metric in METRICS:
                    if all(values[metric] is not None for values in pair):
                        paired_samples[col][metric].append(pair[1][metric] - pair[0][metric])
        if any(supported) and all(pair[0] is not None for i, pair in enumerate(stats) if supported[i]):
            deltas.append(np.mean([pair[1]["f1"] - pair[0]["f1"] for pair in stats if pair[0] is not None]))
            for model in range(2):
                macro_samples[model].append(np.mean([pair[model]["f1"] for pair in stats if pair[0] is not None]))
    output = []
    for col, endpoint in enumerate(endpoints):
        for m, name in enumerate(("published", "anchored_linear_residual_v1")):
            row = {"endpoint": endpoint, "model": name, "n_ecg_with_reference": int((labels[:, col] >= 0).sum()),
                   "n_patients_with_reference": len(np.unique(patients[labels[:, col] >= 0])),
                   "n_positive_ecg": int((labels[:, col] == 1).sum()), "n_negative_ecg": int((labels[:, col] == 0).sum()),
                   "n_positive_patients": supports[col][1], "n_negative_patients": supports[col][0],
                   "threshold": threshold[col], "estimable": supported[col]}
            row.update(observed[col][m] or dict.fromkeys((*METRICS, "tp", "tn", "fp", "fn")))
            for key, values in samples[col][m].items():
                low, high = np.quantile(values, [0.025, 0.975]) if values else (None, None)
                row.update({key + "_ci_low": low, key + "_ci_high": high, key + "_valid_replicates": len(values)})
                old_value, new_value = (observed[col][k][key] if observed[col][k] is not None else None
                                        for k in range(2))
                pair_values = paired_samples[col][key] if m else []
                dlo, dhi = np.quantile(pair_values, [0.025, 0.975]) if pair_values else (None, None)
                row.update({key + "_delta": (new_value - old_value if m and old_value is not None
                                              and new_value is not None else None),
                            key + "_delta_ci_low": dlo, key + "_delta_ci_high": dhi,
                            key + "_delta_valid_replicates": len(pair_values)})
            output.append(row)
    estimable = [p for p in observed if p[0] is not None]
    if not estimable:
        return output, {"decision": "NOT_EVALUABLE", "macro_f1_classes": [],
                        "empty_sets": [int((~(scores >= threshold).any(axis=1)).sum()) for scores in (old, new)]}
    delta = float(np.mean([p[1]["f1"] - p[0]["f1"] for p in estimable]))
    sensitivity = float(min(p[1]["sensitivity"] - p[0]["sensitivity"] for p in estimable))
    macro_brier = float(np.mean([p[1]["brier"] - p[0]["brier"] for p in estimable]))
    empty_change = float(np.mean(~(new >= threshold).any(axis=1)) - np.mean(~(old >= threshold).any(axis=1)))
    ci = np.quantile(deltas, [0.025, 0.975]).tolist() if deltas else [None, None]
    pass_gate = (all(supported) and delta >= config["promotion_macro_f1_gain_min"] and ci[0] is not None
                 and ci[0] > 0 and sensitivity >= -config["promotion_max_sensitivity_drop"]
                 and macro_brier <= config["promotion_max_macro_brier_increase"]
                 and empty_change <= config["promotion_max_empty_set_rate_increase"])
    return output, {"macro_f1_delta": delta, "delta_ci95": ci, "delta_valid_replicates": len(deltas),
                    "macro_f1_classes": [e for e, valid in zip(endpoints, supported, strict=True) if valid],
                    "macro_f1": [float(np.mean([p[m]["f1"] for p in estimable])) for m in range(2)],
                    "macro_f1_ci95": [np.quantile(v, [0.025, 0.975]).tolist() if v else [None, None]
                                      for v in macro_samples],
                    "empty_sets": [int((~(scores >= threshold).any(axis=1)).sum()) for scores in (old, new)],
                    "minimum_sensitivity_change": sensitivity, "macro_brier_delta": macro_brier,
                    "five_endpoint_empty_set_delta": empty_change, "observed_metric_gate_pass": pass_gate}


def run(args):
    import h5py
    import torch
    from probe_frozen import load_scorers
    from verify_code15_evaluation import verify, write_aggregate_views

    protocol = json.loads(PROTOCOL.read_bytes())
    config = protocol["evaluation"]
    codes = protocol["reference"]
    endpoints = list(codes)
    columns = [P8_CLASSES.index(name) for name in endpoints]
    receipt_path = args.candidates / "candidate_receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    if (receipt["protocol_sha256"] != digest(PROTOCOL) or receipt["endpoints"] != endpoints
            or receipt["code_or_mimic_outcomes_used"] or receipt["thresholds_changed"]):
        raise ValueError("candidate freeze incompatible with CODE evaluation")
    corrections = {}
    for profile in config["profiles"]:
        path = args.candidates / f"{profile}.npz"
        if digest(path) != receipt["profiles"][profile]["sha256"]:
            raise ValueError("candidate checkpoint digest mismatch")
        with np.load(path, allow_pickle=False) as candidate:
            if candidate["endpoints"].tolist() != endpoints:
                raise ValueError("candidate endpoint order mismatch")
            corrections[profile] = [candidate[key] for key in ("mean", "scale", "coefficients", "cap")]
    code = args.study / "code15"
    for path, field in ((code / "exams.csv", "metadata_sha256"), (code / "record.json", "catalog_sha256")):
        if digest(path) != protocol[field]:
            raise ValueError("CODE publisher metadata mismatch")
    catalog = json.loads((code / "record.json").read_bytes())
    names = {entry["key"] for entry in catalog["files"] if entry["key"].endswith(".zip")}
    archives = args.archives or sorted(names)
    if len(set(archives)) != len(archives) or not set(archives) <= names:
        raise ValueError("unexpected shard list")
    if set(archives) != names and archives != ["exams_part10.zip"]:
        raise ValueError("only full coverage or the frozen first checkpoint is permitted")
    args.output.mkdir(mode=0o700, exist_ok=False)
    parts = {Path(name).with_suffix(".hdf5").name: {} for name in archives}
    all_keys = set()
    with (code / "exams.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["trace_file"] not in parts:
                continue
            key = int(row["exam_id"])
            if key in all_keys:
                raise ValueError("duplicated CODE index exam")
            all_keys.add(key)
            patient = row["patient_id"].strip()
            if not patient:
                raise ValueError("missing CODE patient key")
            parts[row["trace_file"]][key] = (
                (patient, [label(row[codes[endpoint]]) for endpoint in endpoints])
                if selected(patient) else None
            )
    history, unavailable = historical_signatures(args.historical, args.scratch)
    archive_signature_count = len(history)
    publisher_overlap = None
    if getattr(args, "publisher_test", None) is not None:
        publisher, publisher_overlap = publisher_test_signatures(args.publisher_test, args.scratch)
        history = np.concatenate((history, publisher))
    if not len(history):
        raise ValueError(f"no comparable historical CODE-test signatures: {unavailable}")
    source_protocol = json.loads((ROOT / "docs/external_validation_20261111/FROZEN_EXTERNAL_EVALUATION_PROTOCOL.json").read_bytes())
    rhythm, _, hashes, thresholds = load_scorers(args.assets, source_protocol)
    morphology = _safe_morphology(ROOT)
    stats = Counter()
    archive_hashes = {}
    samples, index_rows, excluded, sigs = [], [], [], []
    old = {profile: [] for profile in config["profiles"]}
    new = {profile: [] for profile in config["profiles"]}
    pending = []
    if args.reuse_partial is not None:
        if set(archives) != names:
            raise ValueError("partial scores may only resume the full evaluation")
        prior = json.loads((args.reuse_partial / "code15_evaluation_receipt.json").read_bytes())
        prior_cache = args.reuse_partial / "private_shard_cache.npz"
        prior_ledger = args.reuse_partial / "private_selection.json"
        if (prior["protocol_sha256"] != digest(PROTOCOL)
                or prior["candidate_receipt_sha256"] != digest(receipt_path)
                or prior["private_shard_cache_sha256"] != digest(prior_cache)
                or prior["private_selection_sha256"] != digest(prior_ledger)
                or prior.get("publisher_code_test_overlap") != publisher_overlap
                or prior["archive_sha256"] != {"exams_part10.zip": digest(code / "exams_part10.zip")}):
            raise ValueError("partial cache provenance mismatch")
        archive_hashes.update(prior["archive_sha256"])
        stats.update(prior["counts"])
        excluded.extend(json.loads(prior_ledger.read_bytes())["excluded_before_scoring"])
        with np.load(prior_cache, allow_pickle=False) as cache:
            index_rows.extend((int(exam), patient, y.tolist(), "exams_part10.zip")
                              for exam, patient, y in zip(cache["exams"], cache["patients"], cache["labels"], strict=True))
            sigs.extend(cache["signatures"])
            for profile in old:
                old[profile].append(cache["baseline_" + profile])
                new[profile].append(cache["candidate_" + profile])

    def flush():
        if not pending:
            return
        extracted = _rhythm_batch(rhythm, samples)
        for profile in config["profiles"]:
            features, logits = extracted[profile]
            baseline = logits[:, columns]
            corrected = residual_logits(features, baseline, *corrections[profile])
            if not np.isfinite(corrected).all() or not np.isfinite(baseline).all():
                raise ValueError("nonfinite score")
            if profile == "P6":
                old[profile].append(expit(baseline.astype(np.float64).clip(-50, 50)))
                new[profile].append(expit(corrected.clip(-50, 50)))
            else:
                old[profile].append(torch.as_tensor(baseline).sigmoid().numpy())
                new[profile].append(torch.as_tensor(corrected, dtype=torch.float32).sigmoid().numpy())
        index_rows.extend(pending)
        samples.clear()
        pending.clear()

    for name in archives:
        if name in archive_hashes:
            continue
        h5path = verified_hdf5(code, name, catalog, args.scratch)
        archive_hashes[name] = digest(code / name)
        try:
            with h5py.File(h5path, "r") as h5:
                id_key, trace_key = next(pair for pair in (("exam_id", "tracings"), ("id_exam", "signal"))
                                         if set(pair) <= h5.keys())
                ids, traces = np.asarray(h5[id_key]).reshape(-1), h5[trace_key]
                lookup = parts[h5path.name]
                raw_ids = [int(value) for value in ids if int(value) != 0]
                if (traces.shape != (len(ids), 4096, 12) or len(raw_ids) != len(set(raw_ids))
                        or set(raw_ids) != lookup.keys()):
                    raise ValueError("HDF5 and publisher index do not have identical exam membership")
                stats["source_ecgs"] += len(raw_ids)
                for idx, exam in enumerate(ids):
                    ref = lookup.get(int(exam))
                    if ref is None:
                        continue
                    stats["selected_ecgs"] += 1
                    patient, labels = ref
                    try:
                        signal = unpad_code(traces[idx]).T.astype(np.float32)
                        if np.any(np.ptp(signal, axis=1) <= 1e-6):
                            raise ValueError("flat_lead")
                        prepared = prepare_external(signal, 400, morphology)
                        sig = signature(prepared[0])
                        if np.max(history @ sig) >= 0.995:
                            raise ValueError("aligned_historical_code_test_match")
                    except (ValueError, OSError, RuntimeError) as error:
                        reason = str(error) if str(error) in {"flat_lead", "unexpected_code_padding",
                            "short_or_ambiguous_code_duration", "invalid_code_array", "aligned_historical_code_test_match"} else "decode_or_preprocess_error"
                        stats[reason] += 1
                        excluded.append({"exam": int(exam), "shard": name, "reason": reason})
                        continue
                    pending.append((int(exam), patient, labels, name))
                    samples.append(prepared)
                    sigs.append(sig)
                    if len(samples) == 32:
                        flush()
            print(json.dumps({"shard": name, "cumulative_counts": stats}), flush=True)
        finally:
            h5path.unlink(missing_ok=True)
    flush()
    if not index_rows:
        raise ValueError("no CODE records survived common eligibility")
    matrix = np.stack(sigs)
    raw = {f"{kind}_{profile}": np.concatenate(values[profile])
           for kind, values in (("baseline", old), ("candidate", new)) for profile in old}
    cache_path = args.output / "private_shard_cache.npz"
    if set(archives) != names:
        np.savez_compressed(cache_path, signatures=matrix,
                            exams=np.asarray([row[0] for row in index_rows]),
                            patients=np.asarray([row[1] for row in index_rows]),
                            labels=np.asarray([row[2] for row in index_rows]), **raw)
    duplicate = set()
    for start in range(0, len(matrix), 128):
        for i, j in zip(*np.nonzero(matrix[start:start + 128] @ matrix.T >= 0.995), strict=True):
            if start + i < j:
                duplicate.update((start + int(i), int(j)))
    keep = np.asarray([i for i in range(len(index_rows)) if i not in duplicate], dtype=np.int64)
    if not len(keep):
        raise ValueError("duplicate screen removed every ECG")
    labels = np.asarray([index_rows[i][2] for i in keep])
    patients = np.asarray([index_rows[i][1] for i in keep])
    np.savez_compressed(args.output / "private_scores.npz", labels=labels, patients=patients,
                        exams=np.asarray([index_rows[i][0] for i in keep]),
                        **{key: value[keep] for key, value in raw.items()})
    ledger = {"excluded_before_scoring": excluded, "aligned_duplicate_exams": [index_rows[i][0] for i in sorted(duplicate)],
              "eligible_exams": [index_rows[i][0] for i in keep]}
    (args.output / "private_selection.json").write_text(json.dumps(ledger, sort_keys=True))
    csv_rows, decisions = [], {}
    for profile in config["profiles"]:
        threshold = np.asarray([thresholds[profile][endpoint] for endpoint in endpoints])
        rows, decision = paired_metrics(labels, np.concatenate(old[profile])[keep], np.concatenate(new[profile])[keep],
                                        patients, threshold, endpoints, config)
        csv_rows.extend({"profile": profile, **row} for row in rows)
        if decision.get("decision") != "NOT_EVALUABLE":
            decision["decision"] = ("PASS" if decision["observed_metric_gate_pass"] else "FAIL") if set(archives) == names else "INCOMPLETE_NO_PROMOTION"
        decisions[profile] = decision
    table = args.output / "CODE15_PER_CLASS.csv"
    with table.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(csv_rows)
    verification = verify(args.output, replay=paired_metrics, decisions=decisions)
    views = write_aggregate_views(args.output, decisions, len(keep), len(set(patients)),
                                  set(archives) == names, endpoints)
    result = {"protocol_sha256": digest(PROTOCOL), "candidate_receipt_sha256": digest(receipt_path),
              "archive_sha256": archive_hashes, "baseline_hashes": hashes, "counts": stats,
              "historical_aligned_signatures": len(history), "historical_ineligible": unavailable,
              "historical_release_archive_aligned_signatures": archive_signature_count,
              "publisher_code_test_overlap": publisher_overlap,
              "historical_patient_independence": "NOT_CERTIFIED", "within_code_duplicate_ecgs_excluded": len(duplicate),
              "n_ecg": len(keep), "n_patients": len(set(patients)), "complete_archive_coverage": set(archives) == names,
              "reused_verified_first_archive": args.reuse_partial is not None,
              "private_shard_cache_sha256": digest(cache_path) if cache_path.exists() else None,
              "private_scores_sha256": digest(args.output / "private_scores.npz"),
              "private_selection_sha256": digest(args.output / "private_selection.json"),
              "aggregate_csv_sha256": digest(table), "aggregate_views_sha256": views, "promotion": decisions}
    result["point_estimates_independently_verified"] = verification
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (args.output / "code15_evaluation_receipt.json").write_bytes(output.encode())
    print(output, end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("study", "candidates", "assets", "historical", "scratch", "output"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--archives", nargs="+")
    parser.add_argument("--publisher-test", type=Path)
    parser.add_argument("--reuse-partial", type=Path)
    run(parser.parse_args())
