#!/bin/bash
#SBATCH --job-name=titan-ext-mimic
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G
#SBATCH --time=03:00:00
set -euo pipefail
umask 077
study=${1:?study directory required}
mode=${2:?reference or acquire required}
module load pytorch/2.2
cd "$study/repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
protocol=docs/external_validation_20261111/FROZEN_EXTERNAL_EVALUATION_PROTOCOL.json
case "$mode" in
    reference) script=audit_mimic_reference.py ;;
    acquire) script=acquire_mimic.py ;;
    *) exit 2 ;;
esac
python -B -u "scripts/external_validation/$script" "$study" "$protocol"
