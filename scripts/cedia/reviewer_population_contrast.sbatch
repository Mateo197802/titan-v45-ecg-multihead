#!/usr/bin/env bash
#SBATCH --job-name=titan-review-population
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
set -euo pipefail
umask 077
if [[ $# != 6 ]]; then
    echo "Usage: $0 CODE FROZEN_TREE SPH_SOURCE DUPLICATES SCORE OUTPUT_ROOT" >&2
    exit 2
fi
code=$1 tree=$2 source=$3 duplicates=$4 score=$5 root=$6
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ $(cd "$tree" && git rev-parse HEAD) == eb1c67b9229af875a9f868797b0c2f5c546e3dac ]]
[[ -z $(cd "$tree" && git status --porcelain) ]]
output=$root/population-contrast-$SLURM_JOB_ID
mkdir -m 700 -- "$output"
module load pytorch/2.2
export PYTHONPATH="$tree/src"
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1
python -u "$code/reviewer_population_contrast.py" --phase "$code/phase1.json" --protocol "$code/protocol.json" \
    --frozen "$tree/configs/external_validation/sph_frozen.json" --source "$source" \
    --duplicate-index "$duplicates" --ledger "$score/private-predictions.jsonl" \
    --receipt "$score/scoring-receipt.json" --output "$output/aggregate.json"
(cd "$output" && sha256sum aggregate.json > SHA256SUMS)
