#!/usr/bin/env bash
#SBATCH --job-name=titan-two-comment
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
set -euo pipefail
umask 077
[[ $# == 3 ]]
code=$1 base=$2 experiment=$3
root="$base/titan-v45-two-comment-rigorous"
history="$base/titan-four-reviewers-historical-replay"
stage_a="$base/specialist-heads-20261111-v2"
repo="$stage_a/repo"
deps="$base/life-4620846-revision-20261028/python_deps.tar"
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ $(git -C "$repo" rev-parse HEAD) == f4d6be30b0befea739cf2e35df1033230a1f5d10 ]]
[[ -z $(git -C "$repo" status --porcelain) ]]
module load pytorch/2.2
source "$code/scripts/cedia/reviewer_private_scratch.sh"
scratch=$(reviewer_private_scratch "$root")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
protocol="$code/configs/reviewer_experiments/two_comment_rigorous_v1.json"
if [[ "$experiment" == runtime ]]; then
    protocol="$code/configs/reviewer_experiments/two_comment_gpu_v1.json"
fi
out="$root/$experiment-$SLURM_JOB_ID"
mkdir -m 700 -- "$out"
common=(--protocol "$protocol" --output "$out/aggregate.json")
case "$experiment" in
    runtime)
        python -u "$code/scripts/evaluation/reviewer_morphology_runtime.py" "${common[@]}" +            --base "$base" --repo "$repo" --assets "$stage_a/attempt-92505-qc-corrected/release-assets-v0.1.0"
        ;;
    selective)
        python -u "$code/scripts/evaluation/reviewer_selective_utility.py" "${common[@]}" --base "$base"
        ;;
    morphology)
        python -u "$code/scripts/evaluation/reviewer_morphology_multiseed.py" "${common[@]}" +            --original "$code/configs/reviewer_experiments/november_morphology_retrained.json" +            --features "$history/retrained-33474/features" +            --inventory "$stage_a/attempt-92505-qc-corrected/preflight/private_inventory.json"
        ;;
    *) exit 2 ;;
esac
(
    cd "$out"
    shopt -s nullglob
    sha256sum ./*.json ./*.jsonl > SHA256SUMS
)
