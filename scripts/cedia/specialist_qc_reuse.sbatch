#!/bin/bash
#SBATCH --job-name=titan_spec_qc_reuse
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=04:00:00
set -euo pipefail
umask 077

if [[ $# != 5 ]]; then
    printf 'Usage: sbatch %s REPO DATA_ROOT SOURCE_PREFLIGHT_DIR OUTPUT_PREFLIGHT_DIR PYTHON_DEPS_TAR\n' "$0" >&2
    exit 2
fi

repo=$1
data_root=$2
source_preflight=$3
output_dir=$4
deps_tar=$5

module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-specialist-qc-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
tar -xf "$deps_tar" -C "$scratch"
export PYTHONPATH="$scratch${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPYCACHEPREFIX="$scratch/pycache"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4

cd "$repo"
test -z "$(git status --porcelain)"
printf 'source_commit=%s\n' "$(git rev-parse HEAD)"
python -u scripts/specialist_experiments/audit_inputs.py \
    --data-root "$data_root" --output-dir "$output_dir" \
    --reuse-qc-from "$source_preflight" --repo "$repo"
