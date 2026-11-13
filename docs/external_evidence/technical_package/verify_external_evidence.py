"""Verify the fixed public package, directory or ZIP, with Python's standard library."""
from __future__ import annotations

import argparse
import io
import json
import posixpath
import re
import stat
import sys
from pathlib import Path
from zipfile import ZipFile

# The standalone verifier must not create an unsealed file inside the extraction.
_previous_bytecode_policy = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    from external_evidence_tables import (
        PRIMARY,
        SOURCE_FILES,
        csv_rows,
        git_blob,
        require,
        sha,
        tables,
        verified_sources,
    )
finally:
    sys.dont_write_bytecode = _previous_bytecode_policy

ZIP_NAME = "TITAN_V45_EXTERNAL_EVIDENCE_PACKAGE.zip"
TECH = "technical_package"
MANIFEST = f"{TECH}/MANIFEST.json"
SUMS = f"{TECH}/SHA256SUMS.txt"
TRACE = f"{TECH}/SOURCE_TRACEABILITY.csv"
SNAPSHOT = f"{TECH}/source_snapshot"
VERIFIERS = ("external_evidence_tables.py", "verify_external_evidence.py")


def snapshot_path(name):
    return f"{SNAPSHOT}/{SOURCE_FILES[name].removeprefix('docs/domain_adaptation/')}"


CORE = {
    "PRIMARY_RESULTS_SUMMARY.md", "METHODS_AND_COHORT.md", "FIGURE_CAPTIONS.md", "ALLOWED_AND_DISALLOWED_CLAIMS.md",
    "PRIMARY_RESULTS_TABLE.csv", "PER_CLASS_RESULTS.csv", "BASELINE_PER_CLASS_RESULTS.csv", "BASELINE_COMPARISON.csv",
    "SENSITIVITY_PPV.csv", "CONFUSION_MATRICES.csv",
}
SUPPORT = {
    "SECONDARY_EVIDENCE_INDEX.md", "HISTORICAL_FROZEN_EXTERNAL_SCREENING.md", "DOMAIN_ADAPTATION_HISTORY.md",
    "CORRECTIVE_EXPERIMENTS.md", "AUTONOMOUS_LOOP_RESULTS.md", "MORPHOLOGY_AND_CASCADE_LIMITATIONS.md",
    "P4_VALIDATION_BOUNDARY.md", "REPRODUCIBILITY_AND_PROVENANCE.md",
}
FIGURES = ("figure_01_global_comparison", "figure_02_classwise_metrics", "figure_03_sensitivity_ppv",
           "figure_04_confusion_matrices", "figure_05_observed_precision_recall")
PAYLOAD = (
    {"README.md", TRACE, f"{TECH}/PACKAGE_VERIFICATION.md"}
    | {f"manuscript_core/{name}" for name in CORE}
    | {f"supporting_evidence/{name}" for name in SUPPORT}
    | {f"figures/{stem}.{ext}" for stem in FIGURES for ext in ("svg", "pdf", "png")}
    | {snapshot_path(name) for name in SOURCE_FILES}
    | {f"{TECH}/{name}" for name in VERIFIERS}
)
MEMBERS = PAYLOAD | {MANIFEST, SUMS}
REPO_URL = "https://github.com/Mateo197802/titan-v45-ecg-multihead"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
PRIVATE_FIELDS = {"patient_id", "record_id", "exam_id", "trace_file", "signal", "waveform", "score"}
SECRET = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{20,}|"
                    r"(?:[A-Za-z]:\\Users\\|/home/diego\.)")
LIMIT = 8_000_000


def source_snapshot(payload):
    return {name: payload[snapshot_path(name)] for name in SOURCE_FILES}


def checksums(payload):
    return "".join(f"{sha(data)}  {path}\n" for path, data in sorted(payload.items()) if path != SUMS).encode()


def read_zip(raw):
    with ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        require(len(infos) == len(MEMBERS) and {i.filename for i in infos} == MEMBERS,
                "ZIP has missing, duplicate, extra or unsafe members")
        require(sum(i.file_size for i in infos) <= LIMIT and all(
            not stat.S_ISLNK(i.external_attr >> 16) and not i.is_dir() and not i.flag_bits & 1 for i in infos
        ), "invalid archive member type, encryption or expanded size")
        require(z.testzip() is None, "ZIP CRC failure")
        return {i.filename: z.read(i) for i in infos}


def read_directory(folder):
    result = {}
    for name in MEMBERS:
        file = folder / name
        require(file.is_file() and not file.is_symlink() and file.resolve().is_relative_to(folder.resolve()),
                f"missing or unsafe package file: {name}")
        result[name] = file.read_bytes()
    allowed = MEMBERS | {ZIP_NAME, ZIP_NAME + ".sha256"}
    require({p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()} <= allowed,
            "unexpected file in package directory")
    return result


def verify_text(name, data):
    if Path(name).suffix not in {".md", ".csv", ".json", ".svg"}:
        return
    body = data.decode("utf-8")
    require(not SECRET.search(body), f"restricted path or credential in {name}")
    if name.endswith(".csv"):
        header = body.splitlines()[0].split(",")
        require(not PRIVATE_FIELDS.intersection(header), f"individual record columns in {name}")
    if name.endswith(".md"):
        for target in re.findall(r"\]\(([^)]+)\)", body):
            if target.startswith("https://") or target.startswith("#") or target == ZIP_NAME:
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), target.split("#")[0]))
            require(resolved in MEMBERS or any(p.startswith(resolved.rstrip("/") + "/") for p in MEMBERS),
                    f"broken relative link {name}: {target}")


def verify_payload(payload, repo=None):
    require(set(payload) == MEMBERS and sum(map(len, payload.values())) <= LIMIT, "invalid payload inventory")
    require(payload[SUMS] == checksums(payload), "checksum manifest mismatch")
    manifest = json.loads(payload[MANIFEST])
    require(manifest["primary_commit"] == PRIMARY and manifest["scope"] == "WITHIN_CODE_HELD_OUT",
            "incorrect primary source")
    require(manifest["status"] == {
        "WITHIN_CODE_HELD_OUT_EVALUATION": "COMPLETED", "INDEPENDENT_INSTITUTIONAL_VALIDATION": "NOT_EVALUATED",
        "P4_EXTERNAL_VALIDATION": "NOT_EVALUATED", "MODEL_PROMOTION": "NOT_AUTHORIZED", "MANUSCRIPT_MODIFIED": False,
    }, "scientific boundary mismatch")
    require(set(manifest["files"]) == PAYLOAD and all(
        v["sha256"] == sha(payload[name]) and v["bytes"] == len(payload[name]) for name, v in manifest["files"].items()
    ), "file digest or length mismatch")
    for name, data in payload.items():
        verify_text(name, data)
    src = source_snapshot(payload)
    if repo:
        require(src == verified_sources(repo), "public snapshot differs from the exact original Git commit")
    for name, wanted in tables(src).items():
        require(payload[f"manuscript_core/{name}"] == wanted, f"derived table changed: {name}")
    trace = csv_rows(payload[TRACE])
    seen = set()
    primary_seen = set()
    for r in trace:
        commit, path, digest = r["commit"], r["source_path"], r["sha256"]
        require((commit, path) not in seen and SHA256.fullmatch(digest)
                and re.fullmatch(r"[0-9a-f]{40}", commit)
                and r["url"] == f"{REPO_URL}/blob/{commit}/{path}", "invalid trace record")
        seen.add((commit, path))
        if r["tier"] == "A":
            name = Path(path).name
            require(commit == PRIMARY and SOURCE_FILES.get(name) == path and r["disposition"] == snapshot_path(name)
                    and sha(src[name]) == digest, "original snapshot trace mismatch")
            primary_seen.add(name)
        if repo:
            require(sha(git_blob(repo, commit, path)) == digest, f"upstream blob mismatch: {path}")
    require(primary_seen == set(SOURCE_FILES), "incomplete primary traceability")
    require({r["pr"] for r in trace if r["tier"] == "B"} >= {"6", "10", "11", "12", "15", "16"},
            "incomplete supplementary traceability")
    require(b"P4_EXTERNAL_MACRO_F1: NOT_ESTIMABLE" in payload["supporting_evidence/P4_VALIDATION_BOUNDARY.md"],
            "P4 result must remain separate")
    for stem in FIGURES:
        require(b"<svg" in payload[f"figures/{stem}.svg"][:1024]
                and payload[f"figures/{stem}.pdf"].startswith(b"%PDF-")
                and payload[f"figures/{stem}.png"].startswith(b"\x89PNG\r\n\x1a\n"), "invalid figure format")
    return {"members": len(payload), "source_trace_rows": len(trace), "primary_models": 3, "endpoints": 5}


def verify(path, repo=None):
    if path.is_file():
        require(path.stat().st_size <= LIMIT, "compressed archive exceeds fixed package limit")
        return verify_payload(read_zip(path.read_bytes()), repo)
    payload = read_directory(path)
    result = verify_payload(payload, repo)
    archive = path / ZIP_NAME
    if archive.exists():
        require(archive.stat().st_size <= LIMIT, "compressed archive exceeds fixed package limit")
        raw = archive.read_bytes()
        require(read_zip(raw) == payload, "ZIP and repository payload differ")
        require((path / (ZIP_NAME + ".sha256")).read_text(encoding="ascii") == f"{sha(raw)}  {ZIP_NAME}\n",
                "outer ZIP checksum mismatch")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--repo", type=Path, help="add original Git blob verification")
    args = parser.parse_args()
    print(json.dumps(verify(args.path, args.repo), sort_keys=True))
