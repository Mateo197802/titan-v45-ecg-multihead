"""Trace the reconstructed runtime and execute a conditional P6 fallback."""
import argparse
from collections import Counter
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
from time import perf_counter
from unittest.mock import patch
from zipfile import ZipFile

import numpy as np
import scipy
from scipy.signal import butter, lfilter, resample_poly
import torch
import wfdb

from compare_reviewer_baseline import digest
from reviewer_selective_utility import SEALED, read, sealed
from freeze_reviewer_selective_policy import jsonl
from score_reviewer_closure_ludb import PREFIX, TensorAudit, source_manifest, write_new
from titan_v45.data import reconstructed as prep
from titan_v45.data.preprocessing import CANONICAL_12_LEADS, extract_named_leads
from titan_v45.models import frozen_pathology as fp, frozen_rhythm as fr


def imported(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_fixtures(m):
    wave = np.zeros((12, 1250))
    for peak in (200, 300, 425):
        wave[1, peak-20] = 0.2
        wave[1, peak-1:peak+2] = [0.7, 1, 0.7]
    t = np.arange(1250) / 125
    mix = np.sin(2*np.pi*0.5*t) + 2*np.sin(2*np.pi*10*t) + 3*np.sin(2*np.pi*40*t)
    bands = np.stack([2*mix] + [mix]*10 + [-mix])
    flat = np.zeros((12, 1250))
    flat[0, 0] = np.nan
    flat[1, 0] = np.inf
    expected = {
        "hr_median_bpm": 60/0.9, "rrv_cv": 0.1/0.9, "rrv_rmssd_ms": 200,
        "qrs_width_proxy_ms": 24, "p_to_r_proxy_ms": 160,
        "qrs_band_ratio": 4/14, "lowfreq_ratio": 1/14, "hf_ratio": 9/14,
        "lead_corr_abs_mean": 1, "limb_qrs_asymmetry": 0.6,
    }
    pulse, spectrum = (m.compute_morphology_features(x, 125) for x in (wave, bands))
    observed = {k: (pulse if i < 5 else spectrum)[k] for i, k in enumerate(expected)}
    if pulse["r_peak_count"] != 3:
        raise ValueError("unexpected peak count for the pulse fixture")
    np.testing.assert_allclose(list(observed.values()), list(expected.values()), atol=1e-12, rtol=0)
    normal = m.normalized_morphology_features(wave, 125)
    np.testing.assert_allclose(normal[:5], [expected[k]/d for k, d in
                              zip(list(expected)[:5], [220, 1, 500, 220, 320], strict=True)], atol=1e-7)
    flat_values = m.normalized_morphology_features(flat, 125)
    # The historical candidate has no flat-line rejection before plateau peak selection.
    flat_peak_count = m.compute_morphology_features(flat, 125)["r_peak_count"]
    np.testing.assert_allclose(flat_values, [60/.28/220, 0, 0, 0, .28/.32, 0, 0, 0, 0, 0], atol=1e-7)
    if flat_peak_count != 36:
        raise ValueError("flat-line boundary behavior differs")
    reversed_leads = bands.copy()
    reversed_leads[[0, 5]] = reversed_leads[[5, 0]]
    np.testing.assert_allclose(m.normalized_morphology_features(reversed_leads, 125)[-1], -0.6, atol=1e-7)
    if m._norm(440, 220) != 1 or m._norm(-1, 1) != 0 or m._norm(-2, 1, low=-1) != -1:
        raise ValueError("normalization clamp differs")
    return {"expected": expected, "observed": observed, "pulse_peak_count": 3,
            "flat_line_artifact": {"peaks": flat_peak_count, "normalized_values": flat_values.tolist()},
            "clamp_checked": True, "negative_limb_asymmetry_checked": True}


def features(path, m, trace):
    rec = wfdb.rdrecord(str(path))
    if rec.fs != 500 or rec.sig_len != 5000 or tuple(n.lower() for n in rec.sig_name) != tuple(
            n.lower() for n in CANONICAL_12_LEADS):
        raise ValueError("unexpected waveform contract")
    fs = int(rec.fs)
    signal, mask = extract_named_leads(np.pad(rec.p_signal, ((2*fs, 2*fs), (0, 0))), rec.sig_name)
    b, a = butter(3, [0.5/(fs/2), 45/(fs/2)], btype="band")
    filtered = signal.copy()
    active = np.std(filtered, axis=1) > 1e-6
    for idx in np.flatnonzero(active):
        filtered[idx] = lfilter(b, a, filtered[idx])
    pre_z = resample_poly(filtered, 1, 4, axis=1)[:, 250:1500]
    unfiltered = resample_poly(signal, 1, 4, axis=1)[:, 250:1500]

    def standardize(x):
        scale = x.std(axis=1, keepdims=True)
        return (x-x.mean(axis=1, keepdims=True))/np.where(scale < 1e-6, 1, scale)

    real = {}
    for name, f in (("rhythm", prep.prepare_rhythm_record), ("pathology", prep.prepare_p4_record)):
        def extraction(x, fs):
            np.testing.assert_allclose(x, standardize(pre_z), rtol=0, atol=2e-5)
            if fs != 125:
                raise ValueError("morphology rate mismatch")
            sd = np.std(x, axis=1)
            lead = 1 if sd[1] > 1e-6 else int(np.argmax(sd))
            selected = m._best_rhythm_lead(x)
            np.testing.assert_array_equal(selected, x[lead])
            raw = m.compute_morphology_features(x, fs)
            counts = trace[name]
            counts["windows"] += 1
            counts[f"lead_{CANONICAL_12_LEADS[lead]}"] += 1
            counts["peak_count_sum"] += raw["r_peak_count"]
            for key in m.MORPHOLOGY_FEATURE_NAMES:
                counts["nonfinite:" + key] += int(not np.isfinite(raw[key]))
            return m.normalized_morphology_features(x, fs)

        # Spy on actual production calls as well as checking an independently prepared array.
        with patch.object(prep, "butter", wraps=prep.butter) as filt, patch.object(
                prep, "resample_poly", wraps=prep.resample_poly) as resample:
            got = f(path, extraction, wfdb_module=wfdb)
        sample = got[0] if name == "rhythm" else got
        if name == "rhythm" and len(got) != 1:
            raise ValueError("expected one rhythm window")
        np.testing.assert_array_equal(sample[1], mask)
        if (filt.call_count != int(active.sum()) or
                any(call.args[:2] != (3, [0.002, 0.18]) for call in filt.call_args_list)
                or any(call.args[1:3] != (1, 4) for call in resample.call_args_list)
                or resample.call_count != (12 if name == "rhythm" else 1)):
            raise ValueError("actual bandpass/resampling call contract differs")
        trace[name]["bandpass_leads"] += int(active.sum())
        trace[name]["resampling_calls"] += resample.call_count
        real[name] = sample
    dropped = real["rhythm"][0].copy()
    dropped[1] = 0
    missing = mask.copy()
    missing[1] = False
    variants = {"no_bandpass": (standardize(unfiltered), mask),
                "no_standardization": (pre_z, mask), "drop_lead_II": (dropped, missing)}
    return real, {n: (x, lm, m.normalized_morphology_features(x, 125)) for n, (x, lm) in variants.items()}


def p6_fallback(rows, runtime, raw, morphology, thresholds, out):
    targets = fr.P6_CLASSES
    endpoints = [(p, c) for p in ("P8", "P4") for c in thresholds[p]]
    by_endpoint = {f"{p}:{c}": Counter() for p, c in endpoints}
    routes = Counter()
    fallback_time = []
    runtime.heads.pop("P8")
    ledger = out / "private-cascade.jsonl"
    with ledger.open("x", encoding="utf-8") as stream:
        for row in rows:
            state = row["route"]["state"]
            routes[state] += 1
            result = None
            if state == "abstained":
                start = perf_counter()
                try:
                    samples = prep.prepare_rhythm_record(raw / row["key"], morphology, wfdb_module=wfdb)
                    logits, _ = runtime(samples)
                    result = fr.aggregate_rhythm(logits["P6"], thresholds["P6"], profile="P6")
                except (OSError, ValueError, IndexError):
                    routes["fallback_technical_failure"] += 1
                fallback_time.append(perf_counter()-start)
                routes["fallback_executed"] += int(result is not None)
            emitted = row["route"]["emitted"] if state == "accepted" else (
                {"P8_partial": result["labels"]} if result is not None else None)
            for p, c in endpoints:
                stat = by_endpoint[f"{p}:{c}"]
                ref = row["references"][c]
                if ref not in ("positive", "negative"):
                    stat["unknown_reference"] += 1
                    continue
                pos = ref == "positive"
                stat["known_total"] += 1
                stat["positive_total"] += int(pos)
                if state == "technical_unscored":
                    stat["technical_unscored"] += 1
                    stat["positive_unresolved"] += int(pos)
                    continue
                primary = c in row["profiles"][p]["labels"]
                stat["baseline_errors"] += int(primary != pos)
                if state == "accepted":
                    final = primary
                elif result is not None and p == "P8" and c in targets:
                    final = c in result["labels"]
                    stat["fallback_known"] += 1
                    stat["corrected"] += int(primary != pos and final == pos)
                    stat["introduced"] += int(primary == pos and final != pos)
                else:
                    stat["known_unresolved"] += 1
                    stat["positive_unresolved"] += int(pos)
                    continue
                stat["known_emitted"] += 1
                stat["final_errors"] += int(final != pos)
                stat["final_false_negatives"] += int(pos and not final)
            stream.write(json.dumps({"key": row["key"], "primary_route": state,
                                     "primary": row["profiles"], "fallback": result,
                                     "final_emitted": emitted}, allow_nan=False)+"\n")
    totals = Counter()
    for counts in by_endpoint.values():
        totals.update(counts)
    if totals["known_emitted"] + totals["known_unresolved"] + totals["technical_unscored"] != totals["known_total"]:
        raise ValueError("cascade denominator mismatch")
    return {"routes": routes, "full_ecgs": len(rows), "full_profile_coverage": routes["accepted"]/len(rows),
            "at_least_partial_coverage": (routes["accepted"]+routes["fallback_executed"])/len(rows),
            "endpoint_accounting": by_endpoint, "totals": totals,
            "fallback_seconds_median": float(np.median(fallback_time)) if fallback_time else None,
            "fallback_seconds_p95": float(np.quantile(fallback_time, .95)) if fallback_time else None,
            "fallback_seconds_total": float(sum(fallback_time)), "thresholds_P6": thresholds["P6"],
            "individual_ledger_sha256": digest(ledger)}


def main():
    p = argparse.ArgumentParser()
    for key in ("repo", "assets", "base", "protocol", "output"):
        p.add_argument(f"--{key}", type=Path, required=True)
    a = p.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.allow_tf32 = torch.backends.cuda.matmul.allow_tf32 = False
    score_dir = a.base / "titan-v45-scientific-closure" / "ludb-score-33697"
    eval_dir = a.base / "titan-v45-scientific-closure" / "ludb-eval-33720"
    receipt = read(sealed(score_dir / "scoring-receipt.json", SEALED["ludb_score"]))
    evaluated = read(sealed(eval_dir / "aggregate.json", SEALED["ludb"]))
    rows = list(jsonl(sealed(eval_dir / "private-reference-route-ledger.jsonl",
                             evaluated["private_reference_route_ledger_sha256"])))
    originals = list(jsonl(sealed(score_dir / "private-scored-and-routed.jsonl",
                                  receipt["private_score_route_ledger_sha256"])))
    index = {r["key"]: r for r in originals}
    if (len(rows) != 200 or len(index) != 200 or any(
            r["route"] != index[r["key"]]["route"] or r["profiles"] != index[r["key"]]["profiles"] for r in rows)):
        raise ValueError("fallback route lineage differs")
    raw = score_dir / "private-waveforms"
    archive = sealed(score_dir.parent / "ludb-1.0.1.zip", receipt["source_archive_sha256"])
    with ZipFile(archive) as z:
        manifest = z.read(PREFIX+"SHA256SUMS.txt")
    if sha256(manifest).hexdigest() != receipt["publisher_manifest_sha256"]:
        raise ValueError("publisher waveform manifest seal differs")
    publisher = source_manifest(manifest.decode())
    for r in rows:
        for suffix in (".hea", ".dat"):
            sealed(raw / (r["key"]+suffix), publisher[r["key"]+suffix])
        if publisher[r["key"]+".dat"] != index[r["key"]]["raw_waveform_digest"]:
            raise ValueError("prior scored waveform seal differs")
    morphology_path = sealed(a.repo / "scripts/cedia/recovery_candidates/morphology_features_v4.py",
                             receipt["morphology_source_sha256"])
    m = imported(morphology_path, "morphology_candidate")
    stage = imported(a.repo / "scripts/specialist_experiments/extract_features.py", "stage_a_feature_contract")
    morph = stage._safe_morphology(a.repo)
    sealed(Path(prep.__file__), receipt["preprocessor_sha256"])
    fixtures = check_fixtures(m)
    names = {fr.BACKBONE, *fr.HEADS.values(), fp.BACKBONE, fp.SPECIALIST}
    assets, hashes = fp.verified_assets(a.repo, a.assets, names)
    if hashes != receipt["model_hashes"]:
        raise ValueError("release asset lineage differs")
    contract = read(a.repo / "outputs/models/heads/global_head_contracts.json")
    events = fr.load_recorded_event_extractor(a.repo / "docs/provenance/recovered-original-sources-20261029.zip")
    rhythm, path = fr.FrozenRhythm(assets, contract, events, "cuda"), fp.FrozenPathology(assets, contract, "cuda")
    if stage._baseline_thresholds(a.repo, path) != receipt["thresholds"]:
        raise ValueError("release threshold lineage differs")
    picked = sorted((r for r in rows if r["route"]["state"] != "technical_unscored"),
                    key=lambda r: sha256(("titan-morph-trace-v1:"+r["key"]).encode()).hexdigest())[:16]
    trace = {k: Counter() for k in ("rhythm", "pathology")}
    samples = [features(raw/r["key"], m, trace) for r in picked]
    rb, pb = ([real[k] for real, _ in samples] for k in ("rhythm", "pathology"))
    for x, _, f in rb+pb:
        np.testing.assert_array_equal(morph(x, fs=125), f)
    audit = TensorAudit(torch)
    for name, model in (("V3F", rhythm.model), ("V3AG", path.model)):
        audit.attach_backbone(name, model)
        audit.attach_head(name+"_global_rhythm", model.head_rhythm, 650)
        audit.attach_head(name+"_global_pathology", model.head_pathology, 640, includes_morphology=False)
    for name, head in rhythm.heads.items():
        audit.attach_head(name, head, 681)
    audit.attach_head("P4", path.head, 670)

    def forward(r, p):
        audit.start(r)
        scores, _ = rhythm(r)
        audit.start(p)
        scores["P4"] = np.asarray([list(x.values()) for x, _ in path(p)])
        return scores

    baseline = forward(rb, pb)
    for k, x in forward(rb, pb).items():
        np.testing.assert_array_equal(x, baseline[k])
    individual = [forward([r], [p]) for r, p in zip(rb, pb, strict=True)]
    variants = {"singleton": {k: np.concatenate([d[k] for d in individual]) for k in baseline}}
    variants["zero_morphology"] = forward(*[[(x, mask, np.zeros_like(f)) for x, mask, f in batch]
                                            for batch in (rb, pb)])
    for k in samples[0][1]:
        v = [variant[k] for _, variant in samples]
        variants[k] = forward(v, v)
    audit.remove()
    cpu_r, cpu_p = fr.FrozenRhythm(assets, contract, events, "cpu"), fp.FrozenPathology(assets, contract, "cpu")
    cpu, _ = cpu_r(rb)
    cpu["P4"] = np.asarray([list(x.values()) for x, _ in cpu_p(pb)])
    variants["CPU"] = cpu
    effects = {name: {k: {"max_abs": float(np.max(np.abs(v-baseline[k]))),
                           "mean_abs": float(np.mean(np.abs(v-baseline[k]))),
                           "p4_outside_unchanged_tolerance": int((np.abs(v-baseline[k])>1e-5).sum()) if k == "P4" else None}
                      for k, v in variant.items()} for name, variant in variants.items()}
    fallback = p6_fallback(rows, rhythm, raw, morph, receipt["thresholds"], a.output.parent)
    write_new(a.output, {"job": os.environ.get("SLURM_JOB_ID"), "protocol_sha256": digest(a.protocol),
                         "score_receipt_sha256": SEALED["ludb_score"], "preprocessor_sha256": receipt["preprocessor_sha256"],
                         "morphology_sha256": digest(morphology_path), "model_hashes": hashes, "fixture": fixtures,
                         "torch": str(torch.__version__), "numpy": np.__version__, "scipy": scipy.__version__,
                         "gpu": torch.cuda.get_device_name(), "cuda": torch.version.cuda,
                         "shape_signal": [12, 1250], "shape_mask": [12], "shape_morphology": [10],
                         "source_fs": 500, "extractor_fs": 125, "filter": {"type": "causal Butterworth", "order": 3,
                                                                           "band_hz": [0.5, 45]},
                         "traced_ecgs": len(samples), "trace": trace, "tensors": audit.counts,
                         "architecture": {"rhythm_width": rhythm.widths,
                                          "p4_hidden_width": int(path.head.heads[0][1].weight.shape[0]),
                                          "model_parameters": {"V3F": sum(p.numel() for p in rhythm.model.parameters()),
                                                               "V3AG": sum(p.numel() for p in path.model.parameters())}},
                         "identical_fixed_batch_repetition": True,
                         "effects_rhythm_logits_pathology_probabilities": effects, "fallback": fallback,
                         "historical_loader_authenticated": False, "individual_data_exported": False})


if __name__ == "__main__":
    main()
