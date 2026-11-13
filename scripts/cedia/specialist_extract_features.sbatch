#!/bin/bash
#SBATCH --job-name=titan_spec_features
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
set -euo pipefail
umask 077

if [[ $# != 6 ]]; then
    printf 'Usage: sbatch %s REPO DATA_ROOT PREFLIGHT_DIR ASSET_ROOT FEATURE_OUTPUT_DIR PYTHON_DEPS_TAR\n' "$0" >&2
    exit 2
fi

repo=$1
data_root=$2
preflight_dir=$3
asset_root=$4
feature_output_dir=$5
deps_tar=$6
mkdir -p "$(dirname "$feature_output_dir")"
chmod 700 "$(dirname "$feature_output_dir")"

module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-specialist-features-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
tar -xf "$deps_tar" -C "$scratch"
export PYTHONPATH="$scratch${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPYCACHEPREFIX="$scratch/pycache"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
export CUBLAS_WORKSPACE_CONFIG=:4096:8

cd "$repo"
test -z "$(git status --porcelain)"
python -u scripts/specialist_experiments/extract_features.py \
    --data-root "$data_root" --preflight-dir "$preflight_dir" \
    --output-dir "$feature_output_dir" --repo "$repo" --asset-root "$asset_root" --device cuda
