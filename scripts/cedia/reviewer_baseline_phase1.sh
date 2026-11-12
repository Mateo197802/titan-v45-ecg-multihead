#!/usr/bin/env bash
# Submit exactly one baseline. All paths must be in authorized CEDIA storage.
set -euo pipefail
umask 077
if [[ $# != 8 ]]; then
    echo "Usage: $0 FROZEN_TREE SPH_SOURCE RELEASE_ROOT DEPS H5PY_DEPS DUPLICATES NEW_RUN_ROOT EXPERIMENT_COMMIT" >&2
    exit 2
fi
tree=$1 source=$2 release=$3 deps=$4 h5=$5 duplicates=$6 root=$7 experiment_commit=$8
frozen_commit=eb1c67b9229af875a9f868797b0c2f5c546e3dac
protocol_sha=d788ad8cca94793cebb738496acc131e82b1ca1900976f11020b99a79a5fc366
[[ "$experiment_commit" =~ ^[0-9a-f]{40}$ ]]
[[ $(git -C "$tree" rev-parse HEAD) == "$frozen_commit" ]]
[[ -z $(git -C "$tree" status --porcelain) ]]
[[ $(sha256sum "$tree/configs/external_validation/sph_frozen.json" | cut -d' ' -f1) == "$protocol_sha" ]]
for f in "$source/metadata.csv" "$source/code.csv" "$source/records.tar.gz" "$deps" "$h5" "$duplicates"; do
    test -s "$f"
done
test -d "$release"
# An existing root indicates a previous attempt; inspect its scheduler state instead of resubmitting.
mkdir -m 700 -- "$root"
printf 'EXPERIMENT_COMMIT=%s\nBASELINE_COMMIT=%s\nPROTOCOL_SHA256=%s\n' \
    "$experiment_commit" "$frozen_commit" "$protocol_sha" > "$root/run.env"
job=$(sbatch --parsable --job-name=titan-review-baseline --time=02:00:00 \
    --output="$root/baseline-%j.out" --error="$root/baseline-%j.err" \
    "$tree/scripts/cedia/score_sph_frozen.sbatch" \
    "$tree" "$source" "$release" "$deps" "$h5" "$duplicates" "$root" "$frozen_commit" "$protocol_sha" 16)
[[ "$job" =~ ^[0-9]+(\;.*)?$ ]]
printf 'BASELINE_JOB=%s\n' "$(cut -d';' -f1 <<< "$job")" >> "$root/run.env"
cat "$root/run.env"
