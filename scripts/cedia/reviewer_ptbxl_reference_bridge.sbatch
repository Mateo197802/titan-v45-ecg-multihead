#!/usr/bin/env bash
#SBATCH --job-name=titan-review-ptbxl-bridge
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=28G
#SBATCH --time=02:00:00
set -euo pipefail
umask 077
if [[ $# != 7 ]]; then
    echo "Usage: $0 CODE UPSTREAM DATA_ROOT PREFLIGHT ASSETS DEPS OUTPUT_ROOT" >&2
    exit 2
fi
code=$1 repo=$2 data=$3 preflight=$4 assets=$5 deps=$6 root=$7
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ $(cd "$repo" && git rev-parse HEAD) == f4d6be30b0befea739cf2e35df1033230a1f5d10 ]]
[[ -z $(cd "$repo" && git status --porcelain) ]]
out=$root/ptbxl-bridge-$SLURM_JOB_ID
mkdir -m 700 -- "$out"
module load pytorch/2.2
scratch=$(mktemp -d)
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
bridge() {
    python -u "$code/reviewer_ptbxl_reference_bridge.py" "$@" --repo "$repo" --data-root "$data" \
        --source "$data/00_FUENTES_FISICAS_RAW/ptb-xl" --assets "$assets" --protocol "$code/protocol.json" \
        --inventory "$preflight/private_inventory.json" --ledger "$out/private-scores.jsonl" \
        --receipt "$out/scoring-receipt.json" --output "$out/aggregate.json"
}
bridge score
receipt=$(sha256sum "$out/scoring-receipt.json" | cut -d' ' -f1)
(cd "$out" && sha256sum scoring-receipt.json private-scores.jsonl > SCORE_SHA256SUMS)
bridge evaluate --expected-receipt-sha256 "$receipt"
(cd "$out" && sha256sum aggregate.json scoring-receipt.json > SHA256SUMS)
