# Recovery ZIP addendum for internal audits

**As of:** 2026-11-10
**Archive SHA-256:** `23523fb59501b916cc6cea55ad0ae669387dbd0b10267a2d4bac7d353f8b5d06`
**Machine-readable record:** [`REVIEWER_48_DETAILED.json`](REVIEWER_48_DETAILED.json), field `recovery_zip_internal_audit_update`.

The original audit statuses are unchanged. This addendum records only bounded evidence and checks from the recovery ZIP. It does not modify the 21 editorial-only reviewer items.

| Audit | New evidence verified within scope | Status change | Remaining limit |
|---|---|---|---|
| A-01 | P4 denominator units reconfirmed: 962 panel observations, 733 ECG, 676 linked patients. | None; remains `VERIFIED_COMPLETE`. | Do not treat panel observations as unique ECGs. |
| A-02 | Received derived audit reports one exact duplicate pair in rhythm and none in the P4 set; no source-crossing group. | None; remains `VERIFIED_WITH_LIMITATIONS`. | Not rerun from raw waveforms; aliases, transformed duplicates and patient independence remain unresolved. |
| A-03 | Canonical P4 aggregate means reconfirmed at 80.23% mean binary accuracy and 79.35% macro-F1. | None; remains `VERIFIED_WITH_LIMITATIONS`. | Apply values consistently only during later approved manuscript editing. |
| A-04 | Four P4 calibration thresholds and 1,492 calibration panel-window observations cross-checked against retained checkpoint/log evidence. | None; remains `EVIDENCE_CEILING_REACHED`. | Consumed manifest bytes, patient grouping and calibration/evaluation isolation remain unverified. |
| A-05 | Public checkpoint hashes and serialized global/specialist dimensions verified. | None; remains `VERIFIED_COMPLETE`. | Tensor shapes do not prove training lineage or patient isolation. |
| A-06 | Two separate 41M generations, two bounded logged completed-trial observations and their parameters documented in PR #4. | None; remains `EVIDENCE_CEILING_REACHED`. | Original SQLite/WAL/SHM and trial-to-checkpoint promotion link absent. |
| A-07 | Recovery archive integrity passed; the private archive was not published. | None; remains `VERIFIED_WITH_LIMITATIONS`. | Later data-availability wording must cite approved public artifacts and restricted inputs. |
| A-08 | No final supplement was assembled from the recovery archive. | None; remains `MANUSCRIPT_ONLY_PENDING`. | Reconcile promised supplementary files during the editorial phase. |
| A-09 | No bibliography change was made. | None; remains `MANUSCRIPT_ONLY_PENDING`. | Verify/correct the DOI during the editorial phase. |
| A-10 | Archive screened; raw receipts and private clinical material were not published. | None; remains `ACTIVE_RECOVERY_REQUIRED`. | Source provenance and redistribution rights still require custodian/author evidence. |
| A-11 | No clinical interpretability or adjudicated Grad-CAM experiment was added. | None; remains `NEW_EXPERIMENT_REQUIRED`. | Restrict claims or conduct a separately authorized expert/faithfulness study. |
| A-12 | V4 May error-subset arithmetic is verified but is not clinician review. | None; remains `NEW_EXPERIMENT_REQUIRED`. | No human-review ledger; a retained reader-benefit claim requires an approved reader study. |
