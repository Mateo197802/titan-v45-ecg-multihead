#!/bin/bash
#SBATCH --job-name=titan-code-fetch
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=2
#SBATCH --time=04:55:00
#SBATCH --mem=2G
set -euo pipefail
umask 077
cd "${1:?study directory}/code15"
module load pytorch/2.2
index=$(mktemp)
trap 'rm -f "$index"' EXIT
python - > "$index" <<'PY'
import hashlib
import json
import re
from pathlib import Path

data = Path("record.json").read_bytes()
if hashlib.sha256(data).hexdigest() != "b20c4991cdee599f98e7ecac4ded8be4d2856d203a51985e5ea4462108df9496":
    raise ValueError("publisher catalog mismatch")
parts = {row["key"]: row for row in json.loads(data)["files"] if row["key"].endswith(".zip")}
assert set(parts) == {f"exams_part{i}.zip" for i in range(18)}
for name in sorted(parts, key=lambda key: hashlib.sha256(("20261111|code15-transport|" + key).encode()).digest()):
    row = parts[name]
    digest = row["checksum"].removeprefix("md5:")
    assert re.fullmatch("[0-9a-f]{32}", digest) and 0 < row["size"] <= 3 * 1024**3
    print(name, digest, row["size"])
PY
while read -r filename checksum size; do
    if [[ ! -f "$filename" ]]; then
        available=$(df -PB1 . | awk 'NR==2 {print $4}')
        (( available > size + 10737418240 ))
        curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
            --retry 2 --connect-timeout 20 --max-time 12000 --max-filesize "$size" \
            --continue-at - --output "$filename.part" \
            "https://zenodo.org/records/4916206/files/$filename?download=1"
        [[ $(stat -c %s "$filename.part") == "$size" ]]
        printf '%s  %s\n' "$checksum" "$filename.part" | md5sum --check --status
        mv "$filename.part" "$filename"
    fi
    [[ $(stat -c %s "$filename") == "$size" ]]
    printf '%s  %s\n' "$checksum" "$filename" | md5sum --check --status
    sha256sum "$filename"
done < "$index"
