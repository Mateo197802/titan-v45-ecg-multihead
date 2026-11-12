#!/bin/bash
#SBATCH --job-name=titan-ext-probe
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:25:00
set -euo pipefail
umask 077
repo=${1:?repository required}
study=${2:?study directory required}
assets=${3:?asset cache required}
deps=${4:?dependency tar required}
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-external-probe-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$scratch${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPYCACHEPREFIX="$scratch/pycache"
cd "$repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
python -u scripts/external_validation/probe_frozen.py "$study" "$assets"
