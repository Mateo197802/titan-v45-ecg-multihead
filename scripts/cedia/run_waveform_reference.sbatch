#!/bin/bash
#SBATCH --job-name=titan_waveform_reference
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:05:00
set -euo pipefail
umask 077
if [[ $# != 4 ]]; then
    printf 'Usage: sbatch %s REPO P4_LEDGER RHYTHM_LEDGER PRIVATE_OUTPUT_ROOT\n' "$0" >&2
    exit 2
fi
output=$4/waveform-reference-$SLURM_JOB_ID
mkdir "$output"
module load pytorch/2.2
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1
cd "$1"
git rev-parse HEAD > "$output/commit.txt"
python -u scripts/evaluation/compare_waveform_references.py \
    --pathology-ledger "$2" --rhythm-ledger "$3" --output "$output/aggregate.json"
