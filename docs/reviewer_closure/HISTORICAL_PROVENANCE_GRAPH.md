# Historical Provenance Graph: Round 2

This is the human-readable index for [`HISTORICAL_PROVENANCE_GRAPH.json`](HISTORICAL_PROVENANCE_GRAPH.json), generated from the evidence package as of 2026-11-10. `VERIFIED` always refers to the narrow edge described; it does not imply that a full training chain is verified.

## Evidence roots

The second recovery ZIP has SHA-256 `d1d77535d2b1995fc8a1ba5e3b47cf9c63703cd29d4ef63334e5402fe731e82f`. Its inventory, checksums and ZIP CRC passed. It contains six CEDIA plan archives represented by 25 code/launcher/test text files. Fourteen delivered members match their declared source-member hashes; eleven launcher copies are marked sanitized and have distinct source/copy hashes. There are 24 unique member contents because the same S4 decision evaluator appears in two plan archives.

The archive-to-member byte relationships are authenticated against the supplied CEDIA receipt and the package manifests. The receipt is not a signed execution attestation. Full member digests, package digests and byte counts are in the JSON graph. Raw paths, raw receipts and source code are intentionally not copied here.

## Graph

```text
CEDIA S4/S5/U plan archive bytes
  ├─ VERIFIED_TO_SUPPLIED_RECEIPT → 25 packaged source/launcher/test members
  ├─ SUPPORTED_NOT_CRYPTO_LINKED → decision jobs 15493 (S4), 15504 (U)
  │    └─ expected decision outputs were not present in the bounded checks
  └─ no edge → June V4.5 checkpoint, all-input route, patient-level quarantine ledger

V3C jobs 16748-16759 (all COMPLETED)
  └─ UNVERIFIED → trial count / selected trial-6 JSON

trial-6 JSON path reference
  └─ SUPPORTED_NOT_CRYPTO_LINKED → job 16768 (COMPLETED)
       └─ UNVERIFIED → intermediate checkpoint bytes/hash
            └─ path reference → job 16781 (COMPLETED)
                 ├─ UNVERIFIED → fine-tuned output bytes/hash
                 └─ UNVERIFIED → published V3F backbone

V4 May Primary-9 error-subset routing (672 ECG)
  └─ WRONG_MODEL_VERSION → June V4.5 quarantine claim

V4.5 job-consumed splits / exact loader / 41M SQLite / June quarantine ledger
  └─ NOT_RECOVERED in the supplied round-2 evidence
```

## Interpretation

The new evidence verifies that particular plan source members exist with measured bytes and that specified SLURM jobs reached the recorded states. It does not show that a job opened those exact script, manifest, model or policy bytes. Expected output paths are not outputs. Submit-line hashes are not hashes of the script contents or checkpoint files.

The six S4/U plans concern binary/core viability and selection. Their source code explicitly sets `valid_for_gate=0` and leaves external release for manual action. S5 is a Flutter/PAC curation queue. None supplies the V4.5 per-ECG quarantine policy, scores, transition ledger, reference labels or pre/post denominator.

The V3C/V3F and Optuna relationships remain incomplete. V3F release-file identity is verified by its public artifact SHA, but the missing output digest from job 16781 prevents attributing that release file to the job. Twelve completed V3C SLURM jobs are not twelve completed trials. The original 41M database and its before-resume snapshot remain absent; the three 41M jobs are recorded failed.

The prior V4 May ledger remains separate from V4.5 June. Likewise, the previously recorded P4 replay residual and the lack of the exact 36,271-byte loader are unchanged. No split/patient isolation edge was added. See [`NEW_RECOVERY_EVIDENCE_INTEGRATION.md`](NEW_RECOVERY_EVIDENCE_INTEGRATION.md) for the detailed package audit and [`REMAINING_CRITICAL_ARTIFACTS.md`](REMAINING_CRITICAL_ARTIFACTS.md) for the exact recovery targets.
