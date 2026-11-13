#!/usr/bin/env bash
#SBATCH --job-name=titan-review-morph-retrained
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=05:00:00
set -euo pipefail
umask 077
if [[ $# != 7 ]]; then
    echo "Usage: $0 CODE_DIR UPSTREAM DATA_ROOT PREFLIGHT ASSETS DEPS OUTPUT_ROOT" >&2
    exit 2
fi
code=$1 upstream=$2 data=$3 preflight=$4 assets=$5 deps=$6 root=$7
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ $(cd "$upstream" && git rev-parse HEAD) == f4d6be30b0befea739cf2e35df1033230a1f5d10 ]]
[[ -z $(cd "$upstream" && git status --porcelain) ]]
out=$root/retrained-$SLURM_JOB_ID
mkdir -m 700 -- "$out"
module load pytorch/2.2
scratch=$(mktemp -d)
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$upstream/src:$scratch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
proto=$code/protocol.json
python -u "$code/extract_reviewer_morphology_arms.py" --protocol "$proto" --upstream "$upstream" \
    --data-root "$data" --preflight "$preflight" --assets "$assets" --output "$out/features"
retrained() {
    python -u "$code/reviewer_morphology_retrained.py" "$@" \
        --protocol "$proto" --features "$out/features" --inventory "$preflight/private_inventory.json" \
        --model "$out/private-models.json"
}
retrained fit --output "$out/fit-receipt.json"
(cd "$out" && sha256sum private-models.json fit-receipt.json > FIT_SHA256SUMS)
model_sha=$(sha256sum "$out/private-models.json" | cut -d' ' -f1)
retrained evaluate --output "$out/aggregate.json" --expected-model-sha256 "$model_sha"
(cd "$out" && sha256sum aggregate.json fit-receipt.json features/extraction-receipt.json > SHA256SUMS)
