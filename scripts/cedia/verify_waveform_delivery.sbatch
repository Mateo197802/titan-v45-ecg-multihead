#!/bin/bash
#SBATCH --job-name=titan_verify_delivery
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:05:00
set -euo pipefail
umask 077
if [[ $# != 3 ]]; then
    printf 'Usage: sbatch %s REPO RELEASE_ROOT PRIVATE_OUTPUT_ROOT\n' "$0" >&2
    exit 2
fi
output=$3/verify-waveform-delivery-$SLURM_JOB_ID
mkdir "$output"
module load pytorch/2.2
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1
cd "$1"
python scripts/evaluation/verify_waveform_delivery.py --output "$output/checkout.json"
python scripts/evaluation/verify_release_hashes.py --root "$2" --require-models \
    --output "$output/physical-assets.json"
python scripts/evaluation/verify_release_evidence.py --output "$output/canonical-evidence.json"
python scripts/evaluation/verify_membership_policy.py --output "$output/p8-membership.json"
python scripts/evaluation/audit_af_reference_contract.py --output "$output/af-reference.json"
