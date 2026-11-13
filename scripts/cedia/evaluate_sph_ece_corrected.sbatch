#!/bin/bash
#SBATCH --job-name=titan_sph_ece
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=04:00:00
set -euo pipefail
umask 077
if [[ $# != 10 ]]; then
    printf 'Usage: sbatch %s FROZEN_REPO SPH_DIR LEDGER SCORING_RECEIPT DUPLICATE_INDEX DEPS OUTPUT_DIR COMMIT WRAPPER WRAPPER_SHA256\n' "$0" >&2
    exit 2
fi
repo=$1
source=$2
ledger=$3
scoring_receipt=$4
duplicate_index=$5
deps=$6
output=$7/sph-ece-report-$SLURM_JOB_ID
commit=$8
wrapper=$9
wrapper_sha=${10}
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$wrapper_sha" =~ ^[0-9a-f]{64}$ ]]
test "$(sha256sum "$wrapper" | cut -d ' ' -f 1)" = "$wrapper_sha"
mkdir -m 700 "$output"
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-sph-ece-XXXXXX")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
cd "$repo"
test "$(git rev-parse HEAD)" = "$commit"
test -z "$(git status --porcelain)"
python -u "$wrapper" --repo "$repo" --source "$source" --ledger "$ledger" \
    --scoring-receipt "$scoring_receipt" --duplicate-index "$duplicate_index" \
    --python-deps-archive "$deps" --output "$output/aggregate.json" \
    --receipt-output "$output/aggregation-receipt.json" \
    --correction-receipt "$output/ece-correction-receipt.json" --expected-commit "$commit"
sha256sum "$output/aggregate.json" "$output/aggregation-receipt.json" \
    "$output/ece-correction-receipt.json" > "$output/SHA256SUMS"
