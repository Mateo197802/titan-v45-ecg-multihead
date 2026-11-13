#!/bin/bash
# Submit the immutable training checkout once. The chain outlives this shell.
set -eo pipefail
repo=${1:?pinned repository}
study=${2:?private study directory}
deps=${3:?dependency archive}
hdf=${4:?HDF5 dependency archive}
previous=${5:?sealed development banks}
archive=${6:?sealed baseline scores}
node=${7:-compute-0-1}
umask 077
test -d "$study"
test -f "$deps"
test -f "$hdf"
cd "$repo"
test -z "$(git status --porcelain)"
exec 9>"$study/submit.lock"
flock -n 9
test ! -e "$study/slots"
dep=
for i in $(seq 1 9); do
    options=()
    if [ -n "$dep" ]; then
        options=(--dependency=afterany:"$dep")
    fi
    dep=$(sbatch --parsable "${options[@]}" --nodelist="$node" --time=00:40:00 +        --job-name=titan-loop --output="$study/slot-%j.log" +        scripts/cedia/titan_performance_recovery.sbatch "$PWD" autonomous "$study" "$deps" +        "$hdf" "$previous" "$archive" "$study/state")
    printf '%s\n' "$dep" | tee -a "$study/slots"
done
