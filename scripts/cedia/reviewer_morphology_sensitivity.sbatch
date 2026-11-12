#!/usr/bin/env bash
#SBATCH --job-name=titan-review-morph-sensitivity
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:15:00
set -euo pipefail
umask 077
if [[ $# != 6 ]]; then
    echo "Usage: $0 CODE_DIR HISTORICAL_RUN_ROOT RELEASE_ROOT DEPS P4_JOB RHYTHM_JOB" >&2
    exit 2
fi
code=$1 root=$2 release=$3 deps=$4 p4_job=$5 rhythm_job=$6
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ "$p4_job" =~ ^[0-9]+$ && "$rhythm_job" =~ ^[0-9]+$ && "$p4_job" != "$rhythm_job" ]]
output=$root/morph-sensitivity-$SLURM_JOB_ID
mkdir -m 700 -- "$output"
module load pytorch/2.2
scratch=$(mktemp -d "$output/.scratch-XXXXXX")
export TMPDIR=$scratch
tar -xf "$deps" -C "$scratch"
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1
for tag in p4 rhythm; do
    if [[ "$tag" == p4 ]]; then
        profile=pathology_primary4
        source_commit=02019b832fafecd0c263ea556c70f16fa0a50ccf
        baseline=$root/p4-cascade-$p4_job
    else
        profile=rhythm
        source_commit=cfe6d59fa5cc4be10de0d7c6803fa5208fae0072
        baseline=$root/rhythm-cascade-$rhythm_job
    fi
    test "$(cat "$baseline/commit.txt")" = "$source_commit"
    (cd "$baseline" && sha256sum -c SHA256SUMS)
    digest=$(sha256sum "$baseline/ledger.jsonl" | cut -d' ' -f1)
    PYTHONPATH="$root/$tag-source/src:$scratch" \
        python -u "$code/run_reviewer_morphology_perturbation.py" \
        --profile "$profile" --repo "$root/$tag-source" --release "$release" --scratch "$scratch" \
        --source-commit "$source_commit" --baseline-ledger "$baseline/ledger.jsonl" \
        --baseline-sha256 "$digest" --private-ledger "$output/$tag-private.jsonl" \
        --output "$output/$tag-aggregate.json"
done
(cd "$output" && sha256sum ./*.json ./*.jsonl > SHA256SUMS)
