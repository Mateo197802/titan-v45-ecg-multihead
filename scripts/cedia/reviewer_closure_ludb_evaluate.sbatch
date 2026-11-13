#!/usr/bin/env bash
#SBATCH --job-name=titan-closure-ludb-eval
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=01:00:00
set -euo pipefail
umask 077
if [[ $# != 8 ]]; then
    echo "Usage: $0 CODE NATIVE_REPO DEPS POLICY SCORE_DIR SPH_HEAD_DIR STAGE_A_INVENTORY OUT_ROOT" >&2
    exit 2
fi
code=$1 repo=$2 deps=$3 policy=$4 score=$5 other=$6 stage_inventory=$7 root=$8
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
(cd "$score" && sha256sum -c SHA256SUMS)
(cd "$other" && sha256sum -c FIT_SHA256SUMS)
[[ $(cd "$repo" && git rev-parse HEAD) == f4d6be30b0befea739cf2e35df1033230a1f5d10 ]]
[[ -z $(cd "$repo" && git status --porcelain) ]]
module load pytorch/2.2
source "$code/scripts/cedia/reviewer_private_scratch.sh"
scratch=$(reviewer_private_scratch "$root")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
out=$root/ludb-eval-$SLURM_JOB_ID
python -u "$code/scripts/evaluation/evaluate_reviewer_closure_ludb.py" \
    --archive "$root/ludb-1.0.1.zip" --output "$out" --scored "$score" --policy "$policy" \
    --protocol "$code/configs/reviewer_experiments/scientific_closure_v1.json" \
    --other-model "$other/private-models.json" --other-fit-receipt "$other/fit-receipt.json" \
    --stage-a-inventory "$stage_inventory"
(cd "$out" && sha256sum private-reference-route-ledger.jsonl aggregate.json > SHA256SUMS)
