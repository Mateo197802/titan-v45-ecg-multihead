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
previous=${7:-}
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
scope=(--archives exams_part10.zip)
if [[ -n "$previous" ]]; then
    scope=(--reuse-partial "$previous")
fi
run_id=$SLURM_JOB_ID
if [[ ${SLURM_STEP_ID:-batch} =~ ^[0-9]+$ ]]; then
    run_id="$run_id.$SLURM_STEP_ID"
fi
python -B -u scripts/external_validation/evaluate_code15.py \
    --study "$study" --assets "$assets" --historical "$historical" \
    --publisher-test "$study/code15/code-test-3765780" \
    --candidates "$study/code15_frozen_candidates" --scratch "$scratch/work" \
    --output "$study/code15-evaluation-$run_id" "${scope[@]}"
