#!/bin/bash
#SBATCH --job-name=titan_spec_preflight
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=12:00:00
set -euo pipefail
umask 077

if [[ $# != 4 ]]; then
    printf 'Usage: sbatch %s REPO DATA_ROOT EXPERIMENT_ROOT PYTHON_DEPS_TAR\n' "$0" >&2
    exit 2
fi

repo=$1
data_root=$2
experiment_root=$3
deps_tar=$4
output_dir="$experiment_root/preflight"
mkdir -p "$output_dir"
chmod 700 "$experiment_root" "$output_dir"

module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-specialist-preflight-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
tar -xf "$deps_tar" -C "$scratch"
export PYTHONPATH="$scratch${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPYCACHEPREFIX="$scratch/pycache"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4

cd "$repo"
test -z "$(git status --porcelain)"
python - <<'PY'
import numpy as np
import torch

probe = torch.as_tensor(np.asarray([1.0, 2.0], dtype=np.float32))
if not torch.equal(probe, torch.tensor([1.0, 2.0])):
    raise RuntimeError("PyTorch and NumPy array interoperability check failed")
print({"python": __import__("platform").python_version(),
       "numpy": np.__version__, "torch": torch.__version__,
       "cuda_available": torch.cuda.is_available()})
PY
python -u scripts/specialist_experiments/audit_inputs.py \
    --data-root "$data_root" --output-dir "$output_dir" --repo "$repo"
