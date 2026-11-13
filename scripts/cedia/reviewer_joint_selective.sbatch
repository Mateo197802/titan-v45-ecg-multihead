#!/usr/bin/env bash
#SBATCH --job-name=titan-review-joint-selective
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
set -euo pipefail
umask 077
if [[ $# != 7 ]]; then
    echo "Usage: $0 CODE FROZEN_TREE SOURCE DUPLICATES SCORE_DIR SELECTIVE_DIR OUTPUT_ROOT" >&2
    exit 2
fi
code=$1 tree=$2 source=$3 duplicates=$4 score=$5 selective=$6 root=$7
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
(cd "$selective" && sha256sum -c SHA256SUMS)
[[ $(cd "$tree" && git rev-parse HEAD) == eb1c67b9229af875a9f868797b0c2f5c546e3dac ]]
[[ -z $(cd "$tree" && git status --porcelain) ]]
out=$root/joint-selective-$SLURM_JOB_ID
mkdir -m 700 -- "$out"
module load pytorch/2.2
export PYTHONPATH="$tree/src" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python -u "$code/reviewer_joint_selective.py" --phase "$code/phase1.json" --protocol "$code/protocol.json" \
    --frozen "$tree/configs/external_validation/sph_frozen.json" --source "$source" --duplicate-index "$duplicates" \
    --ledger "$score/private-predictions.jsonl" --receipt "$score/scoring-receipt.json" \
    --selective-dir "$selective" --output-dir "$out"
(cd "$out" && sha256sum aggregate.json joint-policy.json private-joint-routes.jsonl > SHA256SUMS)
