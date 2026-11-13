#!/bin/bash
#SBATCH --job-name=titan-da-sources
#SBATCH --partition=cpu-dev
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=10G
set -euo pipefail
umask 077
repo=${1:?repository}
raw=${2:?authorized raw root}
preflight=${3:?verified inventory root}
code=${4:?sealed CODE bank}
output=${5:?output directory}
deps=${6:?dependencies archive}
hdf5deps=${7:?HDF5 dependencies archive}
module load pytorch/2.2
source "$repo/scripts/cedia/code15_scratch.sh"
scratch=$(code15_scratch "$(dirname -- "$output")" multisource)
trap 'rm -rf -- "$scratch"' EXIT
tar -xf "$deps" -C "$scratch"
tar -xf "$hdf5deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export TMPDIR="$scratch" OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4
cd "$repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
sha256sum docs/domain_adaptation/CROSS_SOURCE_PROTOCOL.json
python -B -u scripts/domain_adaptation/build_additional_sources.py "$raw" "$preflight" "$code" "$output"
