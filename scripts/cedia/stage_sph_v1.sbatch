#!/bin/bash
#SBATCH --job-name=titan_sph_stage
#SBATCH --partition=cpu-dev
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:20:00
set -euo pipefail
umask 077
if [[ $# != 1 || "$1" != /* || ! -d "$1" ]]; then
    printf 'Usage: sbatch %s ABSOLUTE_EXISTING_PRIVATE_DIRECTORY\n' "$0" >&2
    exit 2
fi
cd "$1"
test "$(stat -c '%u' .)" = "$(id -u)"
test "$(stat -c '%a' .)" = 700
# Allow download and future unpacking, without treating free space as quota.
available=$(df -Pk . | awk 'NR==2 {print $4}')
test "$available" -ge 6291456
exec 9>stage.lock
flock -n 9

fetch() {
    local name=$1 id=$2 bytes=$3 md5=$4 current
    if [[ ! -f "$name" ]]; then
        if [[ -f "$name.part" ]]; then
            current=$(stat -c '%s' "$name.part")
            test "$current" -le "$bytes"
        fi
        if [[ ! -f "$name.part" || $(stat -c '%s' "$name.part") -lt $bytes ]]; then
            curl --fail --location --silent --show-error --connect-timeout 15 \
                --max-time 960 --retry 2 --max-filesize "$bytes" --continue-at - \
                --output "$name.part" "https://ndownloader.figshare.com/files/$id"
        fi
        test "$(stat -c '%s' "$name.part")" -eq "$bytes"
        printf '%s  %s\n' "$md5" "$name.part" | md5sum -c
        mv -n -- "$name.part" "$name"
    fi
    test "$(stat -c '%s' "$name")" -eq "$bytes"
    printf '%s  %s\n' "$md5" "$name" | md5sum -c
}

fetch code.csv 32630954 1839 9fafec6cc6e1ef8117e2964116654d05
fetch metadata.csv 34793152 999219 8ef8e8789059a585c89c5302c7891909
fetch records.tar.gz 32630684 2281799680 0beef976f54cf0a95fac9f45bb157950
sha256sum code.csv metadata.csv records.tar.gz > "sha256-$SLURM_JOB_ID.txt"
file records.tar.gz
tar -tf records.tar.gz | awk 'END {print "Archive member count:", NR}'
