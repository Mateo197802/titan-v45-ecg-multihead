#!/bin/bash
#SBATCH --job-name=titan-ext-qc
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
set -euo pipefail
umask 077
repo=${1:?repository required}
study=${2:?study directory required}
history=${3:?Stage A inventory required}
deps=${4:?dependency tar required}
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-external-qc-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$scratch${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPYCACHEPREFIX="$scratch/pycache"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
cd "$repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
python -u scripts/external_validation/audit_mimic_signals.py "$study" "$history"
