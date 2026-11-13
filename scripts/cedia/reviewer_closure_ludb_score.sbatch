#!/usr/bin/env bash
#SBATCH --job-name=titan-closure-ludb-score
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
set -euo pipefail
umask 077
if [[ $# != 6 ]]; then
    echo "Usage: $0 CODE NATIVE_REPO ASSETS DEPS POLICY OUT_ROOT" >&2
    exit 2
fi
code=$1 repo=$2 assets=$3 deps=$4 policy=$5 root=$6
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ $(cd "$repo" && git rev-parse HEAD) == f4d6be30b0befea739cf2e35df1033230a1f5d10 ]]
[[ -z $(cd "$repo" && git status --porcelain) ]]
module load pytorch/2.2
source "$code/scripts/cedia/reviewer_private_scratch.sh"
scratch=$(reviewer_private_scratch "$root")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
out=$root/ludb-score-$SLURM_JOB_ID
python -u "$code/scripts/evaluation/score_reviewer_closure_ludb.py" \
    --archive "$root/ludb-1.0.1.zip" --output "$out" --repo "$repo" --assets "$assets" \
    --protocol "$code/configs/reviewer_experiments/scientific_closure_v1.json" --policy "$policy"
(cd "$out" && sha256sum private-scored-and-routed.jsonl scoring-receipt.json > SHA256SUMS)
