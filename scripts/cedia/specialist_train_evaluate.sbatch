#!/bin/bash
#SBATCH --job-name=titan_spec_stage_a
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=24:00:00
set -euo pipefail
umask 077

if [[ $# != 4 ]]; then
    printf 'Usage: sbatch %s REPO FEATURE_DIR PRIVATE_OUTPUT_DIR PYTHON_DEPS_TAR\n' "$0" >&2
    exit 2
fi

repo=$1
feature_dir=$2
output_dir=$3
deps_tar=$4
mkdir -p "$(dirname "$output_dir")"
chmod 700 "$(dirname "$output_dir")"

module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-specialist-train-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
tar -xf "$deps_tar" -C "$scratch"
export PYTHONPATH="$scratch${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPYCACHEPREFIX="$scratch/pycache"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
export CUBLAS_WORKSPACE_CONFIG=:4096:8

cd "$repo"
test -z "$(git status --porcelain)"
python -u scripts/specialist_experiments/train_evaluate.py \
    --feature-dir "$feature_dir" --output-dir "$output_dir" --device cuda
