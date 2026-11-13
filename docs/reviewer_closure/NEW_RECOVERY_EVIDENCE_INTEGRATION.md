# Directed2 Historical Recovery Evidence Integration

As of 2026-11-10. This document records the `TITAN_V45_RECUPERACION_DIRIGIDA_2_2026-11-10.zip` findings. It is specific to that package and does not replace the separate reconciliation of the later CEDIA REV1/REV2 export in [`HISTORICAL_RECOVERY_CANONICAL_INDEX.md`](HISTORICAL_RECOVERY_CANONICAL_INDEX.md). Neither report claims that the submitted study has been reproduced.

## Package validation

- ZIP SHA-256: `d1d77535d2b1995fc8a1ba5e3b47cf9c63703cd29d4ef63334e5402fe731e82f`.
- Outer archive: 38 files; CRC passed; no duplicate ZIP member names or unsafe archive paths.
- `INVENTARIO_ZIP.csv`: all 36 rows match packaged bytes and SHA-256.
- `SHA256SUMS.txt`: all 37 listed entries match. It covers the 36 inventory rows plus the inventory file; the checksum file does not checksum itself.
- Static privacy screen: 38 text members scanned; no common private-key/token markers, record/patient-ID CSV headers, or selected JSON record-identifier values were detected. The receipts do contain internal paths. This bounded scan is not a universal privacy certification, so raw receipts and the ZIP are not published.
- The archive inventory and checksums establish package-byte integrity. They do not independently authenticate the CEDIA custody chain or prove that a job consumed a particular source file.

The existing versioned verifier was extended to accept this package's `ruta` inventory schema as well as the prior `ruta_relativa` schema. A regression test rejects traversal in inventory paths. The original round-2 audit compared PR #3 commit `e8f3179866d1199cbb98966f328d37774baa646d` and PR #4 commit `3cfedf39a81a22c867fde04faf9b1a1dd2f60448`; the later CEDIA REV2 audit used the live PR #3 HEAD recorded in the canonical index.

## What is genuinely new

The package contains six source-plan archives represented by 25 code/launcher/test members as text, not executable files. CEDIA receipt member digests match 14 delivered members byte-for-byte. Eleven launcher copies are explicitly marked sanitized and have different source and delivered hashes. The sanitized copies were not treated as original bytes. One decision-evaluator member occurs identically in both the original and repair S4 packages; it is one unique content item, not two discoveries. Thus there are 24 unique member contents among 25 inventory rows.

| Source archive | Bytes | SHA-256 |
|---|---:|---|
| `plan_s4_binary_split_20260617.tgz` | 9,813 | `8425019f660c6646190028dab0d4d7076225077efa34ae4aeb29e4551ed025b5` |
| `plan_s4_binary_split_repair_20260617.tgz` | 10,122 | `f0f281fd87c7d92d4bc22c3a227e0d344dbb370fefc1d043c6f4cd9b324a94bb` |
| `plan_s4_decision_fix_20260617.tgz` | 1,887 | `0822ec352a2cefecb77e9f2a7dee08cb8edb168167058097edca9b8e9d01cf0c` |
| `plan_s5_flutter_pac_queue_20260617.tgz` | 4,046 | `e8690d09b3df34e4c99facddfcece2bab778be1ffe7ca0a5d82cba44e5270828` |
| `plan_u_decision_fix_20260618.tgz` | 4,239 | `64c67d605676cfc837d70cbcc1d3eda8b41d4193e487684c20114b8352fa1261` |
| `plan_u_robust_core_20260618.tgz` | 7,335 | `b2ec526bb3c0a21544b60003d840ba53acd41c23d3a74cdb77e5112726fbf7e1` |

The per-member source and delivered digests are recorded in [`HISTORICAL_PROVENANCE_GRAPH.json`](HISTORICAL_PROVENANCE_GRAPH.json). Raw source archives, unsanitized receipts, paths and scripts remain outside Git because this integration needs their identity and bounded behavior, not redistribution of the private export.

The new bundle has 37 payload files after excluding its checksum file. Byte comparison found 0/37 identical payloads in the tracked files of PR #3 (573 tracked files at the pinned ref) and 0/37 in PR #4 (368 tracked files). It also found no exact payload match against the earlier complete-recovery ZIP. The repeated S4 evaluator is an internal duplicate within this bundle and is counted once above.

## Historical links and limits

### S4, S5 and U plans

Static inspection of recovered text shows that the S4 decision code computes viability criteria for binary branches, sets `valid_for_gate=0`, disallows Optuna progression in the decision payload, and leaves external release manual. U similarly evaluates core-class viability, routes weak classes to review/defer decisions, sets `valid_for_gate=0`, and leaves external release manual. S5 builds a Flutter/PAC data-teacher or manual waveform-review queue. These are plan/selection or curation components; they are not evidence of the released V4.5 checkpoint's all-input routing, patient-level evaluation, a quarantine ledger, or clinical review having occurred. No recovered script was executed.

The CEDIA receipt reports decision jobs 15493 (S4) and 15504 (U) completed with exit `0:0`; the expected decision outputs were absent from the bounded paths checked in the receipt. The job records and source archive names support a plan-to-job association, but there is no digest of the exact script consumed by either job. This is `SUPPORTED_NOT_CRYPTO_LINKED`, not a verified execution edge.

### V3C trial 6 and V3F

The receipt corroborates that jobs 16748-16759, 16768 and 16781 ended `COMPLETED`. Twelve completed SLURM jobs do not establish twelve completed Optuna trials. Submission records for 16768 reference `selected_candidate_v3c_trial6_final.json` and its expected run output; 16781 references the expected 16768 checkpoint as a base. No exact JSON, intermediate checkpoint, stdout/stderr, digest-of-read input or digest-of-written output was recovered in this package. The release V3F backbone still hashes to `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8`, but this does not bind it to job 16781. The chain remains incomplete; see [`V3C_TRIAL6_CHECKPOINT_LINEAGE.md`](V3C_TRIAL6_CHECKPOINT_LINEAGE.md).

### Optuna 41M and A10

No original SQLite database, before-resume SQLite snapshot, WAL/SHM set, complete trial export, or new trial-to-checkpoint link is present. Jobs 13169, 13172 and 13181 remain failed in the supplied receipt. A damaged log backup produced literal references only and is not a recovered database. The two Optuna generations remain separate. No A10 artifact was added or changed. PR #4 remains the governing place for its existing bounded correction; see [`OPTUNA_PR4_EVIDENCE_HANDOFF.md`](OPTUNA_PR4_EVIDENCE_HANDOFF.md).

### Splits, loader, architecture and quarantine

- No job-consumed train/validation/calibration manifests, V3H/V3S parent populations, exclusion ledger, patient map or new split counts were recovered. `PATIENT_ISOLATION_NOT_CERTIFIED` remains unchanged.
- No candidate in the six plans matches the exact loader requirement `fc8d7367f9f2c108376839435021ec3172fe2757faa4a615f0ef5d39cbf1e855` (36,271 bytes LF). The loader is not identified by this round.
- Re-reading the previously inventoried trainer/runtime source corroborates the already documented 512 classwise constructor and 192 metadata/default discrepancy; it is not a new source artifact and does not establish which code wrote the released checkpoint metadata. Tensor dimensions and serialized metadata are unchanged.
- No V4.5 per-ECG uncertainty/quarantine ledger, policy-score pair, or complete pre/post denominator was recovered. S4/U decision jobs are not quarantine evaluation. V4 May's 672-record error-subset routing remains a different model version and is not evidence for June V4.5.
- No fresh SPH, MIMIC, external-cohort, model-inference, or training result was generated. Existing SPH evidence and its independence limitation are unchanged.

## Reviewer impact

The round adds bounded historical context for R1-2, R1-4, R2-3a/c/e, R2-4e and R2-4k, and corroborates existing boundaries in R1-1, R2-3f and other technical items. It closes no previously unmet original reviewer subrequirement. The 15 technical item states therefore remain 12 `PARTIALLY_ADDRESSED` and 3 `NOT_SATISFIED`; all 21 editorial-only items remain unchanged. Per-item evidence and coverage calculations are in [`REVIEWER_15_EVIDENCE_UPDATE.md`](REVIEWER_15_EVIDENCE_UPDATE.md). The later CEDIA REV2 addendum is linked from the authoritative 48-item matrix, with no status or coverage change.

## Reproducibility and publication boundary

No recovered code, shell script, notebook, model or dataset was executed. The original directed2 review did not launch training/inference or query CEDIA. The subsequent CEDIA REV2 integration added a bounded in-memory archive verifier and regression tests; its receipt, package counts and privacy limits are recorded in [`receipts/CEDIA_REV2_INTEGRATION_2026-11-10.json`](receipts/CEDIA_REV2_INTEGRATION_2026-11-10.json). No manuscript/PDF/figure/response edit, PR #4/#5 modification, merge or historical artifact modification occurred.
