#!/bin/bash

# Probe actual directory creation: some CEDIA nodes expose a non-writable /tmp.
code15_scratch() {
    local study=${1:?study directory}
    local phase=${2:?CODE phase}
    local min_kib=${3:-12582912}
    local root shared free result
    [[ $phase =~ ^[a-z-]+$ && $min_kib =~ ^[0-9]+$ ]] || return 2
    shared="$study/.code15-scratch"
    for root in "${SLURM_TMPDIR:-${TMPDIR:-/tmp}}" "$shared"; do
        if [[ $root == "$shared" ]]; then
            mkdir -p -- "$shared" || return 1
        fi
        [[ -d $root ]] || continue
        free=$(df -Pk -- "$root" | awk 'NR == 2 {print $4}') || continue
        [[ $free =~ ^[0-9]+$ ]] && (( free >= min_kib )) || continue
        if result=$(mktemp -d -- "$root/titan-code15-$phase-XXXXXX"); then
            if [[ $root == "$shared" ]]; then
                printf 'CODE-15%% %s: using private project scratch\n' "$phase" >&2
            fi
            printf '%s\n' "$result"
            return 0
        fi
    done
    printf 'CODE-15%% %s: no writable scratch with %s KiB free\n' "$phase" "$min_kib" >&2
    return 1
}
