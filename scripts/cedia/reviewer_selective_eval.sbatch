#!/usr/bin/env bash
#SBATCH --job-name=titan-review-selective
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
set -euo pipefail
umask 077
if [[ $# != 7 ]]; then
    echo "Usage: $0 CODE_DIR FROZEN_TREE SPH_SOURCE DEPS PRIVATE_DUPLICATES SCORE_DIR OUTPUT_ROOT" >&2
    exit 2
fi
code=$1 tree=$2 source=$3 deps=$4 duplicates=$5 score=$6 root=$7
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ $(cd "$tree" && git rev-parse HEAD) == eb1c67b9229af875a9f868797b0c2f5c546e3dac ]]
[[ -z $(cd "$tree" && git status --porcelain) ]]
output=$root/selective-$SLURM_JOB_ID
mkdir -m 700 -- "$output"
module load pytorch/2.2
scratch=$(mktemp -d)
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$tree/src:$scratch"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
config=$tree/configs/external_validation/sph_frozen.json
policy=$output/policy.json
python -u "$code/freeze_reviewer_selective_policy.py" --phase "$code/phase1.json" \
    --frozen-config "$config" --ledger "$score/private-predictions.jsonl" \
    --receipt "$score/scoring-receipt.json" --duplicate-index "$duplicates" --output "$policy" \
    --private-split "$output/private-split.jsonl"
policy_sha=$(sha256sum "$policy" | cut -d' ' -f1)
printf '%s  policy.json\n' "$policy_sha" > "$output/POLICY_SHA256SUMS"
python -u "$code/evaluate_reviewer_selective_policy.py" --phase "$code/phase1.json" \
    --evaluation "$code/selective.json" --frozen-config "$config" --source "$source" \
    --ledger "$score/private-predictions.jsonl" --receipt "$score/scoring-receipt.json" \
    --duplicate-index "$duplicates" --policy "$policy" --expected-policy-sha256 "$policy_sha" \
    --output "$output/aggregate.json" --private-ledger "$output/private-routes.jsonl"
(cd "$output" && sha256sum policy.json aggregate.json private-split.jsonl private-routes.jsonl > SHA256SUMS)
