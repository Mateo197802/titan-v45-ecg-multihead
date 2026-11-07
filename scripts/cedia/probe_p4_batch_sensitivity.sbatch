#!/bin/bash
#SBATCH --job-name=titan_p4_batch_probe
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=12G
#SBATCH --time=00:05:00
set -euo pipefail
umask 077
if [[ $# != 5 ]]; then
    printf 'Usage: sbatch %s REPO RELEASE_ROOT DEPS_TAR SEALED_P4_LEDGER PRIVATE_OUTPUT_ROOT\n' "$0" >&2
    exit 2
fi
output=$5/p4-batch-probe-$SLURM_JOB_ID
mkdir "$output"
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-p4-probe-XXXXXX")
tar -xf "$3" -C "$scratch"
export PYTHONPATH="$scratch${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$scratch/pycache"
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
cd "$1"
git rev-parse HEAD > "$output/commit.txt"
python -u scripts/evaluation/probe_p4_batch_sensitivity.py --release-root "$2" \
    --scratch "$scratch" --sealed-pathology-ledger "$4" --output "$output/aggregate.json"
