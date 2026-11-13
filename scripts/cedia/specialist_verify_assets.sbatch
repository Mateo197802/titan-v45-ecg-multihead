#!/bin/bash
#SBATCH --job-name=titan_spec_asset_smoke
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=01:00:00
set -euo pipefail
umask 077

if [[ $# != 3 ]]; then
    printf 'Usage: sbatch %s REPO ASSET_ROOT PRIVATE_RECEIPT\n' "$0" >&2
    exit 2
fi

repo=$1
asset_root=$2
receipt=$3
module load pytorch/2.2
cd "$repo"
test -z "$(git status --porcelain)"
printf 'source_commit=%s\n' "$(git rev-parse HEAD)"
python -u scripts/specialist_experiments/verify_release_weights.py \
    --repo "$repo" --asset-root "$asset_root" --output "$receipt"
