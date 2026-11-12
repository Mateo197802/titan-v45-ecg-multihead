#!/bin/bash
#SBATCH --job-name=titan-code-delivery
#SBATCH --partition=cpu-dev
#SBATCH --time=00:20:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
set -euo pipefail
umask 077
repo=${1:?repository}
code=${2:?CODE directory}
first=${3:?first archive evaluation}
evaluation=${4:?full evaluation}
destination=${5:?aggregate-only destination}
deps=${6:?dependencies archive}
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-code-delivery-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2
cd "$repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
python -B -u scripts/external_validation/seal_full_code15_delivery.py "$code" "$first" "$evaluation" "$destination"
