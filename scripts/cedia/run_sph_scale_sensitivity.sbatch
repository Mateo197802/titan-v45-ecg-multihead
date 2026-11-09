#!/bin/bash
#SBATCH --job-name=titan_v46_scale_probe
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:20:00
set -euo pipefail
umask 077
if [[ $# != 9 ]]; then
    printf 'Usage: sbatch %s V45_REPO SPH_SOURCE RELEASE_ROOT PYTHON_DEPS H5PY_DEPS LEDGER V46_REPO PRIVATE_OUTPUT_DIR SCRIPT_SHA256\n' "$0" >&2
    exit 2
fi
v45_repo=$1
source=$2
release=$3
deps=$4
h5py_deps=$5
ledger=$6
v46_repo=$7
output_root=$8
expected_script_sha=$9
script="$v46_repo/scripts/benchmarkmax/sph_scale_sensitivity.py"
[[ "$expected_script_sha" =~ ^[0-9a-f]{64}$ ]]
test "$(sha256sum "$script" | cut -d ' ' -f 1)" = "$expected_script_sha"
output_dir="$output_root/sph-scale-sensitivity-$SLURM_JOB_ID"
mkdir -m 700 -p "$output_dir"
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-v46-scale-XXXXXX")
tar -xf "$deps" -C "$scratch"
tar -xf "$h5py_deps" -C "$scratch"
export PYTHONPATH="$v45_repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPYCACHEPREFIX="$scratch/pycache"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 CUBLAS_WORKSPACE_CONFIG=:4096:8
cd "$v46_repo"
git rev-parse HEAD > "$output_dir/experiment-commit.txt"
python -u "$script" --frozen-repo "$v45_repo" --source "$source" \
    --release "$release" --ledger "$ledger" --output "$output_dir/aggregate.json"
sha256sum "$output_dir/aggregate.json" > "$output_dir/SHA256SUMS"
