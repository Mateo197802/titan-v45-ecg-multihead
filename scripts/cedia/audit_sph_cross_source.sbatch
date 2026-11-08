#!/bin/bash
#SBATCH --job-name=titan_sph_xsrc_audit
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:30:00
set -euo pipefail
umask 077
if [[ $# != 5 ]]; then
    printf 'Usage: sbatch %s SOURCE_TREE SPH_DIRECTORY RELEASE_ROOT PYTHON_DEPS_TAR PRIVATE_OUTPUT_DIR\n' "$0" >&2
    exit 2
fi
repo=$1
source=$2
release=$3
deps=$4
output=$5/sph-cross-source-audit-$SLURM_JOB_ID
mkdir -m 700 "$output"
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-sph-xsrc-XXXXXX")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
cd "$repo"
git rev-parse HEAD > "$output/commit.txt"
python -u scripts/external_validation/audit_sph_cross_source.py \
    --source "$source" --release-root "$release" \
    --output "$output/aggregate.json" \
    --private-candidates "$output/private-signature-candidates.jsonl"
sha256sum "$output/aggregate.json" "$output/private-signature-candidates.jsonl" \
    > "$output/SHA256SUMS"
