# Historical Provenance Graph: CEDIA Recovery Rounds

This is the human-readable index for [`HISTORICAL_PROVENANCE_GRAPH.json`](HISTORICAL_PROVENANCE_GRAPH.json). Its Round 2 section below remains a dated historical record; the REV3-REV6 addendum began from PR #3 HEAD `52ae5743f33419e3d045d4e0c9ab58d93607e90a` and PR #4 HEAD `3cfedf39a81a22c867fde04faf9b1a1dd2f60448`. PR #3's core evidence integration is commit `34ef99dcd5de5e49e062eb10b0878da3a3731b51`; PR #4 was updated in its separate branch to `1d556ba5a58255b1eef97221da8107a9c8d120b0`. `VERIFIED` always refers to the narrow edge described; it does not imply that a full training chain is verified.

## Evidence roots

The second recovery ZIP has SHA-256 `d1d77535d2b1995fc8a1ba5e3b47cf9c63703cd29d4ef63334e5402fe731e82f`. Its inventory, checksums and ZIP CRC passed. It contains six CEDIA plan archives represented by 25 code/launcher/test text files. Fourteen delivered members match their declared source-member hashes; eleven launcher copies are marked sanitized and have distinct source/copy hashes. There are 24 unique member contents because the same S4 decision evaluator appears in two plan archives.

The archive-to-member byte relationships are authenticated against the supplied CEDIA receipt and the package manifests. The receipt is not a signed execution attestation. Full member digests, package digests and byte counts are in the JSON graph. Raw paths, raw receipts and source code are intentionally not copied here.

The separate CEDIA outer export has SHA-256 `4e7b9dcfbecf90a0427a60972a03020aaeb5a5e7e279ae0b826aa47cc252298b`; nested REV1/REV2 hashes and their inventories are verified in the canonical index. REV2 inventory rows include references and not-found/recovery-required classifications; those rows are not 145 newly recovered experiment artifacts. Source-side hashes in the export are CEDIA-reported metadata and were not recomputed from original CEDIA bytes.

## Graph

```text
CEDIA S4/S5/U plan archive bytes
  ├─ VERIFIED_TO_SUPPLIED_RECEIPT → 25 packaged source/launcher/test members
  ├─ SUPPORTED_NOT_CRYPTO_LINKED → decision jobs 15493 (S4), 15504 (U)
  │    └─ expected decision outputs were not present in the bounded checks
  └─ no edge → June V4.5 checkpoint, all-input route, patient-level quarantine ledger

CEDIA REV2 scheduler/AF receipt summaries
  ├─ REPORTED COMPLETED → jobs 15874, 15880, 15885, 15886, 15887, 15903, 15905
  ├─ no afterok edge within W/Z/AC/AD/AE/AF; no verified input-read digest
  ├─ REPORTED_NOT_RECOMPUTED → AF aggregate metrics and 23 handoff rows
  └─ NOT_LINKED → complete V4.5 eligible denominator / quarantine transitions

V3C jobs 16748-16759 (all COMPLETED)
  └─ UNVERIFIED → trial count / selected trial-6 JSON

trial-6 JSON path reference
  └─ SUPPORTED_NOT_CRYPTO_LINKED → job 16768 (COMPLETED)
       └─ UNVERIFIED → intermediate checkpoint bytes/hash
            └─ path reference → job 16781 (COMPLETED)
                 ├─ UNVERIFIED → fine-tuned output bytes/hash
                 └─ UNVERIFIED → published V3F backbone

V4 May Primary-9 error-subset routing (672 ECG)
  ├─ RECOMPUTED_FROM_HASHED_AGGREGATES → sanitized receipt (Level C; same legacy scope)
  └─ WRONG_MODEL_VERSION → June V4.5 quarantine claim

V4.5 job-consumed splits / exact loader / 41M SQLite / June quarantine ledger
  └─ NOT_RECOVERED or NOT_LINKED in the supplied exports
```

## Interpretation

The package audits verify the supplied ZIP/nested ZIP bytes, CRCs and internal checksum manifests. CEDIA REV2 adds reported scheduler states, repeated AF summary values, May cache-key checks and reported released-backbone hash matches. It does not provide the raw execution logs, source-side input bytes or file-read digests needed to authenticate those claims against the original CEDIA files. Expected output paths are not outputs. Submit-line hashes are not hashes of the script contents or checkpoint files.

The six S4/U plans concern binary/core viability and selection. Their source code explicitly sets `valid_for_gate=0` and leaves external release for manual action. S5 is a Flutter/PAC curation queue. The separate AF summaries report 23 handoff rows, `valid_for_gate=0`, and `external_gate_allowed=false`; they do not supply a V4.5 per-ECG quarantine policy, complete denominator, transition ledger, reference labels or pre/post counts. The handoff count must not be used as a quarantine numerator or denominator.

The V3C/V3F and Optuna relationships remain incomplete. V3F release-file identity is verified by its public artifact SHA, but the missing output digest from job 16781 prevents attributing that release file to the job. Twelve completed V3C SLURM jobs are not twelve completed trials. The original 41M database and its before-resume snapshot remain absent; the three 41M jobs are recorded failed.

The prior V4 May ledger remains separate from V4.5 June. Likewise, the P4 replay residual (`0.0006194115` versus `1e-5`) and absence of the exact 36,271-byte loader are unchanged. May cache-key disjointness does not certify patient/signal independence or the manifests consumed by June jobs. See [`HISTORICAL_RECOVERY_CANONICAL_INDEX.md`](HISTORICAL_RECOVERY_CANONICAL_INDEX.md), [`PLAN_AE_AF_QUARANTINE_EVIDENCE.md`](PLAN_AE_AF_QUARANTINE_EVIDENCE.md), [`REVIEWER_15_CEDIA_REV2_ADDENDUM.md`](REVIEWER_15_CEDIA_REV2_ADDENDUM.md), and [`REMAINING_CRITICAL_ARTIFACTS.md`](REMAINING_CRITICAL_ARTIFACTS.md) for detailed claims and recovery requirements.

## Addendum: CEDIA REV3-REV6 (2026-11-11)

All four CEDIA-exclusive revision packages pass ZIP SHA-256, CRC, safe-member-name, internal checksum and inventory checks. REV6 has 48 members, 273 inventory rows and 47 checksum entries; 45 exported payload hashes match the package export records (29 labeled identical and 16 sanitized). The original CEDIA source bytes were not rehashed from a live CEDIA source. The revisions are cumulative: adjacent comparisons show 23/30, 26/32 and 25/34 same-byte members, with 2, 2 and 13 additions. Exact package hashes and counts are in the [machine-readable graph](HISTORICAL_PROVENANCE_GRAPH.json) and [audit receipt](receipts/CEDIA_REV3_REV6_PACKAGE_AUDIT_2026-11-11.json).

REV6's 47 payload members were compared against 591 tracked PR #3 files and 368 tracked PR #4 files. Each tree had one content match, the same backbone implementation already tracked in PR #3 at a different path; there were zero exact relative-path-and-byte matches. Nine of ten exported source-code copies add content versus tracked PR #3; one is a duplicate. Their hashes and byte counts are indexed as `SRC-REV6-01` through `SRC-REV6-10`. Export-byte verification does not authenticate original CEDIA bytes or show job execution.

| Chain or claim | New bounded observation | Edge status | What remains unproved |
|---|---|---|---|
| Trial 6 / job 16781 / V3F | Released metadata `parent_checkpoint` text agrees with the input path declared by job 16781. | `PATH_REFERENCE_ONLY` | No parent read digest, job-16781 output bytes/hash or promotion receipt links its output to the released V3F file. |
| V3F auxiliary rhythm supervision | Static trainer copies show a 14-output target/loss path and a separate V3F fine-tune path restricted to P8/P4. | Static behavior only; source-to-job edge `UNVERIFIED` | Which source/config/manifests a release job used, secondary label supports, and checkpoint-linked metrics. |
| ALMI/ILMI/LAE | Static generic pathology code has seven target positions and a row-level presence mask. Omitted labels enter as zero; this is not a per-class unknown mask. | Static behavior only; source-to-job edge `UNVERIFIED` | Label completeness, effective supports, job execution, checkpoint linkage, calibration and performance. |
| Hidden-width report | A separate P4 epoch-report path can instantiate width 512 while writing a `192` metadata field. | Possible static mechanism; not job-linked | This does not explain the P6/P8 runtime width discrepancy or establish the P4 release training configuration. |
| Optuna objective | REV6 has a static source copy with a 60/40 P8/P4 base objective, optional modifiers, missing-class penalties and stability ranking. | Source copy verified in package; May job edges `UNVERIFIED` | Effective CLI args, SQLite bytes, which implementation jobs 13169/13172/13181 used, complete trials and trial-to-checkpoint link. PR #4 separately retains the 45/35/10/10 log-derived observation. |
| Plan AE/AF | REV6 repeats reported AE policy/manifest hashes and AF summaries with 23 handoff rows and `valid_for_gate=0`. | Reported summary only | Original policy/manifest bytes and recomputed hashes, full denominator, checkpoint, uncertainty inputs and per-record pre/post ledger. Do not calculate a quarantine rate from 23 rows. |

The new round adds **zero original V4.5 artifacts newly linked to a producing job and released checkpoint**. It refines static-source behavior for R2-3c/R2-3d and clarifies the possible 192/512 report-writer mechanism for R2-3f. A follow-up filename-only CEDIA search in the known project and named backup roots found no target artifacts; its bounded scope and exclusions are in [the search receipt](receipts/CEDIA_TARGETED_RECOVERY_SEARCH_2026-11-11.json). The exact loader remains absent; P4 score residual remains `0.0006194115` against `1e-5`; P6/P8 replay agreements remain unchanged. Historical patient independence remains uncertified. REV6 does not resolve June quarantine or 41M Optuna provenance. See the [final CEDIA report](CEDIA_FINAL_RECOVERY_REPORT.md), [source authentication](CEDIA_SOURCE_CODE_AUTHENTICATION.md), [PR #4 Optuna handoff](OPTUNA_PR4_EVIDENCE_HANDOFF.md), and [reviewer coverage](REVIEWER_15_COVERAGE_AND_CEILING.md).
