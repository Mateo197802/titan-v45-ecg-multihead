#!/bin/bash
#SBATCH --job-name=titan-da-code-build
#SBATCH --partition=cpu-dev
#SBATCH --time=02:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=10G
set -euo pipefail
umask 077
repo=${1:?repository}
code=${2:?CODE directory}
output=${3:?waveform bank}
deps=${4:?dependencies archive}
hdf5deps=${5:?HDF5 dependencies archive}
module load pytorch/2.2
source "$repo/scripts/cedia/code15_scratch.sh"
scratch=$(code15_scratch "$(dirname -- "$output")" development)
trap 'rm -rf -- "$scratch"' EXIT
mkdir "$scratch/deps" "$scratch/work"
tar -xf "$deps" -C "$scratch/deps"
tar -xf "$hdf5deps" -C "$scratch/deps"
export PYTHONPATH="$repo/src:$scratch/deps${PYTHONPATH:+:$PYTHONPATH}"
export TMPDIR="$scratch" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
cd "$repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
sha256sum docs/domain_adaptation/MULTISOURCE_TRAINING_PROTOCOL.json
python -B -u scripts/domain_adaptation/build_code_development.py "$code" "$output" "$scratch/work"
