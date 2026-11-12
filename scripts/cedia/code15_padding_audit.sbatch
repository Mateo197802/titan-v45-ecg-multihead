#!/bin/bash
#SBATCH --job-name=titan-code-pad
#SBATCH --partition=cpu-dev
#SBATCH --time=01:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
set -euo pipefail
umask 077
repo=${1:?repository}
study=${2:?study directory}
evaluation=${3:?scored evaluation directory}
deps=${4:?dependencies archive}
hdf5deps=${5:?HDF5 dependencies archive}
audit_output=${6:-padding_audit.json}
[[ $audit_output =~ ^[a-z_]+\.json$ ]]
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-code-pad-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
mkdir "$scratch/deps"
tar -xf "$deps" -C "$scratch/deps"
tar -xf "$hdf5deps" -C "$scratch/deps"
export PYTHONPATH="$scratch/deps${PYTHONPATH:+:$PYTHONPATH}"
export TMPDIR="$scratch" OPENBLAS_NUM_THREADS=2
cd "$repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
python -B scripts/external_validation/audit_code15_padding.py "$study/code15" "$evaluation" "$evaluation/$audit_output"
sha256sum "$evaluation/$audit_output"
