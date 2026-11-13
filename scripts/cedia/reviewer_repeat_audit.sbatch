#!/usr/bin/env bash
#SBATCH --job-name=titan-review-repeat-audit
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:10:00
set -euo pipefail
umask 077
if [[ $# != 5 ]]; then
    echo "Usage: $0 SCRIPT PHASE_PROTOCOL ORIGINAL_SCORE_DIR NEW_SCORE_DIR RUN_ROOT" >&2
    exit 2
fi
module load pytorch/2.2
out=$5/repeat-audit-$SLURM_JOB_ID
mkdir -m 700 -- "$out"
python -u "$1" --protocol "$2" \
    --original-ledger "$3/private-predictions.jsonl" --original-receipt "$3/scoring-receipt.json" \
    --new-ledger "$4/private-predictions.jsonl" --new-receipt "$4/scoring-receipt.json" \
    --output "$out/aggregate.json"
sha256sum "$1" "$2" "$out/aggregate.json" > "$out/SHA256SUMS"
