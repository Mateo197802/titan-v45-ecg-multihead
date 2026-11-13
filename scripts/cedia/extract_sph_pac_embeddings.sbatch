#!/bin/bash
#SBATCH --job-name=titan_pac_embed
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:30:00
set -euo pipefail
umask 077
if [[ $# != 8 ]]; then
    printf 'Usage: sbatch %s REPO SOURCE RELEASE PYTHON_DEPS H5PY_DEPS PRIVATE_OUTPUT_ROOT COMMIT CONFIG_SHA256\n' "$0" >&2
    exit 2
fi
repo=$1
source=$2
release=$3
deps=$4
h5py_deps=$5
output_root=$6
commit=$7
config_sha256=$8
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$config_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$repo" == /* && "$source" == /* && "$release" == /* && "$output_root" == /* ]]
mkdir -m 700 -p "$output_root"
output="$output_root/sph-pac-embeddings-$SLURM_JOB_ID"
mkdir -m 700 "$output"
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-pac-embed-XXXXXX")
export TITAN_PYTHON_DEPS_SHA256="$(sha256sum "$deps" | awk '{print $1}')"
export TITAN_H5PY_DEPS_SHA256="$(sha256sum "$h5py_deps" | awk '{print $1}')"
[[ "$TITAN_PYTHON_DEPS_SHA256" =~ ^[0-9a-f]{64}$ ]]
[[ "$TITAN_H5PY_DEPS_SHA256" =~ ^[0-9a-f]{64}$ ]]
tar -xf "$deps" -C "$scratch"
tar -xf "$h5py_deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
cd "$repo"
test "$(git rev-parse HEAD)" = "$commit"
test -z "$(git status --porcelain)"
python -u scripts/external_validation/extract_sph_v3f_embeddings.py \
    --repo "$repo" --source "$source" --release-root "$release" \
    --output "$output/embeddings-private.npz" --receipt "$output/receipt-public-safe.json" \
    --expected-commit "$commit" --expected-config-sha256 "$config_sha256"
sha256sum "$output/embeddings-private.npz" "$output/receipt-public-safe.json" \
    > "$output/SHA256SUMS"
