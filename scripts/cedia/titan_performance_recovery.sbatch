#!/bin/bash
#SBATCH --job-name=titan-recovery
#SBATCH --partition=gpu-dev
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --time=00:55:00
#SBATCH --cpus-per-task=12
#SBATCH --mem=20G
set -euo pipefail
umask 077
repo=${1:?repository}
mode=${2:?phase}
out=${3:?study output}
deps=${4:?dependency archive}
hdf5deps=${5:?HDF5 dependency archive}
shift 5
module load pytorch/2.2
source "$repo/scripts/cedia/code15_scratch.sh"
scratch=$(code15_scratch "$out" recovery 2097152)
trap 'rm -rf -- "$scratch"' EXIT
tar -xf "$deps" -C "$scratch"
tar -xf "$hdf5deps" -C "$scratch"
export PYTHONPATH="$repo/src:$scratch${PYTHONPATH:+:$PYTHONPATH}"
export TMPDIR="$scratch" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
cd "$repo"
test -z "$(git status --porcelain)"
git rev-parse HEAD
sha256sum docs/performance_recovery/MODEL_PERFORMANCE_RECOVERY_PROTOCOL.json
case "$mode" in
    diagnose) python -B -u scripts/domain_adaptation/recovery_inputs.py "$@" ;;
    calibrate) python -B -u scripts/domain_adaptation/recovery_calibration.py "$@" ;;
    fit) python -B -u scripts/domain_adaptation/recovery_training.py "$@" ;;
    fit-full)
        gate=${5:?sealed full gate}
        allowed=$(python -c 'import json,sys; print(int(json.load(open(sys.argv[1]))["allow_full"]))' "$gate")
        if [ "$allowed" = 1 ]; then
            python -B -u scripts/domain_adaptation/recovery_training.py "${@:1:4}" full 20261112 --gate "$gate"
        else
            printf '%s\n' 'Full fine-tuning skipped: frozen gate did not trigger.'
        fi
        ;;
    fit-repeats)
        gate=${5:?sealed repeat gate}
        modes=$(python -c 'import json,sys; print(",".join(json.load(open(sys.argv[1]))["repeat_modes"]))' "$gate")
        test -n "$modes"
        python -B -u scripts/domain_adaptation/recovery_training.py "${@:1:4}" "$modes" 20261113,20261114 --gate "$gate"
        ;;
    select) python -B -u scripts/domain_adaptation/recovery_selection.py select "$@" ;;
    score) python -B -u scripts/domain_adaptation/recovery_selection.py score "$@" ;;
    report) python -B -u scripts/domain_adaptation/recovery_reporting.py "$@" ;;
    *) exit 2 ;;
esac
