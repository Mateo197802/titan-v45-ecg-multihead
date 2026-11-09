#!/bin/bash
#SBATCH --job-name=titan_sph_support
#SBATCH --partition=cpu-dev
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:45:00
set -euo pipefail
umask 077

if [[ $# != 11 ]]; then
    printf 'Usage: sbatch %s V46_REPO V45_REPO METADATA DICTIONARY WAVEFORMS SOURCE_INVENTORY PRIVATE_ROOT EXPECTED_COMMIT CONFIG_SHA256 SCRIPT_SHA256 VERIFIER_SHA256\n' "$0" >&2
    exit 2
fi

repo=$1
v45_repo=$2
metadata=$3
dictionary=$4
waveforms=$5
source_inventory=$6
private_root=$7
commit=$8
config_sha=$9
script_sha=${10}
verifier_sha=${11}
config="$repo/configs/benchmarkmax/sph_postdedup_support.json"
script="$repo/scripts/benchmarkmax/audit_sph_postdedup_feasibility.py"
verifier="$repo/scripts/benchmarkmax/verify_sph_postdedup_feasibility.py"
deps="$private_root/h5py-audit-deps.tar"
run_dir="$private_root/postdedup-support-$SLURM_JOB_ID"

[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
[[ "$config_sha" =~ ^[0-9a-f]{64}$ ]]
[[ "$script_sha" =~ ^[0-9a-f]{64}$ ]]
[[ "$verifier_sha" =~ ^[0-9a-f]{64}$ ]]
[[ -d "$repo/.git" && -d "$v45_repo/.git" && -f "$metadata" && -f "$dictionary" && -f "$waveforms" ]]
[[ -f "$source_inventory" && -f "$deps" && -d "$private_root" ]]
[[ ! -e "$run_dir" ]]
test "$(sha256sum "$config" | cut -d ' ' -f 1)" = "$config_sha"
test "$(sha256sum "$script" | cut -d ' ' -f 1)" = "$script_sha"
test "$(sha256sum "$verifier" | cut -d ' ' -f 1)" = "$verifier_sha"
test "$(sha256sum "$deps" | cut -d ' ' -f 1)" = \
    e2ad92e7a9258e6ca5872b87d5cdde2ab1b6fb2d80cf69f890043e58df8baf61
mkdir -m 700 "$run_dir"

module load python/3.11
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-sph-support-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=197802
python3 - <<'PY'
import h5py
import numpy

expected = {"numpy": "2.4.3", "h5py": "3.13.0"}
actual = {"numpy": numpy.__version__, "h5py": h5py.__version__}
if actual != expected:
    raise SystemExit(f"runtime version mismatch: {actual} != {expected}")
print("runtime_verified", actual)
PY

cd "$repo"
test "$(git rev-parse HEAD)" = "$commit"
test -z "$(git status --porcelain)"
python3 -u "$script" \
    --metadata "$metadata" \
    --dictionary "$dictionary" \
    --waveforms "$waveforms" \
    --source-inventory "$source_inventory" \
    --config "$config" \
    --expected-config-sha256 "$config_sha" \
    --expected-commit "$commit" \
    --output "$run_dir/aggregate.json" \
    --forbidden-root "$repo" \
    --forbidden-root "$v45_repo"
python3 -u "$verifier" \
    --report "$run_dir/aggregate.json" \
    --config "$config" \
    --expected-config-sha256 "$config_sha" \
    --output "$run_dir/verification.json" \
    --forbidden-root "$repo" \
    --forbidden-root "$v45_repo"
chmod 600 "$run_dir/aggregate.json"
chmod 600 "$run_dir/verification.json"
sha256sum "$run_dir/aggregate.json" "$run_dir/verification.json" > "$run_dir/SHA256SUMS"
chmod 600 "$run_dir/SHA256SUMS"
printf 'PRIVATE_RESULT_DIR=%s\n' "$run_dir"
