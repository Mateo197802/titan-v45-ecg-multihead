#!/bin/bash
#SBATCH --job-name=titan-code-dev
#SBATCH --partition=cpu-dev
#SBATCH --time=00:35:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
set -euo pipefail
umask 077
repo=${1:?repo}
study=${2:?study}
features=${3:?Stage A feature directory}
deps=${4:?dependency tar}
module load pytorch/2.2
scratch=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/titan-code-dev-XXXXXX")
trap 'rm -rf "$scratch"' EXIT
tar -xf "$deps" -C "$scratch"
export PYTHONPATH="$scratch${PYTHONPATH:+:$PYTHONPATH}"
export OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 OMP_NUM_THREADS=4
cd "$repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
python -B -u scripts/external_validation/audit_mimic_grammar.py "$study" "$study/mimic_grammar_audit.json"
python -B -u scripts/external_validation/fit_code_transfer.py "$features" "$study/code15_frozen_candidates"
