# Historical Provenance Graph: Round 2 And CEDIA REV2

This is the human-readable index for [`HISTORICAL_PROVENANCE_GRAPH.json`](HISTORICAL_PROVENANCE_GRAPH.json), reconciled against the live PR #3 HEAD `307ddaf3e3d840a624009d10f53923db307a500c` on 2026-11-10. `VERIFIED` always refers to the narrow edge described; it does not imply that a full training chain is verified.

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
