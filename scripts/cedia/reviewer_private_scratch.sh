# Sourced inside a CEDIA allocation. Prints only the chosen directory.
reviewer_private_scratch() {
    local fallback=$1 base space scratch
    for base in "${SLURM_TMPDIR:-}" "${TMPDIR:-}" /var/tmp /tmp /dev/shm "$fallback"; do
        [[ -n "$base" && -d "$base" && -w "$base" ]] || continue
        space=$(df -Pk -- "$base" | awk 'END {print $4}')
        [[ "$space" =~ ^[0-9]+$ && "$space" -ge 2097152 ]] || continue
        if scratch=$(mktemp -d "$base/titan-review-$SLURM_JOB_ID-XXXXXX" 2>/dev/null); then
            printf '%s\n' "$scratch"
            return 0
        fi
    done
    echo "No authorized writable scratch with at least 2 GiB free" >&2
    return 1
}
