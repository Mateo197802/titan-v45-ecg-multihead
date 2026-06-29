# Release Process

Release `v0.1.0` stores weights and evaluated external-development cohorts outside Git history. `release-manifest.json` records file name, repository destination, byte count, SHA-256, license, source lineage, and download URL. `SHA256SUMS` duplicates the cryptographic inventory in standard text form.

The release is created as a draft, all assets are uploaded, downloaded into a clean clone, and verified before publication. Each file must remain below GitHub's 2 GiB per-file limit.
