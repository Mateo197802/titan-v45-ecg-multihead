"""Audit an openly licensed complementary reference source, without model outputs."""
from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from compare_reviewer_baseline import digest
from score_reviewer_closure_ludb import sha256, source_manifest, write_new


def fetch(base, name):
    for retry in range(3):
        try:
            with urlopen(base + name, timeout=20) as response:
                return response.read()
        except (OSError, URLError):
            if retry == 2:
                raise
            time.sleep(2**retry)
    raise RuntimeError("unreachable fetch state")


def normalize(raw):
    return " ".join(raw.casefold().split())


def source_references(header, config):
    fields = defaultdict(set)
    for raw in header.decode("latin-1").splitlines():
        match = re.fullmatch(r"\s*#\s*([^:]+):\s*(.*)", raw)
        if match:
            field, value = map(normalize, match.groups())
            if field in (config["condition_field"], config["territory_field"]):
                fields[field].add(value)
    condition, territory = fields[config["condition_field"]], fields[config["territory_field"]]
    if len(condition) > 1 or len(territory) > 1:
        return {key: "discordant_header" for key in config["territories"]}
    no_territory = not territory or territory <= {"n/a", "na", "none", "-", ""}
    return {key: (
        "positive" if condition == {config["required_condition"]} and territory == {name}
        else "explicit_control" if condition == {config["explicit_control"]} and no_territory
        else "unknown")
        for key, name in config["territories"].items()}


def summarize(refs, endpoints):
    report = {}
    for key in endpoints:
        by_patient = defaultdict(set)
        states = Counter()
        for row in refs:
            state = row["references"][key]
            by_patient[row["source_subject"]].add(state)
            states[state] += 1
        counts = Counter()
        for value in by_patient.values():
            observed = value & {"positive", "explicit_control"}
            state = next(iter(observed)) if len(observed) == 1 else (
                "discordant_known_polarities" if len(observed) == 2 else "no_known_polarity")
            counts[state] += 1
        report[key] = {
            "record_states": dict(states), "subject_states": dict(counts),
            "eligible_for_territory_control_comparison": min(counts["positive"], counts["explicit_control"]) >= 5,
        }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_bytes())
    base = config["source_url"]
    if base != "https://physionet.org/files/ptbdb/1.0.0/":
        raise ValueError("unexpected source/version")
    names = fetch(base, "RECORDS")
    checks = fetch(base, config["source_manifest"])
    index = source_manifest(checks.decode("ascii"))
    entries = names.decode("ascii").splitlines()
    if (len(entries) != config["records"] or len(set(entries)) != len(entries)
            or any(not re.fullmatch(r"patient[0-9]{3}/[A-Za-z0-9_-]+", item) for item in entries)
            or len({x.split("/")[0] for x in entries}) != config["subjects"]
            or sha256(names) != index["RECORDS"]):
        raise ValueError("provider record enrollment, subject namespace or digest differs")
    out = args.output_dir
    out.mkdir(mode=0o700)
    (out / "RECORDS").write_bytes(names)
    (out / "publisher-SHA256SUMS.txt").write_bytes(checks)
    headers = out / "private-headers"
    headers.mkdir(mode=0o700)

    def header(entry):
        name = entry + ".hea"
        raw = fetch(base, name)
        checksum = sha256(raw)
        if checksum != index[name]:
            raise ValueError("provider header checksum differs")
        target = headers / name
        target.parent.mkdir(mode=0o700, exist_ok=True)
        target.write_bytes(raw)
        return {"record": entry, "source_subject": entry.split("/")[0], "header_sha256": checksum,
                "references": source_references(raw, config)}

    with ThreadPoolExecutor(max_workers=6) as pool:
        refs = list(pool.map(header, entries))
    private = out / "private-reference-manifest.jsonl"
    with private.open("x", encoding="utf-8") as stream:
        for r in refs:
            stream.write(json.dumps(r, separators=(",", ":")) + "\n")
    write_new(out / "aggregate.json", {
        "schema": config["schema"], "scope": "complete provider enrollment; enriched comparator, no inference",
        "config_sha256": digest(args.config), "source": config["dataset"], "version": config["version"],
        "source_records": len(refs), "source_subjects": config["subjects"], "source_record_index_sha256": sha256(names),
        "publisher_checksum_manifest_sha256": sha256(checks), "verified_headers": len(refs),
        "reference_manifest_sha256": digest(private), "endpoints": summarize(refs, config["territories"]),
        "model_performance_computed": False, "historical_independence_certified": False,
        "waveforms_downloaded": False, "no_individual_records_exported": True,
    })


if __name__ == "__main__":
    main()
