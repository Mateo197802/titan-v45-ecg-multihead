#!/bin/bash
#SBATCH --job-name=titan_release_hashes
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
set -euo pipefail
umask 077
if [[ $# != 3 ]]; then
    printf 'Usage: sbatch %s AUDIT_REPO RELEASE_ROOT OUTPUT_DIRECTORY\n' "$0" >&2
    exit 2
fi
repo=$1
release=$2
output=$3/release-model-hashes-$SLURM_JOB_ID.json
test ! -e "$output"
module load pytorch/2.2
python "$repo/scripts/evaluation/verify_release_hashes.py" \
    --root "$release" --require-models --output "$output"
sha256sum "$output"
