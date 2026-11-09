# SPH Post-Dedup Support Audit

## Purpose and Boundary

This audit measures aggregate label support remaining after signal-level eligibility checks and exact duplicate exclusion. It does not perform model inference, fit a specialist, select thresholds, calculate performance metrics, or establish independent validation. SPH has already been observed in V4.5 and in the PAC pilot; every result here is exploratory development evidence.

The frozen machine-readable contract is [sph_postdedup_support.json](../../configs/benchmarkmax/sph_postdedup_support.json). The job must run from the exact commit recorded in its receipt. The source signals, row-level labels, patient IDs, duplicate IDs, and record-level intermediate state remain in authorized CEDIA storage.

## Frozen Inputs and Population

The protocol pins the SHA-256 digests of SPH `metadata.csv`, `code.csv`, and `records.tar.gz`, plus the existing source-inventory digest. The expected source population is 25,770 ECG records from 24,666 patients. The inventory reports 25,770 valid signals, no source technical failures, 168 exact duplicate groups, and 168 duplicate excess records. The PAC pilot previously counted 336 records participating in those groups; this audit independently rechecks that count.

The runtime is Python 3.11.14, NumPy 2.4.3, and h5py 3.13.0. The h5py dependency archive is itself SHA-256 pinned in the configuration and checked by the SLURM wrapper.

## Signal-First Procedure

1. Read only ECG IDs and sample counts from metadata for the first pass. Diagnostic codes and patient IDs do not enter signal eligibility or duplicate detection.
2. Stream the archive without extracting HDF5 members to disk. Validate safe archive paths, unique member IDs, 12-lead HDF5 shape, finite samples, duration of 10-60 seconds at 500 Hz, and at least one non-flat lead.
3. Fingerprint each technically valid signal as SHA-256 over canonical little-endian float64 raw-array bytes. Exclude every record participating in any exact duplicate group. Near-duplicate detection is not performed.
4. Require the source counts and exact-duplicate counts to match the frozen protocol and source inventory. Only then join patient IDs and AHA statements.
5. Assign patients using the frozen label-blind SHA-256 split: train buckets 0-69, development 70-84, and exploratory holdout 85-99. The third bucket was already used as the exploratory PAC holdout, so it is not an untouched or confirmatory test.
6. Report aggregate ECG and patient counts by split and by six endpoints: ASMI (165), IMI (161), LVH (142), PAC (30), PVC (60), and RBBB (106). A missing AHA code is `statement_not_recorded`, not an adjudicated clinical negative.

## Interpretation Limits

Post-dedup support counts are candidate source support, not evidence that an endpoint is trainable or that a model can process every signal. The audit does not run branch-specific V3AG morphology extraction or V3F model preprocessing. A later training decision still needs an explicit model-input contract, rights/provenance review, training-only fitting, development-only selection, patient-level calibration rules, and a separate untouched evaluation cohort. A larger positive count does not resolve label quality, patient/source leakage, the previously observed status of SPH, or the lack of clinical adjudication.

The runner writes only aggregate counts and hashes to a mode-0600 private result. The independent verifier checks population reconciliation, per-split denominators, endpoint support arithmetic, non-overlap declarations, source digests, and the non-performance/non-identifier scope. Any mismatch fails closed; do not relax expected counts or duplicate policy to make a job pass.
