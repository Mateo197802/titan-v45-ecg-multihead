#!/bin/bash
#SBATCH --job-name=titan_sph_xsrc_audit
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=01:00:00
set -euo pipefail
umask 077
if [[ $# != 6 ]]; then
    printf 'Usage: sbatch %s SOURCE_TREE SPH_DIRECTORY RELEASE_ROOT PYTHON_DEPS_TAR H5PY_DEPS_TAR PRIVATE_OUTPUT_DIR\n' "$0" >&2
    exit 2
fi
repo=$1
source=$2
release=$3
deps=$4
h5py_deps=$5
output=$6/sph-cross-source-audit-$SLURM_JOB_ID
mkdir -m 700 "$output"
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-sph-xsrc-XXXXXX")
tar -xf "$deps" -C "$scratch"
tar -xf "$h5py_deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
release_scratch="$scratch/release-root"
mkdir -p "$release_scratch"
python - "$release" "$release_scratch" <<'PY'
import sys
from pathlib import Path
from titan_v45.cascade.run_pathology import _extract_records

source, target = map(Path, sys.argv[1:])
_extract_records(
    source / "data/external_dev/rhythm/external-dev-rhythm-chapman-shaoxing.tar.zst",
    target / "data/external_dev/extracted/rhythm",
    package="external-dev-rhythm-chapman-shaoxing",
)
_extract_records(
    source / "data/external_dev/pathology/external-dev-pathology-ptbxl-fold10.tar.zst",
    target / "data/external_dev/extracted/pathology",
    package="external-dev-pathology-ptbxl-fold10",
)
PY
printf 'Waveform packages staged on node-local scratch.\n'
cd "$repo"
git rev-parse HEAD > "$output/commit.txt"
python -u scripts/external_validation/audit_sph_cross_source.py \
    --source "$source" --release-root "$release_scratch" \
    --output "$output/aggregate.json" \
    --private-candidates "$output/private-signature-candidates.jsonl"
sha256sum "$output/aggregate.json" "$output/private-signature-candidates.jsonl" \
    > "$output/SHA256SUMS"
