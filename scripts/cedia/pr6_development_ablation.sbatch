#!/bin/bash
#SBATCH --job-name=titan-pr6-ablation
#SBATCH --partition=cpu-dev
#SBATCH --time=00:35:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=5G
set -euo pipefail
umask 077
repo=${1:?repo}
features=${2:?verified feature cache}
linear=${3:?frozen linear checkpoints}
out=${4:?new private output directory}
deps=${5:?runtime tar}
replay=${6:-}
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-pr6-ablation-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1
cd "$repo"
git rev-parse HEAD
if [[ -n "$replay" ]]; then
    python -B -u scripts/external_validation/replay_development_ablation.py "$features" "$linear" "$replay" "$out"
else
    python -B -u scripts/external_validation/run_development_ablation.py "$features" "$linear" "$out"
fi
