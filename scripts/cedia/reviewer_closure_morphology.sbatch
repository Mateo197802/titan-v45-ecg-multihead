#!/usr/bin/env bash
#SBATCH --job-name=titan-closure-morph-audit
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:45:00
set -euo pipefail
umask 077
if [[ $# != 6 ]]; then
    echo "Usage: $0 CODE NATIVE_REPO DEPS HISTORY STAGE_A_INVENTORY OUT_ROOT" >&2
    exit 2
fi
code=$1 repo=$2 deps=$3 history=$4 inventory=$5 root=$6
fit="$history/retrained-33474"
eval_dir="$history/retrained-eval-33596"
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
(cd "$fit" && sha256sum -c FIT_SHA256SUMS)
(cd "$eval_dir" && sha256sum -c SHA256SUMS)
[[ $(cd "$repo" && git rev-parse HEAD) == f4d6be30b0befea739cf2e35df1033230a1f5d10 ]]
[[ -z $(cd "$repo" && git status --porcelain) ]]
module load pytorch/2.2
source "$code/scripts/cedia/reviewer_private_scratch.sh"
scratch=$(reviewer_private_scratch "$root")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
out="$root/morphology-audit-$SLURM_JOB_ID"
mkdir -m 700 -- "$out"
python -u "$code/scripts/evaluation/audit_reviewer_closure_morphology.py" \
  --robustness "$code/configs/reviewer_experiments/morphology_posthoc_robustness_v1.json" \
  --original-protocol "$code/configs/reviewer_experiments/november_morphology_retrained.json" \
  --prior-aggregate "$eval_dir/aggregate.json" --model "$fit/private-models.json" \
  --features "$fit/features" --inventory "$inventory" --output "$out/aggregate.json"
(cd "$out" && sha256sum aggregate.json > SHA256SUMS)
