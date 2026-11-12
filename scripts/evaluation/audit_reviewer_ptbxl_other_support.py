"""Count source reference dispositions on the previously scored PTB-XL cache.

This read-only metadata audit never evaluates a prediction, reads a waveform,
or parses fold-10 reference values. Its source grammar is the versioned
PhysioNet SCP dictionary, not an inference from diagnostic abbreviations.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

SCORE_SHA = "16447ad196a1881606db8b027a4fb762783caa82706af7ecbf3fee0b9451574b"
SOURCE_SHA = {
    "metadata": "7600de9c1b27d181d850b3c6038a35d7c3ddb6bb33b702e3a20252a6859d216b",
    "dictionary": "ad05b0b1fcae83bb1230755ad9cfc7c96f303feddc08a4a9ad5bdc9ca63bac8f",
    "inventory": "798866dc1dc00d3e81c9fda28711dd0ea57fb57a7fc2ac0a415ad20a97f17107",
}
DIRECT = {"PAC": "PAC", "Flutter": "AFLT", "LBBB": "CLBBB", "ALMI": "ALMI", "ILMI": "ILMI"}
PROXIES = {"NSR": "SR", "LQTS": "LNGQT", "LAE": "LAO/LAE"}
TARGETS = (*DIRECT, "Paced", "2AVB", "3AVB", *PROXIES)
PROFILES = {"P6", "P8", "P4"}
REFERENCE_SCHEMA = "TITAN_V45_PTBXL_OTHER_SUPPORT_V1"


def digest(path):
    with path.open("rb") as stream:
        h = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def identity(path):
    return hashlib.sha256(f"ptbxl\0{path}".encode()).hexdigest()


def disposition(endpoint, codes, marker):
    if endpoint in PROXIES:
        return "non_equivalent_proxy" if PROXIES[endpoint] in codes else "unknown"
    if endpoint in {"2AVB", "3AVB"}:
        return "unknown"
    control = codes.get("NORM", 0) > 0 and codes.keys() <= {"NORM", "SR"} and not marker
    if endpoint == "Paced":
        if "PACE" in codes or marker:
            if marker == "pacemaker" and "PACE" in codes and "NORM" not in codes:
                return "positive" if codes["PACE"] > 0 else "concordant_marker_unknown_scp_likelihood"
            return "ambiguous_pacing_reference"
    elif DIRECT[endpoint] in codes:
        return "positive" if codes[DIRECT[endpoint]] > 0 and "NORM" not in codes else "ambiguous"
    return "explicit_normal_control" if control else "unknown"


def load_rows(metadata, dictionary, inventory, receipt_path, ledger):
    sources = {"metadata": metadata, "dictionary": dictionary, "inventory": inventory}
    if {k: digest(p) for k, p in sources.items()} != SOURCE_SHA or digest(receipt_path) != SCORE_SHA:
        raise ValueError("PTB-XL bridge input or scoring receipt differs")
    receipt = json.loads(receipt_path.read_bytes())
    if (str(receipt["job"]) != "33410" or receipt["fold10_scored"] is not False
            or receipt["references_accessed_for_scoring"] is not False or digest(ledger) != receipt["ledger_sha256"]):
        raise ValueError("old score ledger not sealed against a fold-1-9 inference run")
    with dictionary.open(encoding="utf-8-sig", newline="") as stream:
        records = {row[0]: row[1] for row in csv.reader(stream)}
    if (not set(DIRECT.values()).union(PROXIES.values()) <= records.keys()
            or records["PACE"].casefold() != "normal functioning artificial pacemaker"
            or {"2AVB", "3AVB"} & records.keys()):
        raise ValueError("official statement contract changed")

    flow = {p: Counter() for p in PROFILES}
    statuses = {}
    with ledger.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            key = row["key"]
            if key in statuses or set(row["profiles"]) != PROFILES:
                raise ValueError("duplicated scores or unexpected scoring profile")
            statuses[key] = {p: value["status"] for p, value in row["profiles"].items()}
            for p, value in statuses[key].items():
                flow[p][value] += 1
    if flow != receipt["flow"]:
        raise ValueError("source scoreability counts do not reconcile")
    cache = {}
    for row in json.loads(inventory.read_bytes())["rows"]:
        if row["task"] == "pathology" and row["source"] == "ptbxl":
            key = row["identity_hash"]
            if key in cache or not 1 <= row["fold"] <= 9:
                raise ValueError("duplicate or reserved inventory record")
            cache[key] = (row["fold"], row.get("signal_sha256"))

    eligible, patients, signals, folds = set(), {}, defaultdict(set), Counter()
    counts = {e: defaultdict(Counter) for e in TARGETS}
    groups = {e: defaultdict(lambda: defaultdict(set)) for e in TARGETS}
    markers = Counter()
    reserved = 0
    with metadata.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            fold = int(row["strat_fold"])
            if fold == 10:
                reserved += 1
                continue
            patient = Decimal(row["patient_id"])
            key = identity(row["filename_lr"])
            if (not 1 <= fold <= 9 or not patient.is_finite() or patient != patient.to_integral_value()
                    or patients.setdefault(patient, fold) != fold or key not in statuses or key in eligible):
                raise ValueError("invalid enrollment or source patient crosses the allowed folds")
            eligible.add(key)
            folds[str(fold)] += 1
            if key in cache:
                f, signal = cache[key]
                if f != fold:
                    raise ValueError("metadata and inventory fold differ")
                if signal:
                    signals[signal].add(fold)
            codes = ast.literal_eval(row["scp_codes"])
            if (not isinstance(codes, dict) or not codes.keys() <= records.keys()
                    or any(not math.isfinite(v) or not 0 <= v <= 100 for v in codes.values())):
                raise ValueError("unrecognized or invalid source SCP annotation")
            marker = row["pacemaker"].strip().casefold()
            markers["explicit_marker" if marker == "pacemaker" else "other_nonempty" if marker else "blank"] += 1
            partitions = ["all_folds_1_9", *(p + "_scoreable" for p in sorted(PROFILES)
                            if statuses[key][p] == "scored")]
            for endpoint in TARGETS:
                state = disposition(endpoint, codes, marker)
                for part in partitions:
                    counts[endpoint][part][state] += 1
                    groups[endpoint][part][state].add(patient)
    if eligible != statuses.keys() or not cache.keys() <= eligible or (len(eligible), reserved) != (19601, 2198):
        raise ValueError("full source and scoreable cache enrollment do not reconcile")
    return {
        "schema": REFERENCE_SCHEMA, "source_doi": "10.13026/kfzx-aw45", "source_scoring_job": 33410,
        "source_input_sha256": SOURCE_SHA, "source_score_receipt_sha256": SCORE_SHA,
        "source_private_score_ledger_sha256": receipt["ledger_sha256"],
        "fold10_reference_parsed": False, "fold10_waveforms_accessed": False,
        "historical_independence_certified": False, "inference_or_performance_estimation": False,
        "metadata_ecgs": len(eligible), "source_subjects": len(patients), "cached_records": len(cache),
        "eligible_ecgs_by_fold": folds, "fold10_metadata_count_only": reserved,
        "cached_exact_signal_groups_crossing_folds_1_9": sum(len(v) > 1 for v in signals.values()),
        "distinct_cached_exact_signal_groups": len(signals), "profile_scoring_flow": flow,
        "source_pacing_marker_flow": markers, "no_individual_records_exported": True,
        "endpoint_support": {e: {p: {"ECGs": c, "source_subjects": {s: len(v) for s, v in groups[e][p].items()}}
                                  for p, c in counts[e].items()} for e in TARGETS},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("metadata", "dictionary", "inventory", "receipt", "ledger", "output"):
        parser.add_argument(f"--{arg}", type=Path, required=True)
    args = parser.parse_args()
    report = load_rows(args.metadata, args.dictionary, args.inventory, args.receipt, args.ledger)
    with args.output.open("x", encoding="ascii", newline="\n") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
