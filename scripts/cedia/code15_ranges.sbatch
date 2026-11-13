#!/bin/bash
#SBATCH --job-name=titan-code-ranges
#SBATCH --partition=cpu-dev
#SBATCH --time=04:55:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G
set -euo pipefail
umask 077
repo=${1:?repo}
code=${2:?CODE directory}
mode=${3:?first or all}
module load pytorch/2.2
cd "$repo"
git rev-parse HEAD
python -B -u scripts/external_validation/download_code_ranges.py "$code" "$mode"
