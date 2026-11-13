# SPH duplicate-audit receipt field clarification

The immutable aggregate from CEDIA job `32627`,
[`sph_duplicate_amplitude_audit_32627.json`](../../outputs/results/external_sph/sph_duplicate_amplitude_audit_32627.json),
contains a misleading field name. Its `source_inventory_sha256` value is
`c6f8dc5197758a3970aae554f8b6ee884d96656b121879bc0eb1adf367ea6d86`,
which is the SHA-256 of SPH `metadata.csv`, not the SHA-256 of the aggregate
source-inventory report. The original implementation hashes `metadata.csv`
for that field; the original receipt is preserved unchanged.

The separate source-inventory aggregate from job `32617` is
[`source_inventory_32617.json`](../../outputs/results/external_sph/source_inventory_32617.json),
with SHA-256 `8321abf1d91f0a97ae65b8e9d3a47ba4f5460055ac7780fd84ad2cc86efd2cf7`.
The pre-performance protocol pins both control aggregates independently.
This clarification corrects artifact identification; it does not by itself
rerun the audit or establish independence or clinical performance.
