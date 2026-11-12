#!/bin/bash
#SBATCH --job-name=titan-code-preflight
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --time=01:30:00
set -euo pipefail
umask 077
repo=${1:?repository}
code=${2:?CODE directory}
deps=${3:?dependencies archive}
hdf5deps=${4:?HDF5 dependencies archive}
shift 4
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-code-preflight-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
mkdir "$scratch/deps" "$scratch/work"
tar -xf "$deps" -C "$scratch/deps"
tar -xf "$hdf5deps" -C "$scratch/deps"
export PYTHONPATH="$scratch/deps${PYTHONPATH:+:$PYTHONPATH}"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
cd "$repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
python -B -u scripts/external_validation/preflight_code15.py "$code" "$scratch/work" "$@"
