#!/bin/bash
#SBATCH --job-name=titan-da-reduce
#SBATCH --partition=cpu-dev
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
set -euo pipefail
umask 077
repo=${1:?repository}
scores=${2:?sealed private scores}
out=${3:?aggregate output}
deps=${4:?dependencies archive}
hdf5deps=${5:?HDF5 dependencies archive}
module load pytorch/2.2
source "$repo/scripts/cedia/code15_scratch.sh"
scratch=$(code15_scratch "$(dirname -- "$out")" reduction 1048576)
trap 'rm -rf -- "$scratch"' EXIT
tar -xf "$deps" -C "$scratch"
tar -xf "$hdf5deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export TMPDIR="$scratch" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
cd "$repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
python -B -u scripts/domain_adaptation/evaluate_new_holdout.py reduce "$scores" "$out"
