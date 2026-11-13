#!/usr/bin/env bash
# Replay the retained historical panels without changing the old worktree.
set -euo pipefail
umask 077
if [[ $# != 5 ]]; then
    echo "Usage: $0 HISTORICAL_CHECKOUT RELEASE_ROOT DEPS_ARCHIVE NEW_ROOT EXPERIMENT_COMMIT" >&2
    exit 2
fi
history=$1 release=$2 deps=$3 root=$4 experiment_commit=$5
p4_commit=02019b832fafecd0c263ea556c70f16fa0a50ccf
rhythm_commit=cfe6d59fa5cc4be10de0d7c6803fa5208fae0072
audit_commit=a10f1b1eab62de241c8913a7b9f3c559e37d9b7e
[[ "$experiment_commit" =~ ^[0-9a-f]{40}$ ]]
[[ $(cd "$history" && git rev-parse HEAD) == "$audit_commit" ]]
[[ -z $(cd "$history" && git status --porcelain) ]]
test -s "$deps"
for commit in "$p4_commit" "$rhythm_commit"; do
    (cd "$history" && git cat-file -e "$commit^{commit}")
done
mkdir -m 700 -- "$root"
for tag in p4 rhythm; do
    commit=$p4_commit
    [[ "$tag" != rhythm ]] || commit=$rhythm_commit
    git clone --shared --no-checkout -- "$history" "$root/$tag-source"
    (cd "$root/$tag-source" && git checkout --detach "$commit" \
        && test -z "$(git status --porcelain)" && bash -n scripts/cedia/run_frozen_p4_cascade.sbatch)
done
printf 'EXPERIMENT_COMMIT=%s\nP4_SOURCE=%s\nRHYTHM_SOURCE=%s\nAUDIT_SOURCE=%s\n' \
    "$experiment_commit" "$p4_commit" "$rhythm_commit" "$audit_commit" > "$root/jobs.env"
p4=$(sbatch --parsable --job-name=titan-review-historical-p4 \
    --output="$root/p4-%j.out" --error="$root/p4-%j.err" \
    "$root/p4-source/scripts/cedia/run_frozen_p4_cascade.sbatch" \
    "$root/p4-source" "$release" "$deps" "$root")
p4=$(cut -d';' -f1 <<< "$p4")
[[ "$p4" =~ ^[0-9]+$ ]]
printf 'P4_JOB=%s\n' "$p4" >> "$root/jobs.env"
rhythm=$(sbatch --parsable --time=00:10:00 --job-name=titan-review-historical-rhythm \
    --output="$root/rhythm-%j.out" --error="$root/rhythm-%j.err" \
    "$root/rhythm-source/scripts/cedia/run_frozen_p4_cascade.sbatch" \
    "$root/rhythm-source" "$release" "$deps" "$root" rhythm)
rhythm=$(cut -d';' -f1 <<< "$rhythm")
[[ "$rhythm" =~ ^[0-9]+$ ]]
printf 'RHYTHM_JOB=%s\n' "$rhythm" >> "$root/jobs.env"
audit=$(sbatch --parsable --dependency="afterok:$p4:$rhythm" --kill-on-invalid-dep=yes \
    --output="$root/audit-%j.out" --error="$root/audit-%j.err" \
    "$history/scripts/cedia/run_replay_diagnostics.sbatch" \
    "$history" "$root/p4-cascade-$p4/ledger.jsonl" "$root/rhythm-cascade-$rhythm/ledger.jsonl" "$root")
printf 'AUDIT_JOB=%s\n' "$(cut -d';' -f1 <<< "$audit")" >> "$root/jobs.env"
cat "$root/jobs.env"
