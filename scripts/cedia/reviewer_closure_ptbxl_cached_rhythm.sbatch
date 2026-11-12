#!/usr/bin/env bash
#SBATCH --job-name=titan-closure-ptbxl-cached-rhythm
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:25:00
set -euo pipefail
umask 077
if [[ $# != 8 ]]; then
    echo "Usage: $0 CODE NATIVE_REPO RELEASE_ASSETS DEPS FEATURES METADATA SUPPORT OUT_ROOT" >&2
    exit 2
fi
code=$1 repo=$2 assets=$3 deps=$4 features=$5 metadata=$6 support=$7 root=$8
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ $(cd "$repo" && git rev-parse HEAD) == f4d6be30b0befea739cf2e35df1033230a1f5d10 ]]
[[ -z $(cd "$repo" && git status --porcelain) ]]
module load pytorch/2.2
source "$code/scripts/cedia/reviewer_private_scratch.sh"
scratch=$(reviewer_private_scratch "$root")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
out="$root/ptbxl-cached-rhythm-$SLURM_JOB_ID"
mkdir -m 700 -- "$out"
evaluate() {
    python -u "$code/scripts/evaluation/evaluate_reviewer_ptbxl_cached_rhythm.py" "$@" +      --repo "$repo" --assets "$assets" --features "$features" +      --metadata "$metadata" --support "$support" --output "$out"
}
evaluate score
(cd "$out" && sha256sum scoring-receipt.json private-readout.json > SCORE_SHA256SUMS)
evaluate evaluate --score-receipt-sha256 "$(sha256sum "$out/scoring-receipt.json" | cut -d' ' -f1)"
(cd "$out" && sha256sum aggregate.json scoring-receipt.json private-readout.json > SHA256SUMS)
