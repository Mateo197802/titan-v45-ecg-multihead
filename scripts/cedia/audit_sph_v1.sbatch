#!/bin/bash
#SBATCH --job-name=titan_sph_inventory
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
set -euo pipefail
umask 077
if [[ $# != 3 || ! "$3" =~ ^[0-9]+$ ]]; then
    printf 'Usage: sbatch %s SOURCE_TREE PRIVATE_SPH_DIRECTORY ACQUISITION_JOB_ID\n' "$0" >&2
    exit 2
fi
repo=$1
source=$2
cd "$source"
test "$(stat -c '%u' .)" = "$(id -u)"
test "$(stat -c '%a' .)" = 700
sha256sum -c "sha256-$3.txt"
module load pytorch/2.2
work="$source/inventory-$SLURM_JOB_ID"
mkdir "$work"
python -m pip install --disable-pip-version-check --no-deps --only-binary=:all: \
    --timeout 15 --retries 2 --target "$work/deps" 'h5py==3.13.0'
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
export PYTHONPATH="$work/deps${PYTHONPATH:+:$PYTHONPATH}" PYTHONDONTWRITEBYTECODE=1
python -c 'import h5py, numpy, sys; print(sys.version); print(h5py.__version__, numpy.__version__)'
python -u "$repo/scripts/external_validation/audit_sph_dataset.py" \
    --source "$source" --output "$work/inventory.json"
sha256sum "$work/inventory.json"
