#!/usr/bin/env bash
#SBATCH --job-name=titan-review-replay-contrast
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=3G
#SBATCH --time=00:10:00
set -euo pipefail
umask 077
if [[ $# != 7 ]]; then
    echo "Usage: $0 CODE REFERENCE_TREE OLD_P4 OLD_RHYTHM CURRENT_P4 CURRENT_RHYTHM OUTPUT_ROOT" >&2
    exit 2
fi
code=$1 repo=$2
(cd "$code" && sha256sum -c CODE_SHA256SUMS)
[[ $(cd "$repo" && git rev-parse HEAD) == a10f1b1eab62de241c8913a7b9f3c559e37d9b7e ]]
[[ -z $(cd "$repo" && git status --porcelain) ]]
output=$7/replay-contrast-$SLURM_JOB_ID
mkdir -m 700 -- "$output"
module load pytorch/2.2
export PYTHONPATH="$repo/src" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python -u "$code/reviewer_replay_contrast.py" --repo "$repo" --previous-p4 "$3" --previous-rhythm "$4" \
    --current-p4 "$5" --current-rhythm "$6" --output "$output/aggregate.json"
(cd "$output" && sha256sum aggregate.json > SHA256SUMS)
