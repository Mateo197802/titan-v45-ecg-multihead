# Recovery Round-2 Conflict Resolution

As of 2026-11-10. This note distinguishes actual contradictions from differences in scope, time or evidentiary level. No historical metric, checkpoint, threshold or matrix status was rewritten.

| Observation A | Observation B | Resolution | Status |
|---|---|---|---|
| The recovery report says `REMAINING_HISTORICAL_RECOVERY_TARGETS.md` returned 404 at pinned PR #3 commit `4d5e7cc`. | The file exists on the current PR #3 head `e8f3179`. | The package inspected an earlier commit. The file was added later; this is temporal drift, not current absence. | Resolved by live-head check |
| Jobs 16748-16759 are all recorded `COMPLETED`. | The V3C snapshot contains nine trial rows from twelve planned. | SLURM job count is not Optuna trial count. No inference that twelve trials completed. | No contradiction; trial history incomplete |
| Jobs 16768 and 16781 are `COMPLETED`, `0:0`. | Expected intermediate checkpoints, logs and digest-of-read/output files are not present in the bounded checked locations. | Job accounting and artifact availability are different facts. A successful exit does not prove a specific output exists or was promoted. | Edge remains unverified |
| Jobs 15493 and 15504 are `COMPLETED`, `0:0`. | Their expected decision JSON/MD/CSV outputs were absent in the bounded path checks. | Preserve both facts. The missing output may have been moved/removed or the output root may differ; the package does not resolve why. | Conflict remains operationally unexplained |
| S4/U jobs are called decision jobs and contain decision criteria. | A reviewer requests June V4.5 per-ECG quarantine and pre/post outcomes. | Static source indicates model/class viability decisions, `valid_for_gate=0` and manual release, not a per-ECG quarantine ledger. Do not map one to the other. | Not the same estimand or artifact |
| V4 May evidence records 672 Primary-9 ECG and error-subset routing. | V4.5 June quarantine remains not assessed. | The May result is a different model/version and population. It cannot close the June V4.5 request. | Wrong-version edge rejected |
| The P6/P8 serialized field says 192 while specialist tensors store width 512. | Recovered trainer/source excerpts include explicit 512 classwise construction and other defaults/metadata. | The source read is corroborative and does not prove which exact code wrote the released checkpoint metadata. Keep the mismatch and its cause open. | Not resolved |
| Fourteen delivered source members match their source digest; eleven sanitized files do not. | The inventory gives different hashes for source and delivered sanitized copies. | This is expected for marked sanitization, not corruption. Only the 14 identical members are treated as byte-identical to the supplied source-member digest. | Resolved by identity class |
| The package re-reads two trainer/runtime sources already discussed in the prior report. | It provides a more specific interpretation of the 192/512 discrepancy. | The source bytes are not a new recovery. The interpretation may be recorded as corroboration but does not increase technical coverage or establish a new job edge. | Duplicate/corroborative, not new primary |

## Unresolved items

1. Why successful S4/U decision jobs have no expected outputs in the locations checked.
2. Whether the referenced V3C JSON and intermediate checkpoints survive elsewhere; their actual bytes and job read/write digests remain absent.
3. Why the V3F release artifact has no authenticated output-hash link to job 16781.
4. Whether any external institutional backup exists beyond the bounded records and the custodian's previously reported September listing. A failed Windows shadow-copy catalog query is not evidence that no snapshot exists.

The package report's custody request is an unsent draft. This integration did not contact CEDIA/NOC, inspect new backup sources, or infer that absent paths mean no backup exists.
