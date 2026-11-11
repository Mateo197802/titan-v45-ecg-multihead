# Plan AE/AF Evidence and Quarantine Boundary

This note records what the CEDIA REV2 export supports about the AE/AF jobs and what would be needed to establish a V4.5 historical quarantine result. It does not treat an output summary as a complete workflow replay.

## Reported execution metadata

The CEDIA export reports jobs 15874, 15880, 15885, 15886, 15887, 15903 and 15905 as completed with exit code `0:0`. There is no `afterok` edge among W/Z/AC/AD/AE/AF; job 15874 refers to upstream job 15873 outside this sequence. The recorded submit-line hashes are metadata values, not hashes of the executed source script or inputs. The original scheduler logs, exact run scripts and file-read digests were not transferred.

The two AF summaries report the same AE policy and manifest digests:

| Input | SHA-256 as reported by AF | Original bytes available for recomputation |
|---|---|---|
| AE policy | `14c4e62376d7fdfe86221648d153170c164392f633bd3864225bb25f3dd8a14e` | No |
| AE quarantine manifest | `9a08a369c563576947a0a9da9b916db376efe6c582c9e0e6563b36589d841bad` | No |

These matching reported digests support consistency between the two summaries only. They do not authenticate the original files or prove those bytes were opened by the jobs.

## AF summaries as reported

| Scope | Evaluated rows reported | Accuracy reported | Macro-F1 reported |
|---|---:|---:|---:|
| Rhythm | 1,895 | 0.8506596306068601 | 0.8451000156963052 |
| Pathology | 2,105 | 0.9745368171021378 labelwise accuracy | 0.6803098698964074 |
| Primary internal mean | Not an all-input denominator | 0.912598223854499 | Not reported as a profile-specific macro-F1 |
| Package primary class-balanced | Not an all-input denominator | Not an accuracy | 0.7862463921963416 |

Both summaries report 23 handoff rows, `valid_for_gate=0` and `external_gate_allowed=false`. CEDIA reports stdout SHA-256/byte counts, but raw stdout was not transferred or rehashed here. No row-level predictions or confusion matrices were available for independent metric recomputation.

| AF job | stdout SHA-256 as reported by CEDIA | Bytes | Reported mtime (UTC) |
|---:|---|---:|---|
| 15903 | `ed9e3bc4b3ea169649050bea9ada71c7ac33b8bfe118ef9ee421f025e6d4981a` | 3,799 | 2026-06-19 16:08:20 |
| 15905 | `93f6a9c95d9b03f723a177a8e09adfddd7c496d55b20f9029a8857df1923cd91` | 4,708 | 2026-06-19 16:24:54 |

The seven reported submit-line SHA-256 values and the external dependency note are recorded in [`HISTORICAL_PROVENANCE_GRAPH.json`](HISTORICAL_PROVENANCE_GRAPH.json). Those are CEDIA receipt values; none is claimed to be the executed script, policy, manifest or model hash.

## Quarantine conclusion

The 23 handoff rows are not known to be the complete eligible population, all errors, all uncertain predictions, or all quarantine events. The 1,895/2,105 evaluated rows are profile-specific scored subsets, not an established full-input denominator. Therefore none of these numbers supports a quarantine rate, zero-quarantine claim, pre/post error movement or clinical coverage. The correct V4.5 historical status remains `NOT_ASSESSED`.

Do not conflate these summaries with the separate May 2026 TITAN V4 Primary-9 error-subset routing (672 ECG; 461 correct and 211 errors). That is a different model version, population and policy; it cannot establish June V4.5 quarantine.

## Exact evidence needed to reopen

1. Original AE policy, manifest and uncertainty-score bytes, plus sizes and custodian-computed SHA-256 values.
2. Exact executed scripts/configurations and scheduler stdout/stderr for jobs 15874/15880/15885/15886/15887/15903/15905, with dependency records and input read digests.
3. Complete eligible ECG denominator and inclusion/exclusion ledger linked to the same policy, population, model checkpoints and jobs.
4. Record-linked pre/post decisions, uncertainty scores, threshold, routing state and reason; truth/reference outcomes for error accounting. Keep these restricted to authorized CEDIA storage.
5. A sanitized aggregate export with documented derivation and independently reproducible counts/metrics. No ECG signals, patient/record identifiers or raw clinical text should be placed in the public repository.

Until those artifacts are supplied, preserve the AF metrics only as CEDIA-reported summaries, keep quarantine unassessed, and do not alter historical thresholds or predictions.
