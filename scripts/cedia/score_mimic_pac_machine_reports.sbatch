#!/bin/bash
#SBATCH --job-name=titan_mimic_pac
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=2-00:00:00
set -euo pipefail
umask 077
if [[ $# != 9 ]]; then
    printf 'Usage: sbatch %s REPO SOURCE RELEASE PYTHON_DEPS PRIVATE_MODEL OUTPUT_DIR COMMIT CONFIG_SHA256 MODEL_SHA256\n' "$0" >&2
    exit 2
fi
repo=$1
source=$2
release=$3
deps=$4
private_model=$5
output_dir=$6
commit=$7
config_sha256=$8
model_sha256=$9
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$config_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$model_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$repo" == /* && "$source" == /* && "$release" == /* && "$private_model" == /* && "$output_dir" == /* ]]
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-mimic-pac-XXXXXX")
export TITAN_PYTHON_DEPS_SHA256="$(sha256sum "$deps" | awk '{print $1}')"
[[ "$TITAN_PYTHON_DEPS_SHA256" =~ ^[0-9a-f]{64}$ ]]
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
cd "$repo"
test "$(git rev-parse HEAD)" = "$commit"
test -z "$(git status --porcelain)"
mkdir -m 700 -p "$(dirname "$private_model")"
python -u scripts/external_validation/score_mimic_pac_machine_reports.py \
    --repo "$repo" --source "$source" --release-root "$release" \
    --private-model-bundle "$private_model" \
    --expected-model-bundle-sha256 "$model_sha256" \
    --output-dir "$output_dir" --expected-commit "$commit" \
    --expected-config-sha256 "$config_sha256"
sha256sum "$output_dir/mimic_pac_machine_report_aggregate.json" \
    "$output_dir/mimic_pac_machine_report_receipt.json" \
    > "$output_dir/SHA256SUMS"
