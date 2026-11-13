"""Read-only native inventory; stdout contains no private paths or rows."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOTS = (
    "specialist-heads-20261111-v2", "external-validation-20261111",
    "titan-performance-recovery-v1", "titan-corrective-v1", "titan-v45-benchmarkmax-v46",
    "titan-four-reviewers-november-phase1", "titan-four-reviewers-historical-replay",
    "titan-v45-scientific-closure", "titan-v45-two-comment-rigorous",
    "titan-main-integration-audit-20261112",
)
WEIGHTS = {".pt", ".pth", ".safetensors", ".ckpt"}
RELEASE_NAMES = {
    "backbone-v3ag-pathology.pt", "backbone-v3f-original.pt",
    "specialists-v3ag-primary4-calibrated.pt", "specialists-v3p-e008-primary6-diagnostic.pt",
    "specialists-v3q-primary8-best-candidate.pt", "external-dev-pathology-ptbxl-fold10.tar.zst",
    "external-dev-rhythm-chapman-shaoxing.tar.zst",
}
JOBS = (
    16748, 16749, 16750, 16751, 16752, 16753, 16754, 16755, 16756, 16757, 16758, 16759,
    16768, 16781, 32668, 32669, 32677, 32728, 32758, 32761, 32763, 32805,
    33296, 33355, 33357, 33362, 33390, 33396, 33399, 33410, 33414, 33474, 33572, 33573,
    33574, 33575, 33596, 33697, 33704, 33720, 33737, 33747, 33795, 33796, 33799, 33801,
    33803, 33805, 33807, 33825, 33826, 33827, 33829, 33831, 33832,
)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--root", action="append", choices=(*ROOTS, "domain-adaptation-v1"))
    a = p.parse_args()
    artifacts, roots, failures = [], {}, []
    for group in a.root or ROOTS:
        root = a.base / group
        roots[group] = root.is_dir()
        if not roots[group]:
            continue
        for path in sorted(root.rglob("*")):
            if path.is_symlink() or not path.is_file() or len(path.relative_to(root).parts) > 9:
                continue
            is_weight = path.suffix.lower() in WEIGHTS
            name = path.name
            stable_release_name = name if name in RELEASE_NAMES else ""
            selected = is_weight or stable_release_name or path.suffix.lower() in {
                ".log", ".db", ".sqlite", ".sqlite3",
            } or (path.suffix.lower() in {".json", ".npz", ".jsonl", ".csv"}
                  and re.search(r"receipt|aggregate|score|prediction|split|protocol|manifest|readback|epoch|calibrat|inventory|decision", name, re.I))
            if not selected:
                continue
            rel = path.relative_to(root).as_posix()
            loc = hashlib.sha256((group+"/"+rel).encode()).hexdigest()
            before = path.stat()
            try:
                sha = digest(path)
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise OSError("file changed during read")
            except OSError:
                failures.append({"source": group, "locator_sha256": loc})
                continue
            job = re.search(r"(?:^|[-_])([123]\d{4})(?:[./_-]|$)", rel)
            artifacts.append({"source": group, "locator_sha256": loc, "sha256": sha,
                              "bytes": before.st_size, "format": path.suffix.lower(),
                              "checkpoint": is_weight, "release_name": stable_release_name,
                              "path_job_hint_not_producer": job.group(1) if job else ""})
    raw = subprocess.check_output(["sacct", "-X", "-j", ",".join(map(str, JOBS)), "-n", "-P", "-o",
                                   "JobIDRaw,State,ExitCode,Elapsed,Start,End"], text=True)
    fields = "job state exit elapsed start_scheduler_local end_scheduler_local".split()
    scheduler = [dict(zip(fields, line.split("|"), strict=True)) for line in raw.splitlines() if line]
    out = {"scope": "named CEDIA roots, selected evidence formats, files at depth <=9; no training",
           "roots": roots, "artifacts": artifacts, "read_failures": failures, "scheduler": scheduler,
           "restricted_paths_or_rows_exported": False}
    with a.output.open("x", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main()
