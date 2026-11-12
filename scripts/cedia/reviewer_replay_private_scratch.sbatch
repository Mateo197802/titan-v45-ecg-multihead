#!/usr/bin/env bash
#SBATCH --job-name=titan-review-historical
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:15:00
set -euo pipefail
umask 077
if [[ $# != 5 ]]; then
    echo "Usage: $0 PROFILE PINNED_TREE RELEASE_ROOT DEPS OUTPUT_ROOT" >&2
    exit 2
fi
profile=$1 tree=$2 release=$3 deps=$4 root=$5
case "$profile" in
    p4) commit=02019b832fafecd0c263ea556c70f16fa0a50ccf; extra=() ;;
    rhythm) commit=cfe6d59fa5cc4be10de0d7c6803fa5208fae0072; extra=(rhythm) ;;
    *) exit 2 ;;
esac
[[ $(cd "$tree" && git rev-parse HEAD) == "$commit" ]]
[[ -z $(cd "$tree" && git status --porcelain) ]]
test -d "$root"
SLURM_TMPDIR=$(mktemp -d "$root/.replay-scratch-$SLURM_JOB_ID-XXXXXX")
export SLURM_TMPDIR
export TMPDIR=$SLURM_TMPDIR
source "$tree/scripts/cedia/run_frozen_p4_cascade.sbatch" "$tree" "$release" "$deps" "$root" "${extra[@]}"
out=$root/$profile-cascade-$SLURM_JOB_ID
(cd "$out" && sha256sum aggregate.json ledger.jsonl commit.txt > SHA256SUMS)
