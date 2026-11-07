#!/bin/bash
#SBATCH --job-name=titan_p4_cascade
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:05:00
set -euo pipefail
umask 077
if [[ $# != 4 && $# != 5 ]]; then
    printf 'Usage: sbatch %s REPO RELEASE_ROOT PYTHON_DEPS_TAR PRIVATE_OUTPUT_ROOT [rhythm|pathology_primary4]\n' "$0" >&2
    exit 2
fi
repo=$1
release=$2
deps=$3
profile=${5:-pathology_primary4}
case "$profile" in
    pathology_primary4) name=p4 ;;
    rhythm) name=rhythm ;;
    *) printf 'Unknown waveform profile\n' >&2; exit 2 ;;
esac
output=$4/$name-cascade-$SLURM_JOB_ID
mkdir "$output"
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-p4-XXXXXX")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$scratch${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPYCACHEPREFIX="$scratch/pycache"
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
cd "$repo"
git rev-parse HEAD > "$output/commit.txt"
python -u scripts/evaluation/evaluate_cascade.py --profile "$profile" \
    --release-root "$release" --scratch "$scratch" --device cuda \
    --output "$output/aggregate.json" --private-ledger "$output/ledger.jsonl"
