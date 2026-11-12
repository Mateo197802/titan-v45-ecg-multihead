#!/bin/bash
#SBATCH --job-name=titan-code-eval
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=02:00:00
set -euo pipefail
umask 077
repo=${1:?repo}
study=${2:?study}
assets=${3:?released assets}
historical=${4:?released historical rhythm archive}
deps=${5:?dependency tar}
hdf5deps=${6:?HDF5 dependency tar}
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-code-eval-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
mkdir "$scratch/deps" "$scratch/work"
tar -xf "$deps" -C "$scratch/deps"
tar -xf "$hdf5deps" -C "$scratch/deps"
export PYTHONPATH="$scratch/deps${PYTHONPATH:+:$PYTHONPATH}"
export OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 OMP_NUM_THREADS=4
cd "$repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
python -B -u scripts/external_validation/evaluate_code15.py \
    --study "$study" --assets "$assets" --historical "$historical" \
    --candidates "$study/code15_frozen_candidates" --scratch "$scratch/work" \
    --output "$study/code15-evaluation-$SLURM_JOB_ID" --archives exams_part10.zip
