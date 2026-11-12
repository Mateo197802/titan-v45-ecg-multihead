"""Verify native SLURM results and publication candidates without copying private files."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

SPH = 25770
JOBS = {
    "33355": ("phase", "sph-frozen", ("scoring-receipt.json",), True),
    "33356": ("phase", "repeat-audit", ("aggregate.json",), True),
    "33357": ("phase", "sph-ece-report", ("aggregate.json", "aggregation-receipt.json", "ece-correction-receipt.json"), True),
    "33362": ("phase", "selective", ("aggregate.json", "policy.json"), True),
    "33469": ("history", "p4-cascade", ("aggregate.json",), True),
    "33470": ("history", "rhythm-cascade", ("aggregate.json",), True),
    "33471": ("history", "replay-diagnostics", ("aggregate.json",), False),
    "33369": ("phase", "auxiliary", ("aggregate.json",), True),
    "33474": ("history", "retrained", ("aggregate.json", "fit-receipt.json", "features/extraction-receipt.json"), True),
    "33390": ("phase", "pathology-other", ("aggregate.json", "fit-receipt.json"), True),
    "33396": ("phase", "rhythm-other", ("aggregate.json", "fit-receipt.json"), True),
    "33399": ("phase", "population-contrast", ("aggregate.json",), True),
    "33472": ("history", "replay-contrast", ("aggregate.json",), True),
    "33410": ("phase", "ptbxl-bridge", ("aggregate.json", "scoring-receipt.json"), True),
    "33414": ("phase", "joint-selective", ("aggregate.json", "joint-policy.json"), True),
    "33473": ("history", "morph-sensitivity", ("p4-aggregate.json", "rhythm-aggregate.json"), True),
}
SUPERSEDED = ("33363", "33364", "33365", "33373", "33381", "33403", "33416",
              "33454", "33455", "33456", "33457", "33458", "33459")
REPLAY_COMMITS = {"33469": "02019b832fafecd0c263ea556c70f16fa0a50ccf",
                  "33470": "cfe6d59fa5cc4be10de0d7c6803fa5208fae0072"}
PRIVATE_FIELDS = {
    "ecg_id", "patient_id", "record_id", "window_key", "record_path", "header_path", "record_base",
    "relative_record", "signal_sha256", "signal_sha256_canonical_f64", "state_dict", "record_ids",
    "patient_ids", "window_keys", "optimizer_state_dict", "original_predictions",
}
PRIVATE_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|/home/|/tmp/|/scratch/|/mnt/|\\\\)", re.I)


def digest(path):
    with path.open("rb") as f:
        h = hashlib.sha256()
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
        return h.hexdigest()


def validate_public(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.casefold() in PRIVATE_FIELDS or PRIVATE_PATH.search(key):
                raise ValueError("private key or path in public candidate")
            validate_public(item)
    elif isinstance(value, list):
        for item in value:
            validate_public(item)
    elif isinstance(value, str) and PRIVATE_PATH.search(value):
        raise ValueError("private path in public candidate")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite value in public candidate")


def accounting(text):
    result = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        job, state, code, elapsed = line.rstrip("|").split("|")
        if job not in JOBS and job not in SUPERSEDED:
            continue
        if job in result:
            raise ValueError("duplicate native accounting row")
        result[job] = {"state": state.split()[0], "exit_code": code, "elapsed": elapsed}
    return result


def protected_path(directory, name):
    target = directory / name
    if not target.is_file() or target.is_symlink() or target.resolve() != target.absolute():
        raise ValueError("missing, symlinked or noncanonical output")
    return target


def seal_entry(directory, target):
    manifest = protected_path(directory, "SHA256SUMS")
    matches = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        check, path = line.split(maxsplit=1)
        path = Path(path.removeprefix("*"))
        if (directory / path).absolute() == target.absolute():
            matches.append(check)
    if len(matches) != 1 or matches[0] != digest(target):
        raise ValueError("producer seal does not match the public candidate")
    return matches[0]


def count(value, message):
    if type(value) is not int or value < 0:
        raise ValueError(message)
    return value


def total(values):
    return sum(count(v, "invalid aggregate count") for v in values)


def check_selective(stats):
    held, scored, accepted, abstained, unscored = (count(stats[k], "invalid selective count") for k in (
        "held_records", "scored_records", "accepted", "abstained", "technical_unscored"))
    if held != scored+unscored or scored != accepted+abstained:
        raise ValueError("selective routes do not exhaust the held denominator")
    for field, n, d in (("abstention_all_held", abstained, held), ("abstention_scored", abstained, scored),
                        ("coverage_all_held", accepted, held), ("coverage_scored", accepted, scored)):
        if stats[field] != (n/d if d else None):
            raise ValueError("selective denominator does not match its reported ratio")
    for e in stats["endpoints"].values():
        b, a, q = (e["routes"][k] for k in ("baseline", "accepted", "abstained"))
        for table, expected in ((b, scored), (a, accepted), (q, abstained)):
            if table["n"] != expected or total(table[k] for k in ("tn", "fp", "fn", "tp")) != expected:
                raise ValueError("selective confusion table has the wrong denominator")
        if any(b[k] != a[k]+q[k] for k in ("tn", "fp", "fn", "tp")):
            raise ValueError("selective confusion tables disagree")


def scientific_checks(job, value, earlier, baseline_digest):
    if job == "33355":
        f = value["flow"]
        if (value["stage"] != "full_population" or f["metadata_records"] != SPH
                or total(f["status_counts"].values()) != SPH
                or f["status_counts"].get("scored", 0) != f["scored_records"]
                or value["labels_used_for_inference_or_routing"] is not False):
            raise ValueError("baseline provenance or source denominator failed")
    elif job == "33357":
        if (value["full_population_flow"]["source_metadata_records"] != SPH
                or value["scoring_receipt_sha256"] != baseline_digest
                or value["full_population_flow"]["quarantine_rate"] is not None):
            raise ValueError("baseline metrics not bound to the no-policy baseline")
        for e in value["endpoints"].values():
            m = e["metrics"]
            if total(m[k] for k in ("tn", "fp", "fn", "tp")) != e["scored_evaluable_records"]:
                raise ValueError("endpoint confusion table does not match scored references")
    elif job in {"33362", "33414"}:
        profiles = value["profiles"].values() if job == "33362" else [value["joint_metrics"]]
        for stats in profiles:
            check_selective(stats)
        if job == "33414":
            if total(n for counts in value["source_stratum_route_counts"].values() for n in counts.values()
                     ) != value["joint_metrics"]["held_records"]:
                raise ValueError("joint source strata do not reconcile")
            for e in value["positive_statement_disposition"].values():
                if total(e[k] for k in (
                    "accepted_emitted_correct_positive", "accepted_emitted_missed_positive",
                    "abstained_reference_positive_no_prediction",
                    "technically_unscored_reference_positive_no_prediction",
                )) != e["held_statement_positives"]:
                    raise ValueError("joint positive disposition does not reconcile")
    elif job == "33369":
        if value["source_ecgs"] != SPH or value["baseline_receipt_sha256"] != baseline_digest:
            raise ValueError("auxiliary support is not bound to the full SPH baseline")
        for e in value["endpoints"].values():
            if total(e["all_source_reference_states"].values()) != SPH:
                raise ValueError("auxiliary reference flow is incomplete")
    elif job == "33390":
        for e in value["endpoints"].values():
            if total(n for flow in e["all_source_reference_and_scoring_flow"].values()
                     for n in flow.values()) != value["population"]["metadata_ecgs_folds_1_to_9"]:
                raise ValueError("pathology Other full reference flow is incomplete")
    elif job == "33396":
        for e in value["endpoints"].values():
            if total(n for flow in e["all_metadata_reference_scoring_flow"].values()
                     for n in flow.values()) != SPH:
                raise ValueError("rhythm Other full reference flow is incomplete")
    elif job == "33399":
        if value["baseline_receipt_sha256"] != baseline_digest:
            raise ValueError("population contrast not bound to baseline")
        for p in value["profiles"].values():
            if total(v["metadata_ecgs"] for v in p["reference_strata"].values()) != SPH:
                raise ValueError("population strata do not exhaust SPH")
    elif job == "33472":
        p4 = value["archived_predictions_versus_current_native"]["P4"]
        if (total(p["archived_rows"] for p in p4.values()) != 962
                or total(p["matched_rows"] for p in p4.values()) != value["matched_p4_panel_observations"]
                or any(p["matched_rows"]+p["missing_scores"] != p["archived_rows"] for p in p4.values())):
            raise ValueError("P4 archived panel observations do not reconcile")
        for branch, parent in (("P4", "33469"), ("rhythm", "33470")):
            if value["provenance"][branch]["current"]["runner_aggregate_sha256"] != earlier[parent]:
                raise ValueError("current replay report not bound to native parent")
    elif job == "33410":
        if value["metadata_ecgs"] != 19601 or total(c["metadata"] for c in value["flow_by_official_fold"].values()) != 19601:
            raise ValueError("PTB-XL metadata denominator does not reconcile")
        if set(value["flow_by_official_fold"]) != {str(i) for i in range(1, 10)}:
            raise ValueError("unexpected PTB-XL fold in analyzed data")
    elif job == "33473":
        for p, r in value["profiles"].items():
            if r["intended_records"] != {"P4": 733, "P6": 1643, "P8": 2193}[p] or not (
                0 <= r["decision_changes"] <= r["paired_scored"] <= r["intended_records"]
            ):
                raise ValueError("morphology sensitivity counts are inconsistent")


def bundle_checks(job, directory, items, files):
    if job == "33355":
        receipt = items["scoring-receipt.json"]
        actual = digest(protected_path(directory, "private-predictions.jsonl"))
        if actual != receipt["ledger_sha256"]:
            raise ValueError("private scoring ledger differs from its receipt")
    elif job in REPLAY_COMMITS:
        commit = protected_path(directory, "commit.txt")
        seal_entry(directory, commit)
        seal_entry(directory, protected_path(directory, "ledger.jsonl"))
        if commit.read_text(encoding="utf-8").strip() != REPLAY_COMMITS[job]:
            raise ValueError("historical replay used an unexpected source commit")
    elif job == "33362":
        policy, result = (items[n] for n in ("policy.json", "aggregate.json"))
        if (files["policy.json"]["sha256"] != result["policy_sha256"]
                or policy["reference_labels_used"] is not False or policy["held_scores_used_for_selection"] is not False
                or result["cascade_implemented"] is not False):
            raise ValueError("selective outputs not bound to the frozen reference-free policy")
        for file, expected in (("private-split.jsonl", policy["private_split_sha256"]),
                               ("private-routes.jsonl", result["private_route_ledger_sha256"])):
            if digest(protected_path(directory, file)) != expected:
                raise ValueError("private selective output differs from producer hash")
    elif job in {"33474", "33390", "33396"}:
        fit, evaluated = (items[n] for n in ("fit-receipt.json", "aggregate.json"))
        field = "model_sha256" if job == "33474" else "private_model_sha256"
        if (fit["held_outcomes_evaluated"] is not False or fit[field] != evaluated[field]
                or fit["binding"] != evaluated["binding"]
                or digest(protected_path(directory, "private-models.json")) != fit[field]):
            raise ValueError("held evaluation is not bound to the pre-evaluation checkpoint")
        if job == "33474":
            key = "features/extraction-receipt.json"
            extraction = items[key]
            if (fit["binding"]["extraction_receipt_sha256"] != files[key]["sha256"]
                    or extraction["zeroed_morphology_calls"] <= 0
                    or extraction["arms"]["with_morphology"]["asset_hashes"]
                    != extraction["arms"]["without_morphology"]["asset_hashes"]):
                raise ValueError("matched extraction did not preserve the common release assets")
    elif job == "33410":
        receipt, result = (items[n] for n in ("scoring-receipt.json", "aggregate.json"))
        if (files["scoring-receipt.json"]["sha256"] != result["scoring_receipt_sha256"]
                or receipt["references_accessed_for_scoring"] is not False or receipt["fold10_scored"] is not False
                or digest(protected_path(directory, "private-scores.jsonl")) != receipt["ledger_sha256"]):
            raise ValueError("PTB-XL references or sealed baseline do not reconcile")
    elif job == "33414":
        result = items["aggregate.json"]
        if (files["joint-policy.json"]["sha256"] != result["joint_policy_sha256"]
                or digest(protected_path(directory, "private-joint-routes.jsonl"))
                != result["private_joint_route_ledger_sha256"]):
            raise ValueError("joint outputs not bound to their policy and ledger")


def verify(roots, states):
    inventory, failures, earliest = {}, {}, {}
    for job, (root, folder, names, sealed) in JOBS.items():
        native = states.get(job)
        if not native or (native["state"], native["exit_code"]) != ("COMPLETED", "0:0"):
            inventory[job] = {"scheduler": native, "result_status": "not_verified_no_successful_job"}
            continue
        directory = roots[root].resolve() / f"{folder}-{job}"
        verified, items = {}, {}
        try:
            for idx, name in enumerate(names):
                path = protected_path(directory, name)
                file_hash = seal_entry(directory, path) if sealed else digest(path)
                result = json.loads(path.read_bytes())
                if not isinstance(result, dict):
                    raise ValueError("public result is not a JSON object")
                validate_public(result)
                reported_job = result.get("job", result.get("audit_job", result.get("job_id")))
                if reported_job is not None and str(reported_job) != job:
                    raise ValueError("producer job in public candidate does not match")
                if idx == 0 or job == "33473":
                    scientific_checks(job, result, earliest, earliest.get("33355"))
                verified[name] = {"sha256": file_hash, "producer_checksum_verified": sealed}
                items[name] = result
            bundle_checks(job, directory, items, verified)
            earliest[job] = next(iter(verified.values()))["sha256"]
        except (OSError, KeyError, TypeError, ValueError) as exc:
            # Keep raw exceptions and data out of the shareable receipt.
            failures[job] = type(exc).__name__
        inventory[job] = {"scheduler": native, "result_status": "verification_failed" if job in failures else "verified",
                          "aggregate_candidates": verified if job not in failures else {}}
    return {"schema": "TITAN_V45_NOVEMBER_DELIVERY_VERIFICATION_V1", "jobs": inventory,
            "superseded_jobs_not_used": {j: states.get(j) for j in SUPERSEDED},
            "verification_errors": failures, "verified_jobs": len(earliest), "required_jobs": len(JOBS),
            "public_export_performed": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase-root", type=Path, required=True)
    p.add_argument("--history-root", type=Path, required=True)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    fields = subprocess.check_output([
        "sacct", "-S", "2026-11-11", "-X", "-j", ",".join((*JOBS, *SUPERSEDED)), "-n", "-P",
        "-o", "JobIDRaw,State,ExitCode,Elapsed",
    ], text=True)
    result = verify({"phase": a.phase_root, "history": a.history_root}, accounting(fields))
    report = json.dumps(result, indent=2, allow_nan=False)+"\n"
    if a.output:
        with a.output.open("x", encoding="utf-8") as f:
            f.write(report)
    else:
        print(report, end="")
    return int(bool(result["verification_errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
