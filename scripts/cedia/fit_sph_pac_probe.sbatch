#!/bin/bash
#SBATCH --job-name=titan_pac_fit
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
set -euo pipefail
umask 077
if [[ $# != 8 ]]; then
    printf 'Usage: sbatch %s REPO SOURCE PRIVATE_EMBEDDINGS EMBEDDING_RECEIPT PYTHON_DEPS PRIVATE_MODEL_PATH COMMIT CONFIG_SHA256\n' "$0" >&2
    exit 2
fi
repo=$1
source=$2
embeddings=$3
embedding_receipt=$4
deps=$5
private_model=$6
commit=$7
config_sha256=$8
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$config_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$repo" == /* && "$source" == /* && "$embeddings" == /* && "$embedding_receipt" == /* ]]
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-pac-fit-XXXXXX")
export TITAN_PYTHON_DEPS_SHA256="$(sha256sum "$deps" | awk '{print $1}')"
[[ "$TITAN_PYTHON_DEPS_SHA256" =~ ^[0-9a-f]{64}$ ]]
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
cd "$repo"
test "$(git rev-parse HEAD)" = "$commit"
test -z "$(git status --porcelain)"
mkdir -m 700 -p "$(dirname "$private_model")"
python -u scripts/external_validation/fit_sph_pac_probe.py \
    --repo "$repo" --source "$source" --embeddings "$embeddings" \
    --embedding-receipt "$embedding_receipt" \
    --private-model-bundle "$private_model" \
    --expected-commit "$commit" --expected-config-sha256 "$config_sha256"
sha256sum "$private_model" \
    "$repo/outputs/results/external_sph_pac/pac_probe_aggregate.json" \
    "$repo/outputs/results/external_sph_pac/pac_probe_receipt.json" \
    > "$(dirname "$private_model")/pac-probe-$SLURM_JOB_ID.SHA256SUMS"
