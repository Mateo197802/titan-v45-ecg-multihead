#!/bin/bash
#SBATCH --job-name=titan_sph_points
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:20:00
set -euo pipefail
umask 077
if [[ $# != 8 ]]; then
    printf 'Usage: sbatch %s METADATA LEDGER AGGREGATE PROTOCOL OUTPUT_DIR SCRIPT SCRIPT_SHA256 AGGREGATE_SHA256\n' "$0" >&2
    exit 2
fi
source=$1
ledger=$2
aggregate=$3
protocol=$4
output=$5/independent-sph-points-$SLURM_JOB_ID.json
script=$6
script_sha=$7
aggregate_sha=$8
[[ "$script_sha" =~ ^[0-9a-f]{64}$ ]]
[[ "$aggregate_sha" =~ ^[0-9a-f]{64}$ ]]
test "$(sha256sum "$script" | cut -d ' ' -f 1)" = "$script_sha"
test "$(sha256sum "$aggregate" | cut -d ' ' -f 1)" = "$aggregate_sha"
python3 "$script" --source "$source" --ledger "$ledger" --aggregate "$aggregate" \
    --protocol "$protocol" --output "$output"
sha256sum "$output"
