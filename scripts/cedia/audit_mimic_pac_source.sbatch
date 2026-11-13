#!/bin/bash
#SBATCH --job-name=titan_mimic_preflight
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=2-00:00:00
set -euo pipefail
umask 077
if [[ $# != 6 ]]; then
    printf 'Usage: sbatch %s REPO SOURCE PYTHON_DEPS OUTPUT COMMIT CONFIG_SHA256\n' "$0" >&2
    exit 2
fi
repo=$1
source=$2
deps=$3
output=$4
commit=$5
config_sha256=$6
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$config_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$repo" == /* && "$source" == /* && "$output" == /* ]]
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-mimic-preflight-XXXXXX")
export TITAN_PYTHON_DEPS_SHA256="$(sha256sum "$deps" | awk '{print $1}')"
[[ "$TITAN_PYTHON_DEPS_SHA256" =~ ^[0-9a-f]{64}$ ]]
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
cd "$repo"
test "$(git rev-parse HEAD)" = "$commit"
test -z "$(git status --porcelain)"
python -u scripts/external_validation/audit_mimic_pac_source.py \
    --repo "$repo" --source "$source" --output "$output" \
    --expected-commit "$commit" --expected-config-sha256 "$config_sha256"
sha256sum "$output" > "${output}.SHA256SUMS"
