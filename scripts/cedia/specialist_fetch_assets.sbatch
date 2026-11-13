#!/bin/bash
#SBATCH --job-name=titan_spec_assets
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=02:00:00
set -euo pipefail
umask 077

if [[ $# != 2 ]]; then
    printf 'Usage: sbatch %s REPO ASSET_ROOT\n' "$0" >&2
    exit 2
fi

repo=$1
asset_root=$2
mkdir -p "$asset_root"
chmod 700 "$asset_root"
module load pytorch/2.2
cd "$repo"
test -z "$(git status --porcelain)"
printf 'source_commit=%s\n' "$(git rev-parse HEAD)"
python -u scripts/artifacts/fetch_release_assets.py \
    --manifest "$repo/release-manifest.json" --root "$asset_root" \
    --asset-name backbone-v3f-original.pt \
    --asset-name specialists-v3p-e008-primary6-diagnostic.pt \
    --asset-name specialists-v3q-primary8-best-candidate.pt \
    --asset-name backbone-v3ag-pathology.pt \
    --asset-name specialists-v3ag-primary4-calibrated.pt
