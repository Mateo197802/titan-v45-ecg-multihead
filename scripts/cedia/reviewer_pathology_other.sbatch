#!/usr/bin/env bash
#SBATCH --job-name=titan-review-path-other
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:30:00
set -euo pipefail
umask 077
if [[ $# != 7 ]]; then
    echo "Usage: $0 CODE_DIR UPSTREAM PTBXL FEATURES PREFLIGHT DEPS OUTPUT_ROOT" >&2
    exit 2
fi
code=$1 upstream=$2 source=$3 features=$4 preflight=$5 deps=$6 root=$7
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ $(cd "$upstream" && git rev-parse HEAD) == f4d6be30b0befea739cf2e35df1033230a1f5d10 ]]
[[ -z $(cd "$upstream" && git status --porcelain) ]]
output=$root/pathology-other-$SLURM_JOB_ID
mkdir -m 700 -- "$output"
module load pytorch/2.2
scratch=$(mktemp -d)
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$upstream/src:$scratch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
other() {
    python -u "$code/reviewer_pathology_other.py" "$@" --protocol "$code/protocol.json" \
        --source "$source" --features "$features" --preflight "$preflight" --model "$output/private-models.json"
}
other fit --output "$output/fit-receipt.json"
(cd "$output" && sha256sum private-models.json fit-receipt.json > FIT_SHA256SUMS)
model_sha=$(sha256sum "$output/private-models.json" | cut -d' ' -f1)
other evaluate --expected-model-sha256 "$model_sha" --output "$output/aggregate.json"
(cd "$output" && sha256sum aggregate.json fit-receipt.json > SHA256SUMS)
