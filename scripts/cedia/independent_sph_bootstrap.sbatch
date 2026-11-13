#!/bin/bash
#SBATCH --job-name=titan_sph_bootstrap_check
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=02:00:00
set -euo pipefail
umask 077
if [[ $# != 10 ]]; then
    printf 'Usage: sbatch %s METADATA LEDGER INDEX AGGREGATE PROTOCOL DEPS OUTPUT_DIR SCRIPT SCRIPT_SHA AGGREGATE_SHA\n' "$0" >&2
    exit 2
fi
metadata=$1
ledger=$2
index=$3
aggregate=$4
protocol=$5
deps=$6
output=$7/independent-sph-bootstrap-$SLURM_JOB_ID.json
script=$8
script_sha=$9
aggregate_sha=${10}
[[ "$script_sha" =~ ^[0-9a-f]{64}$ ]]
[[ "$aggregate_sha" =~ ^[0-9a-f]{64}$ ]]
test "$(sha256sum "$script" | cut -d ' ' -f 1)" = "$script_sha"
test "$(sha256sum "$aggregate" | cut -d ' ' -f 1)" = "$aggregate_sha"
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-bootstrap-check-XXXXXX")
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python "$script" --metadata "$metadata" --ledger "$ledger" --duplicate-index "$index" \
    --aggregate "$aggregate" --protocol "$protocol" --output "$output"
sha256sum "$output"
