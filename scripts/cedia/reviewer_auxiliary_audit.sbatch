#!/usr/bin/env bash
#SBATCH --job-name=titan-review-auxiliary
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --time=00:15:00
set -euo pipefail
umask 077
if [[ $# != 6 ]]; then
    echo "Usage: $0 CODE_DIR FROZEN_TREE SPH_SOURCE DEPS SCORE_DIR OUTPUT_ROOT" >&2
    exit 2
fi
code=$1 tree=$2 source=$3 deps=$4 score=$5 root=$6
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ $(cd "$tree" && git rev-parse HEAD) == eb1c67b9229af875a9f868797b0c2f5c546e3dac ]]
[[ -z $(cd "$tree" && git status --porcelain) ]]
output=$root/auxiliary-$SLURM_JOB_ID
mkdir -m 700 -- "$output"
module load pytorch/2.2
scratch=$(mktemp -d)
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$tree/src:$scratch"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python -u "$code/audit_reviewer_auxiliary_support.py" --phase "$code/phase1.json" \
    --ontology "$code/auxiliary.json" --source "$source" --ledger "$score/private-predictions.jsonl" \
    --receipt "$score/scoring-receipt.json" --output "$output/aggregate.json"
(cd "$output" && sha256sum aggregate.json > SHA256SUMS)
