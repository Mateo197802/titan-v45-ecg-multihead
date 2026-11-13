"""Select and fetch a fixed MIMIC-IV-ECG v1.0 cohort without accessing labels."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import tempfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ORIGIN = "https://physionet.org/files/mimic-iv-ecg/1.0/"
SPLITS = ("train", "validation", "calibration", "test")


def rank(seed: str, domain: str, key: str) -> tuple[bytes, str]:
    return hashlib.sha256(f"{seed}|{domain}|{key}".encode()).digest(), key


def select(records, *, seed: str, patient_limit: int, max_records: int):
    patients = defaultdict(list)
    seen = set()
    for row in records:
        subject, study = row["subject_id"], row["study_id"]
        if not re.fullmatch(r"[0-9]{8}", subject) or not re.fullmatch(r"[0-9]{8}", study):
            raise ValueError("unexpected MIMIC identifier format")
        expected = f"files/p{subject[:4]}/p{subject}/s{study}/{study}"
        if row["path"].lstrip("/") != expected or study in seen:
            raise ValueError("unexpected MIMIC path or repeated study ID")
        seen.add(study)
        patients[subject].append((study, expected))
    selected = sorted(patients, key=lambda key: rank(seed, "patient", key))[:patient_limit]
    n = len(selected)
    boundaries = [n * pct // 100 for pct in (65, 75, 85)]
    for idx, subject in enumerate(sorted(selected, key=lambda key: rank(seed, "split", key))):
        split = SPLITS[sum(idx >= boundary for boundary in boundaries)]
        studies = sorted(patients[subject], key=lambda item: rank(seed, "record", item[0]))
        for study, path in studies[:max_records]:
            yield dict(subject_id=subject, study_id=study, path=path, split=split)


def checksum_index(path: Path, wanted: set[str]) -> dict[str, str]:
    result = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            digest, name = line.rstrip().split(maxsplit=1)
            name = name.lstrip("*").removeprefix("./")
            if name in wanted:
                if name in result or not re.fullmatch(r"[0-9a-f]{64}", digest):
                    raise ValueError("invalid or duplicated checksum")
                result[name] = digest
    if result.keys() != wanted:
        raise ValueError(f"missing {len(wanted - result.keys())} publisher checksums")
    return result


def fetch(directory: Path, path: str, digest: str, limit: int):
    destination = directory / path
    if destination.is_file() and destination.stat().st_size <= limit:
        if hashlib.sha256(destination.read_bytes()).hexdigest() == digest:
            return destination.stat().st_size
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
        temp = Path(stream.name)
    try:
        process = subprocess.run(
            ["curl", "--fail", "--silent", "--location", "--proto", "=https", "--proto-redir",
             "=https", "--retry", "2", "--connect-timeout", "15", "--max-time", "75",
             "--max-filesize", str(limit), "--output", str(temp), ORIGIN + path],
            capture_output=True, check=False,
        )
        if process.returncode:
            raise ValueError(f"curl_{process.returncode}")
        size = temp.stat().st_size
        if size > limit or hashlib.sha256(temp.read_bytes()).hexdigest() != digest:
            raise ValueError("component_size_or_sha256")
        temp.replace(destination)
        return size
    finally:
        temp.unlink(missing_ok=True)


def atomic(path: Path, data: bytes):
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_bytes(data)
    temporary.replace(path)


def run(root: Path, protocol: Path):
    config_bytes = protocol.read_bytes()
    config = json.loads(config_bytes)["mimic_acquisition"]
    mimic = root / "mimic"
    checksums = mimic / "SHA256SUMS.txt"
    index = (mimic / "record_list.csv").read_bytes()
    expected = checksum_index(checksums, {"record_list.csv"})
    if hashlib.sha256(index).hexdigest() != expected["record_list.csv"]:
        raise ValueError("record_list.csv checksum mismatch")
    selected = list(select(
        csv.DictReader(io.StringIO(index.decode("utf-8-sig"))),
        seed=config["seed"], patient_limit=config["patient_limit"],
        max_records=config["max_records_per_patient"],
    ))
    if not selected:
        raise ValueError("empty acquisition cohort")
    paths = {row["path"] + suffix for row in selected for suffix in (".hea", ".dat")}
    expected = checksum_index(checksums, paths)
    selection = b"".join(json.dumps(row, sort_keys=True).encode() + b"\n" for row in selected)
    selection_path = root / "private_mimic_selection.jsonl"
    if selection_path.exists() and selection_path.read_bytes() != selection:
        raise ValueError("attempt to change existing selection")
    atomic(selection_path, selection)

    def download(row):
        result = {**row, "status": "verified", "components": {}}
        for suffix in (".hea", ".dat"):
            name = row["path"] + suffix
            try:
                size = fetch(mimic, name, expected[name], config["bytes_max_per_component"])
                result["components"][suffix] = {"sha256": expected[name], "bytes": size}
            except (OSError, ValueError) as exc:
                result["status"] = str(exc) if isinstance(exc, ValueError) else f"io_{exc.errno}"
                break
        return result

    counts = Counter()
    with (root / "private_mimic_acquisition.jsonl.part").open("w", encoding="utf-8") as stream:
        with ThreadPoolExecutor(max_workers=config["download_workers"]) as pool:
            for n, row in enumerate(pool.map(download, selected), 1):
                counts[row["status"]] += 1
                stream.write(json.dumps(row, sort_keys=True) + "\n")
                if n % 128 == 0:
                    stream.flush()
                    print(json.dumps({"processed": n, "counts": counts}, sort_keys=True), flush=True)
    (root / "private_mimic_acquisition.jsonl.part").replace(root / "private_mimic_acquisition.jsonl")
    receipt = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "origin": ORIGIN,
        "protocol_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "selection_sha256": hashlib.sha256(selection).hexdigest(),
        "record_list_sha256": hashlib.sha256(index).hexdigest(),
        "ecg_by_split": dict(Counter(row["split"] for row in selected)),
        "patients_by_split": {s: len({r["subject_id"] for r in selected if r["split"] == s}) for s in SPLITS},
        "acquisition_counts": dict(counts),
        "performance_computed": False,
    }
    atomic(root / "mimic_acquisition_receipt.json", (json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    import os

    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("protocol", type=Path)
    args = parser.parse_args()
    run(args.root, args.protocol)
