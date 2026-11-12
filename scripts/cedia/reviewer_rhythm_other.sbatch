#!/usr/bin/env bash
#SBATCH --job-name=titan-review-rhythm-other
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=10G
#SBATCH --time=00:45:00
set -euo pipefail
umask 077
if [[ $# != 8 ]]; then
    echo "Usage: $0 CODE TREE METRICS_TREE SOURCE DEPS DUPLICATES SCORE OUTPUT_ROOT" >&2
    exit 2
fi
code=$1 tree=$2 metrics=$3 source=$4 deps=$5 duplicates=$6 score=$7 root=$8
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ $(cd "$tree" && git rev-parse HEAD) == eb1c67b9229af875a9f868797b0c2f5c546e3dac ]]
[[ $(cd "$metrics" && git rev-parse HEAD) == f4d6be30b0befea739cf2e35df1033230a1f5d10 ]]
[[ -z $(cd "$tree" && git status --porcelain) && -z $(cd "$metrics" && git status --porcelain) ]]
output=$root/rhythm-other-$SLURM_JOB_ID
mkdir -m 700 -- "$output"
module load pytorch/2.2
scratch=$(mktemp -d)
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$tree/src:$metrics/src/titan_v45/evaluation:$scratch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
rhythm_other() {
    python -u "$code/reviewer_rhythm_other.py" "$@" --phase "$code/phase1.json" --protocol "$code/protocol.json" \
        --source "$source" --duplicate-index "$duplicates" --ledger "$score/private-predictions.jsonl" \
        --receipt "$score/scoring-receipt.json" --model "$output/private-models.json"
}
rhythm_other fit --output "$output/fit-receipt.json"
(cd "$output" && sha256sum private-models.json fit-receipt.json > FIT_SHA256SUMS)
model_sha=$(sha256sum "$output/private-models.json" | cut -d' ' -f1)
rhythm_other evaluate --expected-model-sha256 "$model_sha" --output "$output/aggregate.json"
(cd "$output" && sha256sum aggregate.json fit-receipt.json > SHA256SUMS)
