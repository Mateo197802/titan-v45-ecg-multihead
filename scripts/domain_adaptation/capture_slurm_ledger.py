"""Capture scheduler state for only the explicitly declared study jobs."""
from __future__ import annotations

import argparse
import csv
import io
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def capture(entries, start):
    jobs = {}
    for item in entries:
        job, resource, role = item.split(":", maxsplit=2)
        if not job.isdecimal() or job in jobs or resource not in {"cpu", "gpu"} or not re.fullmatch(r"[a-z0-9_]+", role):
            raise ValueError("unregistered or repeated job metadata")
        jobs[job] = resource, role
    stdout = subprocess.check_output(["sacct", "-X", "-S", start, "-j", ",".join(jobs), "--parsable2",
                                     "--format=JobID,State,ExitCode,Elapsed,Start,End"], text=True)
    returned = list(csv.DictReader(io.StringIO(stdout), delimiter="|"))
    if len(returned) != len(jobs) or {r["JobID"] for r in returned} != jobs.keys():
        raise ValueError("scheduler did not return exactly the requested job set")
    utc = datetime.now(timezone.utc).isoformat()
    return [{"job_id": r["JobID"], "role": jobs[r["JobID"]][1], "resource": jobs[r["JobID"]][0],
             "state": r["State"], "exit_code": r["ExitCode"], "elapsed": r["Elapsed"],
             "start_scheduler_local": r["Start"], "end_scheduler_local": r["End"],
             "captured_at_utc": utc} for r in returned]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("start_date")
    parser.add_argument("output", type=Path)
    parser.add_argument("jobs", nargs="+", help="job:cpu_or_gpu:role")
    args = parser.parse_args()
    rows = capture(args.jobs, args.start_date)
    with args.output.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
