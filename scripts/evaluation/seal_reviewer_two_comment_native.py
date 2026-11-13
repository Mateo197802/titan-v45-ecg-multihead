"""Capture CEDIA accounting and verify native seals before any aggregate export."""
import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

from verify_reviewer_two_comment_rigorous import (
    check_ablation,
    check_runtime,
    check_selective,
    require,
)

EXPERIMENTS = {
    "selective": ("R2_4K_COVERAGE_RISK_AND_FALSE_NEGATIVES.json", check_selective),
    "morphology": ("R2_3F_ABLATION_CONFIRMATORY_RESULTS.json", check_ablation),
    "runtime": ("RUNTIME_AND_CASCADE_AGGREGATE.json", check_runtime),
}


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def accounting(ids):
    cols = "JobIDRaw,State,Elapsed,ExitCode,Start,End,NodeList,Partition"
    raw = subprocess.check_output(["sacct", "-X", "-j", ",".join(ids), "-n", "-P", "-o", cols], text=True)
    fields = "job state elapsed exit start end node partition".split()
    rows = (dict(zip(fields, line.split("|"), strict=True)) for line in raw.splitlines() if line)
    return {row["job"]: row for row in rows if row["job"] in ids}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--attempt", nargs=2, action="append", default=[], metavar=("JOB", "EXCLUSION_REASON"))
    for name in EXPERIMENTS:
        p.add_argument(f"--{name}", nargs=2, required=True, metavar=("JOB", "FULL_COMMIT"))
    a = p.parse_args()
    scheduler = accounting([getattr(a, name)[0] for name in EXPERIMENTS] + [i for i, _ in a.attempt])
    receipt = {"schema": "TITAN_V45_TWO_COMMENT_NATIVE_RECEIPTS_V1", "experiments": {},
               "excluded_attempts": [{"scheduler": scheduler[i], "reason": why} for i, why in a.attempt],
               "individual_data_exported": False}
    for name, (filename, check) in EXPERIMENTS.items():
        job, commit = getattr(a, name)
        state = scheduler[job]
        require(state["state"] == "COMPLETED" and state["exit"] == "0:0", f"{name} not complete")
        suffix = commit[:7]
        archive = Path.home()/f"titan-two-comment-{suffix}.tar"
        native_code = a.root/f"code-{suffix}"
        out = a.root/f"{name}-{job}"
        with tarfile.open(archive) as tar:
            require(tar.pax_headers.get("comment") == commit, f"{name} archive commit mismatch")
        for folder, manifest in ((native_code, "CODE_SHA256SUMS"), (out, "SHA256SUMS")):
            subprocess.run(["sha256sum", "--check", "--status", manifest], cwd=folder, check=True)
        aggregate = out/"aggregate.json"
        result = json.loads(aggregate.read_bytes())
        require(result["job"] == job and result["individual_data_exported"] is False, f"{name} aggregate lineage")
        check(result)
        row = {**state, "code_commit": commit, "code_archive_sha256": digest(archive),
               "code_manifest_sha256": digest(native_code/"CODE_SHA256SUMS"),
               "output_manifest_sha256": digest(out/"SHA256SUMS"),
               "aggregate_filename": filename, "aggregate_sha256": digest(aggregate),
               "log_sha256": digest(a.root/f"{name}-{job}.log")}
        if name == "morphology":
            expected = result["private_predictions_sha256"]
            require(digest(out/"private-ablation-predictions.jsonl") == expected, "ablation ledger hash")
            row["restricted_prediction_ledger_sha256"] = expected
        elif name == "runtime":
            expected = result["fallback"]["individual_ledger_sha256"]
            require(digest(out/"private-cascade.jsonl") == expected, "cascade ledger hash")
            row["restricted_cascade_ledger_sha256"] = expected
        receipt["experiments"][name] = row
    with a.output.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
