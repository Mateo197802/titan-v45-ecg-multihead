#!/usr/bin/env bash
#SBATCH --job-name=titan-review-morph-evaluate
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
set -euo pipefail
umask 077
if [[ $# != 5 ]]; then
    echo "Usage: $0 CODE UPSTREAM PREFLIGHT DEPS OUTPUT_ROOT" >&2
    exit 2
fi
code=$1 upstream=$2 preflight=$3 deps=$4 root=$5
prior=$root/retrained-33474
out=$root/retrained-eval-$SLURM_JOB_ID
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ $(cd "$upstream" && git rev-parse HEAD) == f4d6be30b0befea739cf2e35df1033230a1f5d10 ]]
[[ -z $(cd "$upstream" && git status --porcelain) ]]
(cd "$prior" && sha256sum -c FIT_SHA256SUMS)
model_sha=$(sha256sum "$prior/private-models.json" | cut -d' ' -f1)
[[ $model_sha == 241f8f673121477c9d27c96239f8b423e5b036bbe33d6a33237d5920200a2337 ]]
extract_sha=$(sha256sum "$prior/features/extraction-receipt.json" | cut -d' ' -f1)
[[ $extract_sha == de65d38ef6c3c00cae2546858924ab87a7656e754fe4a52aaac7a2d7b328f3cb ]]
mkdir -m 700 -- "$out" "$out/features"
module load pytorch/2.2
source "$code/scripts/cedia/reviewer_private_scratch.sh"
scratch=$(reviewer_private_scratch "$root")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$upstream/src:$scratch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
python -u "$code/scripts/evaluation/reviewer_morphology_retrained.py" evaluate \
    --protocol "$code/configs/reviewer_experiments/november_morphology_retrained.json" \
    --features "$prior/features" --inventory "$preflight/private_inventory.json" \
    --model "$prior/private-models.json" --expected-model-sha256 "$model_sha" --output "$out/aggregate.json"
cp -- "$prior/fit-receipt.json" "$out/fit-receipt.json"
cp -- "$prior/features/extraction-receipt.json" "$out/features/extraction-receipt.json"
(cd "$out" && sha256sum aggregate.json fit-receipt.json features/extraction-receipt.json > SHA256SUMS)
