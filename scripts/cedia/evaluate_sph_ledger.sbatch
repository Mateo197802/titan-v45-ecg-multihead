#!/bin/bash
#SBATCH --job-name=titan_sph_report
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
set -euo pipefail
umask 077
if [[ $# != 8 ]]; then
    printf 'Usage: sbatch %s SOURCE_TREE SPH_DIRECTORY PRIVATE_LEDGER SCORING_RECEIPT PRIVATE_DUPLICATE_INDEX PYTHON_DEPS_TAR PRIVATE_OUTPUT_DIR COMMIT\n' "$0" >&2
    exit 2
fi
repo=$1
source=$2
ledger=$3
scoring_receipt=$4
duplicate_index=$5
deps=$6
output=$7/sph-report-$SLURM_JOB_ID
commit=$8
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
mkdir -m 700 "$output"
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-sph-report-XXXXXX")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
cd "$repo"
test "$(git rev-parse HEAD)" = "$commit"
test -z "$(git status --porcelain)"
python -u scripts/external_validation/evaluate_sph_ledger.py \
    --repo "$repo" --source "$source" --ledger "$ledger" \
    --scoring-receipt "$scoring_receipt" --duplicate-index "$duplicate_index" \
    --python-deps-archive "$deps" \
    --output "$output/aggregate.json" \
    --receipt-output "$output/aggregation-receipt.json" \
    --expected-commit "$commit"
sha256sum "$output/aggregate.json" "$output/aggregation-receipt.json" \
    > "$output/SHA256SUMS"
