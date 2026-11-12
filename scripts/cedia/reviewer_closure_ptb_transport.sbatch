#!/usr/bin/env bash
#SBATCH --job-name=titan-closure-ptb-transport
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:15:00
set -euo pipefail
umask 077
if [[ $# != 7 ]]; then
    echo "Usage: $0 CODE NATIVE_REPO ASSETS DEPS AUDIT PTBXL_PATHOLOGY_HEAD_DIR OUT_ROOT" >&2
    exit 2
fi
code=$1 repo=$2 assets=$3 deps=$4 audit=$5 other=$6 root=$7
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
(cd "$audit" && sha256sum -c SHA256SUMS)
(cd "$other" && sha256sum -c FIT_SHA256SUMS)
[[ $(cd "$repo" && git rev-parse HEAD) == f4d6be30b0befea739cf2e35df1033230a1f5d10 ]]
[[ -z $(cd "$repo" && git status --porcelain) ]]
module load pytorch/2.2
source "$code/scripts/cedia/reviewer_private_scratch.sh"
scratch=$(reviewer_private_scratch "$root")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
out=$root/ptb-transport-$SLURM_JOB_ID
run() {
    python -u "$code/scripts/evaluation/reviewer_closure_ptb_diagnostic_transport.py" "$@" \
        --archive "$root/ptbdb-1.0.0.zip" --output "$out" --repo "$repo" --assets "$assets" --scratch "$scratch" \
        --config "$code/configs/reviewer_experiments/ptb_diagnostic_transport_v1.json" --audit "$audit" \
        --other-model "$other/private-models.json" --other-fit-receipt "$other/fit-receipt.json"
}
run score
(cd "$out" && sha256sum private-scores.jsonl scoring-receipt.json > SCORE_SHA256SUMS && sha256sum -c SCORE_SHA256SUMS)
receipt=$(sha256sum "$out/scoring-receipt.json" | cut -d' ' -f1)
run evaluate --score-receipt-sha256 "$receipt"
(cd "$out" && sha256sum private-scores.jsonl scoring-receipt.json aggregate.json > SHA256SUMS)
