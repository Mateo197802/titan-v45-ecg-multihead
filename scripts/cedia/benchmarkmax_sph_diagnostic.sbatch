#!/bin/bash
#SBATCH --job-name=titan_v46_baseline_audit
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:20:00
set -euo pipefail
umask 077
if [[ $# != 7 ]]; then
    printf 'Usage: sbatch %s METADATA LEDGER AGGREGATE RECEIPT OUTPUT_DIR SCRIPT SCRIPT_SHA256\n' "$0" >&2
    exit 2
fi
metadata=$1
ledger=$2
aggregate=$3
receipt=$4
output=$5/sph-baseline-diagnostic-$SLURM_JOB_ID.json
script=$6
script_sha=$7
[[ "$script_sha" =~ ^[0-9a-f]{64}$ ]]
test "$(sha256sum "$script" | cut -d ' ' -f 1)" = "$script_sha"
python3 "$script" --metadata "$metadata" --ledger "$ledger" --aggregate "$aggregate" \
    --scoring-receipt "$receipt" --output "$output"
sha256sum "$output"
