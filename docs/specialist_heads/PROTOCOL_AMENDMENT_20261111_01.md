# Protocol Amendment 01: Prior Evaluation Exclusion and WFDB Eligibility

**Applies to:** `specialist-heads-20261111-v2`  
**Frozen configuration:** [`study_20261111_v2.json`](../../configs/specialist_heads/study_20261111_v2.json)  
**Previous version:** [`study_20261111_v1.json`](../../configs/specialist_heads/study_20261111_v1.json)

## Reason

Before any new model-performance metric was calculated, review of the public V4.5 manifests showed that the V1 rhythm-development pool could include records that had already appeared in prior P6/P8 evaluation. Reusing those records in new training, calibration, or internal evaluation would contaminate the intended comparison. V1 was never trained and produced no feature cache, inventory, or preflight receipt; CEDIA jobs 33021 and 33026 both failed during input audit.

The first failure came from manual parsing of an optional WFDB field. Replacing that code with the official WFDB reader exposed headers with non-standard optional date metadata that the pinned WFDB parser does not accept. The raw headers are not rewritten, and sampling metadata is not inferred from malformed or unsupported content.

## Changes Frozen in V2

1. The audit verifies these repository manifests by SHA-256 before reading records:
   - `data/manifests/external_dev/rhythm_primary8_records.csv`: `b7e044ca1696eced6ac25f93cc1574d7c596c1cadfd4a98f86ca9d42699a11d0` (2,193 rows).
   - `data/manifests/external_dev/rhythm_primary6_diagnostic_records.csv`: `db6de6b83c353d7a671482667e91ac1d78de76bb169d5cd751874cb7b0d600ca` (1,643 rows).
2. Their record keys are matched by explicit source aliases and record basename. Every matched P6/P8 record is excluded from all new rhythm train, epoch-selection, threshold-calibration, internal-evaluation, and source-holdout splits. The audit computes the union of keys; manifest row counts are not added as if they were disjoint.
3. Exact-byte copies of the known prior rhythm-evaluation waveforms are also excluded, including copies under a different record basename. Near-duplicate signals remain undetected and are not claimed absent.
4. A header that WFDB cannot parse is assigned `invalid_wfdb_header`, kept only in the private inventory with its error type, and excluded from features and metrics. The aggregate receipt reports the exclusion count by source. There is no fallback parser and no data-driven amplitude cutoff.
5. V2 has a new study ID and hash namespace, so its remaining deterministic splits are distinct from V1. The V1 configuration and failed job logs remain preserved.

## Scientific Boundary

The amendment prevents known record-level reuse from prior public rhythm evaluation; it does not certify patient independence, remove re-encoded or near-duplicate signals, or establish that the frozen historical backbone never saw these sources. The P6/P8 manifests can overlap and are unioned by source and record key. PTB-XL fold 10 remains excluded. SPH and V3H remain unavailable as new independent tests. Independent external validation remains `NOT_RUN`.

V2 has not yet produced a successful preflight, feature cache, training run, or new performance result. GPU work remains gated on review of its aggregate preflight receipt.
