#!/bin/bash
#SBATCH --job-name=titan_sph_dup_audit
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --time=00:20:00
set -euo pipefail
umask 077
if [[ $# != 4 ]]; then
    printf 'Usage: sbatch %s SOURCE_TREE SPH_DIRECTORY PYTHON_DEPS PRIVATE_OUTPUT_DIR\n' "$0" >&2
    exit 2
fi
repo=$1
source=$2
deps=$3
output=$4/sph-duplicate-audit-$SLURM_JOB_ID
mkdir -m 700 "$output"
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-sph-audit-XXXXXX")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1
cd "$repo"
git rev-parse HEAD > "$output/commit.txt"
python -u scripts/external_validation/audit_sph_duplicates.py \
    --source "$source" --output "$output/aggregate.json" \
    --private-index "$output/private-duplicate-index.jsonl"
sha256sum "$output/aggregate.json" "$output/private-duplicate-index.jsonl" \
    > "$output/SHA256SUMS"
