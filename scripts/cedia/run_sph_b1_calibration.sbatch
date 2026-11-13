#!/bin/bash
#SBATCH --job-name=titan_v46_sph_b1_cal
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
set -euo pipefail
umask 077
if [[ $# != 11 ]]; then
    printf 'Usage: sbatch %s METADATA LEDGER V45_CONFIG SCORING_RECEIPT BASELINE_AGGREGATE B1_CONFIG SCRIPT SCRIPT_SHA256 V45_REPO V46_REPO PRIVATE_OUTPUT_DIR\n' "$0" >&2
    exit 2
fi
metadata=$1
ledger=$2
v45_config=$3
receipt=$4
aggregate=$5
b1_config=$6
script=$7
script_sha=$8
v45_repo=$9
v46_repo=${10}
output_dir=${11}
[[ "$script_sha" =~ ^[0-9a-f]{64}$ ]]
test "$(sha256sum "$script" | cut -d ' ' -f 1)" = "$script_sha"
module load miniconda3/3
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate yc_env2
python --version
python -c 'import numpy, scipy; print("numpy", numpy.__version__); print("scipy", scipy.__version__)'
mkdir -p -m 700 "$output_dir"
chmod 700 "$output_dir"
output="$output_dir/sph-b1-calibration-$SLURM_JOB_ID.json"
python "$script" \
    --metadata "$metadata" \
    --ledger "$ledger" \
    --v45-config "$v45_config" \
    --scoring-receipt "$receipt" \
    --baseline-aggregate "$aggregate" \
    --b1-config "$b1_config" \
    --output "$output" \
    --forbidden-root "$v45_repo" \
    --forbidden-root "$v46_repo"
stat -c 'mode=%a size=%s path=%n' "$output"
sha256sum "$output"
