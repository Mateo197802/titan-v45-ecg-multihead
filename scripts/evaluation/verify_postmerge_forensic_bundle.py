"""Build or verify the sanitized forensic deliverables; never include evidence bytes."""
import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

DOCS = {
    "POSTMERGE_FORENSIC_AUDIT_REPORT.md", "MASTER_EXPERIMENT_INVENTORY.csv",
    "MASTER_ARTIFACT_SHA256_LEDGER.csv", "CHECKPOINT_IDENTITY_AND_LINEAGE.csv",
    "TRAINING_JOB_PROVENANCE_MATRIX.csv", "DATASET_SPLIT_AND_LEAKAGE_AUDIT.md",
    "METRICS_INDEPENDENT_RECALCULATION.csv", "EXPERIMENT_TO_CLAIM_TRACEABILITY.csv",
    "SCIENTIFIC_CLAIM_VERIFICATION_MATRIX.csv", "DOCUMENTATION_CONSISTENCY_AUDIT.md",
    "MODEL_AND_RELEASE_INTEGRITY_REPORT.md", "PR15_MAIN_INCLUSION_AUDIT.md",
    "MISSING_OR_RESTRICTED_ARTIFACTS.md", "SCIENTIFIC_CONTRADICTIONS_AND_RESOLUTION.md",
    "FINAL_SCIENTIFIC_INTEGRITY_VERDICT.md", "POSTMERGE_VERIFICATION_RESULTS.json",
    "EXPERIMENT_ANCHORS.json", "NATIVE_AUDIT_RECEIPTS.json", "ADAPTATION_CHECKPOINT_HASH_READBACK.csv",
}
SCRIPTS = {
    "verify_postmerge_forensic_audit.py", "verify_postmerge_forensic_bundle.py",
    "forensic_native_readback.py", "forensic_release_fixture.py",
}
FORBIDDEN = re.compile(rb"(?i)(/home/[a-z0-9_.@-]+/|[A-Z]:\\Users\\[a-z0-9_.@-]+|"
                       rb"-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[a-z0-9]{30,}|"
                       rb"github_pat_[a-z0-9_]{30,}|AKIA[A-Z0-9]{16})")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def csv_rows(payload):
    return list(csv.DictReader(io.StringIO(payload.decode())))


def validate(files):
    for name, raw in files.items():
        if FORBIDDEN.search(raw):
            raise ValueError(f"non-public path or credential pattern in {name}")
    report = json.loads(files["POSTMERGE_VERIFICATION_RESULTS.json"])
    ledger = csv_rows(files["MASTER_ARTIFACT_SHA256_LEDGER.csv"])
    ids = {r["artifact_id"] for r in ledger}
    if len(ids) != report["content_identities"] or len(ledger) != report["locations"]:
        raise ValueError("ledger cardinality changed")
    if any(not re.fullmatch(r"sha256:[a-f0-9]{64}", x) for x in ids):
        raise ValueError("invalid ledger digest")
    experiments = csv_rows(files["MASTER_EXPERIMENT_INVENTORY.csv"])
    eids = {r["experiment_id"] for r in experiments}
    if len(eids) != len(experiments):
        raise ValueError("duplicate experiment ID")
    if any(r["artifact_id"] and r["artifact_id"] not in ids for r in experiments):
        raise ValueError("missing experiment artifact")
    for row in csv_rows(files["METRICS_INDEPENDENT_RECALCULATION.csv"]):
        if row["experiment_id"] not in eids or not set(row["artifact_ids"].split(";")) <= ids:
            raise ValueError("unresolved metric evidence edge")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("bundle",type=Path)
    p.add_argument("--build-from",type=Path)
    a = p.parse_args()
    expected = DOCS | SCRIPTS
    if a.build_from:
        root = Path(__file__).resolve().parent
        files = {n:(a.build_from/n).read_bytes() for n in DOCS}
        files.update({n:(root/n).read_bytes() for n in SCRIPTS})
        validate(files)
        sums = "".join(f"{sha(raw)}  {name}\n" for name,raw in sorted(files.items())).encode()
        with ZipFile(a.bundle,"x") as archive:
            for name,raw in sorted({**files,"SHA256SUMS":sums}.items()):
                info = ZipInfo(name)
                info.compress_type = ZIP_DEFLATED
                archive.writestr(info,raw)
    with ZipFile(a.bundle) as archive:
        if len(archive.namelist()) != len(expected)+1 or set(archive.namelist()) != expected | {"SHA256SUMS"}:
            raise ValueError("unexpected bundle content")
        files = {n:archive.read(n) for n in expected}
        checks = "".join(f"{sha(raw)}  {name}\n" for name,raw in sorted(files.items())).encode()
        if checks != archive.read("SHA256SUMS"):
            raise ValueError("bundle manifest mismatch")
        validate(files)
    print(json.dumps({"sha256":sha(a.bundle.read_bytes()),"members":len(expected)+1,"public_only":True}))


if __name__ == "__main__":
    main()
