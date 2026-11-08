#!/bin/bash
#SBATCH --job-name=titan_sph_frozen
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=01:00:00
set -euo pipefail
umask 077
if [[ $# != 9 ]]; then
    printf 'Usage: sbatch %s SOURCE_TREE SPH_DIRECTORY RELEASE_ROOT PYTHON_DEPS H5PY_DEPS OUTPUT_DIR COMMIT CONFIG_SHA256 RECORDS_PER_BATCH\n' "$0" >&2
    exit 2
fi
repo=$1
source=$2
release=$3
deps=$4
h5py_deps=$5
output=$6/sph-frozen-$SLURM_JOB_ID
commit=$7
config_sha256=$8
batch=$9
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$config_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ "$batch" == 16 ]]
mkdir -m 700 "$output"
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-sph-score-XXXXXX")
tar -xf "$deps" -C "$scratch"
tar -xf "$h5py_deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
cd "$repo"
test "$(git rev-parse HEAD)" = "$commit"
test -z "$(git status --porcelain)"
python - <<'PY'
import h5py, scipy, sys, torch, wfdb, zstandard
print(sys.version)
print("torch", torch.__version__, "cuda", torch.version.cuda)
print("h5py", h5py.__version__, "scipy", scipy.__version__)
print("wfdb", wfdb.__version__, "zstandard", zstandard.__version__)
PY
python -u scripts/external_validation/score_sph_frozen.py \
    --repo "$repo" --source "$source" --release-root "$release" \
    --ledger "$output/private-predictions.jsonl" \
    --output "$output/scoring-receipt.json" \
    --expected-commit "$commit" --expected-config-sha256 "$config_sha256"
sha256sum "$output/private-predictions.jsonl" "$output/scoring-receipt.json" \
    > "$output/SHA256SUMS"
