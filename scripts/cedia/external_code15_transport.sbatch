#!/bin/bash
#SBATCH --job-name=titan-ext-code15
#SBATCH --partition=cpu-dev
#SBATCH --time=03:00:00
#SBATCH --mem=2G
set -euo pipefail
umask 077
cd "${1:?private study directory required}/code15"
module load pytorch/2.2

# Transport validation only. Do not open the labels or build an evaluation from one shard.
read -r filename md5 expected < <(python - <<'PY'
import hashlib
import json
import re

with open("record.json", encoding="utf-8") as handle:
    record = json.load(handle)
assert record["doi"] == "10.5281/zenodo.4916206"
assert record["metadata"]["license"]["id"] == "cc-by-4.0"
parts = {entry["key"]: entry for entry in record["files"] if entry["key"].endswith(".zip")}
assert set(parts) == {f"exams_part{i}.zip" for i in range(18)}
chosen = min(parts, key=lambda key: hashlib.sha256(("20261111|code15-transport|" + key).encode()).digest())
entry = parts[chosen]
checksum = entry["checksum"].removeprefix("md5:")
assert re.fullmatch(r"[0-9a-f]{32}", checksum)
assert 0 < entry["size"] <= 3 * 1024 ** 3
print(chosen, checksum, entry["size"])
PY
)
if [[ ! -f "$filename" ]]; then
    curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
        --retry 2 --connect-timeout 20 --max-time 9000 --max-filesize "$expected" \
        --continue-at - --output "$filename.part" \
        "https://zenodo.org/records/4916206/files/$filename?download=1"
    [[ $(stat -c %s "$filename.part") == "$expected" ]]
    printf '%s  %s\n' "$md5" "$filename.part" | md5sum --check --status
    mv "$filename.part" "$filename"
fi
[[ $(stat -c %s "$filename") == "$expected" ]]
printf '%s  %s\n' "$md5" "$filename" | md5sum --check --status
sha256sum "$filename"
python - "$filename" <<'PY'
import json
import stat
import sys
import zipfile
from pathlib import Path

file = Path(sys.argv[1])
with zipfile.ZipFile(file) as archive:
    files = archive.infolist()
    if len(files) != 1:
        raise ValueError("unexpected CODE-15% archive layout")
    member = files[0]
    if (member.filename != file.with_suffix(".hdf5").name
            or stat.S_ISLNK(member.external_attr >> 16)
            or member.file_size > 8 * 1024 ** 3):
        raise ValueError("unexpected member identity or size")
    if archive.testzip() is not None:
        raise ValueError("CODE-15% CRC failure")
    print(json.dumps({
        "scope": "TRANSPORT_ONLY", "archive_bytes": file.stat().st_size,
        "uncompressed_bytes": member.file_size, "crc_passed": True,
        "labels_read": False, "performance_computed": False,
    }))
PY
