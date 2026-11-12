#!/bin/bash
#SBATCH --job-name=titan-ext-meta
#SBATCH --partition=cpu-dev
#SBATCH --time=00:45:00
#SBATCH --mem=2G
set -euo pipefail
umask 077
cd "${1:?private study directory required}"
mkdir -p mimic code15

download() {
    local url=$1 destination=$2
    if [[ ! -f "$destination" ]]; then
        curl --fail --silent --show-error --location --proto '=https' \
            --retry 3 --connect-timeout 20 --max-time 1200 --continue-at - \
            --output "$destination.part" "$url"
        mv "$destination.part" "$destination"
    fi
}

mimic=https://physionet.org/files/mimic-iv-ecg/1.0
for name in LICENSE.txt RECORDS SHA256SUMS.txt machine_measurements_data_dictionary.csv \
    record_list.csv machine_measurements.csv; do
    download "$mimic/$name" "mimic/$name"
done
download 'https://zenodo.org/records/4916206/files/exams.csv?download=1' code15/exams.csv
download https://zenodo.org/api/records/4916206 code15/record.json
printf '0107516d3f63864498fb77d15799cc95  code15/exams.csv\n' | md5sum -c
python3 - <<'PY'
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path.cwd()
expected = {}
check = {"record_list.csv", "machine_measurements.csv", "machine_measurements_data_dictionary.csv"}
with (root / "mimic/SHA256SUMS.txt").open() as stream:
    for line in stream:
        digest, name = line.rstrip().split(maxsplit=1)
        name = name.lstrip("*")
        if name.startswith("./"):
            name = name[2:]
        if name in check:
            expected[name] = digest
assert expected.keys() == check
receipt = {"verified_utc": datetime.now(timezone.utc).isoformat(), "files": {}}
for path in sorted([*root.glob("mimic/*"), *root.glob("code15/*")]):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if path.parent.name == "mimic" and path.name in check:
        assert digest.hexdigest() == expected[path.name], path.name
    receipt["files"][str(path.relative_to(root))] = {
        "bytes": path.stat().st_size, "sha256": digest.hexdigest()
    }
for name in ("mimic/record_list.csv", "mimic/machine_measurements.csv", "code15/exams.csv"):
    with (root / name).open(newline="") as stream:
        reader = csv.DictReader(stream)
        count = sum(1 for _ in reader)
        receipt["files"][name].update(rows=count, columns=reader.fieldnames)
print(json.dumps(receipt, indent=2))
(root / "metadata_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
PY
