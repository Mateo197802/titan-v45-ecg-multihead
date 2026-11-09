#!/bin/bash
#SBATCH --job-name=titan_v46_sph_support
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
set -euo pipefail
umask 077
if [[ $# != 7 ]]; then
    printf 'Usage: sbatch %s METADATA DICTIONARY SCRIPT SCRIPT_SHA256 V45_REPO V46_REPO PRIVATE_OUTPUT_DIR\n' "$0" >&2
    exit 2
fi
metadata=$1
dictionary=$2
script=$3
script_sha=$4
v45_repo=$5
v46_repo=$6
output_dir=$7
[[ "$script_sha" =~ ^[0-9a-f]{64}$ ]]
test "$(sha256sum "$script" | cut -d ' ' -f 1)" = "$script_sha"
mkdir -p -m 700 "$output_dir"
output="$output_dir/sph-training-feasibility-$SLURM_JOB_ID.json"
python3 "$script" --metadata "$metadata" --dictionary "$dictionary" \
    --output "$output" --forbidden-root "$v45_repo" --forbidden-root "$v46_repo"
sha256sum "$output"
