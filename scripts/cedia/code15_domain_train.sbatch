#!/bin/bash
#SBATCH --job-name=titan-da-fit
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
set -euo pipefail
umask 077
repo=${1:?repository}
bank=${2:?sealed waveform bank}
assets=${3:?released assets}
out=${4:?private run directory}
deps=${5:?dependencies archive}
hdf5deps=${6:?HDF5 dependencies archive}
shift 6
module load pytorch/2.2
source "$repo/scripts/cedia/code15_scratch.sh"
scratch=$(code15_scratch "$(dirname -- "$out")" training 2097152)
trap 'rm -rf -- "$scratch"' EXIT
tar -xf "$deps" -C "$scratch"
tar -xf "$hdf5deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export TMPDIR="$scratch" OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2
cd "$repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
sha256sum docs/domain_adaptation/MULTISOURCE_TRAINING_PROTOCOL.json
case ${1:-} in
    released_baselines)
        python -B -u scripts/domain_adaptation/evaluate_released.py "$bank" "$assets" "$out" ;;
    masked_mimic_ssl)
        python -B -u scripts/domain_adaptation/train_masked_mimic.py "$bank" "$assets" "$out" ;;
    evaluate_frozen)
        shift
        python -B -u scripts/domain_adaptation/evaluate_new_holdout.py "$bank" "$assets" "$@" "$out" ;;
    score_source_transfer)
        shift
        extra=${1:?additional source bank}
        shift
        python -B -u scripts/domain_adaptation/score_source_transfer.py "$bank" "$extra" "$out" "$@" ;;
    *)
        python -B -u scripts/domain_adaptation/train_duration_aware.py "$bank" "$assets" "$out" "$@" ;;
esac
