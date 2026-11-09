#!/bin/bash
#SBATCH --job-name=titan_pac_head
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=08:00:00
set -euo pipefail
umask 077

if [[ $# != 12 ]]; then
    printf 'Usage: sbatch --output=PRIVATE_ROOT/slurm-%%j.out %s V46_REPO SPH_SOURCE V3F_CHECKPOINT P8_SPECIALIST PYTHON_DEPS H5PY_DEPS PRIVATE_ROOT EXPECTED_COMMIT CONFIG_SHA256 V45_REPO P8_LEDGER P8_RECEIPT\n' "$0" >&2
    exit 2
fi

repo=$1
source=$2
backbone=$3
p8_specialist=$4
deps=$5
h5py_deps=$6
private_root=$7
commit=$8
config_sha256=$9
v45_repo=${10}
p8_ledger=${11}
p8_receipt=${12}
run_dir="$private_root/pac-head-$SLURM_JOB_ID"

[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$config_sha256" =~ ^[0-9a-f]{64}$ ]]
[[ -d "$repo/.git" && -d "$source" && -f "$backbone" && -f "$p8_specialist" ]]
[[ -f "$deps" && -f "$h5py_deps" && -d "$private_root" ]]
[[ -f "$p8_ledger" && -f "$p8_receipt" ]]
[[ ! -e "$run_dir" ]]
mkdir -m 700 "$run_dir"

test "$(sha256sum "$deps" | cut -d ' ' -f 1)" = \
    5ea9a481f100342a4b7c9aaf98294659340d05ba20dba645007f37a3fbb6cc45
test "$(sha256sum "$h5py_deps" | cut -d ' ' -f 1)" = \
    e2ad92e7a9258e6ca5872b87d5cdde2ab1b6fb2d80cf69f890043e58df8baf61
test "$(sha256sum "$backbone" | cut -d ' ' -f 1)" = \
    ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8
test "$(sha256sum "$p8_specialist" | cut -d ' ' -f 1)" = \
    b30cb2bbb45f1231c93ff1c196aa966b57b49831cadb296131c0283e7b0ceb02
test "$(sha256sum "$p8_ledger" | cut -d ' ' -f 1)" = \
    4a3a1e61b1784e06190d5caaa089fca04ef84792acb3a5f9fc1af3f9c1173462
test "$(sha256sum "$p8_receipt" | cut -d ' ' -f 1)" = \
    8abdc5f6561fc3fea77eeb68e8aa34bc2d02396cad9c2e9fbeea70b4188dac92

module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-pac-head-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
tar -xf "$deps" -C "$scratch"
tar -xf "$h5py_deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=197802
export CUBLAS_WORKSPACE_CONFIG=:4096:8

cd "$repo"
test "$(git rev-parse HEAD)" = "$commit"
test -z "$(git status --porcelain)"
test "$(sha256sum configs/benchmarkmax/sph_pac_head_comparison.json | cut -d ' ' -f 1)" = "$config_sha256"

python - <<'PY'
import h5py
import numpy
import scipy
import torch

expected = {
    "numpy": "2.2.6",
    "scipy": "1.15.3",
    "torch": "2.10.0+cu128",
    "h5py": "3.13.0",
}
actual = {
    "numpy": numpy.__version__,
    "scipy": scipy.__version__,
    "torch": torch.__version__,
    "h5py": h5py.__version__,
}
if actual != expected:
    raise SystemExit(f"runtime version mismatch: {actual} != {expected}")
if not torch.cuda.is_available() or torch.cuda.get_device_name(0) != "NVIDIA A100-SXM4-40GB":
    raise SystemExit("required NVIDIA A100 runtime is unavailable")
assert torch.from_numpy(numpy.zeros(1, dtype=numpy.float32)).numpy().shape == (1,)
print("runtime_verified", actual, torch.version.cuda, torch.cuda.get_device_name(0))
PY

python -u scripts/benchmarkmax/run_sph_pac_head_comparison.py \
    --source "$source" \
    --backbone "$backbone" \
    --p8-specialist "$p8_specialist" \
    --p8-ledger "$p8_ledger" \
    --p8-receipt "$p8_receipt" \
    --output "$run_dir/aggregate.json" \
    --expected-config-sha256 "$config_sha256" \
    --expected-commit "$commit" \
    --forbidden-root "$repo" \
    --forbidden-root "$v45_repo"

python -u scripts/benchmarkmax/verify_sph_pac_head_aggregate.py \
    --report "$run_dir/aggregate.json" \
    --model-artifact "$run_dir/pac_heads_private.pt" \
    > "$run_dir/verification.json"

chmod 600 "$run_dir/aggregate.json" "$run_dir/pac_heads_private.pt" "$run_dir/verification.json"
sha256sum "$run_dir/aggregate.json" "$run_dir/pac_heads_private.pt" "$run_dir/verification.json" \
    > "$run_dir/SHA256SUMS"
chmod 600 "$run_dir/SHA256SUMS"
printf 'PRIVATE_RESULT_DIR=%s\n' "$run_dir"
