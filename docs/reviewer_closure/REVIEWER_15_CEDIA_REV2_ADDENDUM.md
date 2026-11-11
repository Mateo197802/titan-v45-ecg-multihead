# CEDIA REV2 Update: 15 Technical Reviewer Items

As of 2026-11-10. This is a supplemental evidence update, not a replacement for the authoritative 48-item matrix or the separate 12-item audit register. The machine-readable item-by-item record is [`REVIEWER_15_CEDIA_REV2_ADDENDUM.json`](REVIEWER_15_CEDIA_REV2_ADDENDUM.json); source claims and archive checks are in [`HISTORICAL_RECOVERY_CANONICAL_INDEX.md`](HISTORICAL_RECOVERY_CANONICAL_INDEX.md).

## Disposition

The CEDIA REV2 outer ZIP and both nested exports passed byte-integrity checks. Its inventories and receipts add bounded historical context, but the original CEDIA source bytes for reported job inputs and outputs were not transferred or independently hashed here. No new evidence satisfies a previously unmet scientific subrequirement in the 15 technical reviewer items.

| Count | Before-to-after result |
|---|---|
| Technical reviewer items | 15 reviewed; 0 technical-status changes; 0 satisfaction changes; 0 coverage-point changes |
| Reviewer disposition | 12 partially addressed; 3 not satisfied |
| Editorial-only reviewer items | 21 unchanged |
| Internal project audits | 12; statuses unchanged and kept separate from reviewer comments |
| Manuscript / editor response | Not edited |

Coverage percentages below are inherited, rubric-based estimates from the preceding update, not acceptance probabilities or measures of reviewer satisfaction. The newly supplied receipt did not increase them.

## Item-by-item update

| ID | Technical status; satisfaction; coverage | CEDIA REV2 evidence and what it supports | Still not demonstrated |
|---|---|---|---|
| R1-1 | `EXPERIMENT_COMPLETED_WITH_LIMITATIONS`; partial; 50.0% | Reports zero exact `(source, record)` overlap in four May cache train/validation pairs and matching hashes for the two released backbones. Corroboration only. | Patient/signal independence, June job consumption, full pretraining lineage, untouched cohort. |
| R1-2 | `EXPERIMENT_COMPLETED_WITH_LIMITATIONS`; partial; 33.3% | Reports W/Z/AC/AD/AE/AF job states and two AF aggregate summaries with 23 handoff rows and denied gate. | Complete June population, exclusions, ECG-level transitions, quarantine denominator/rate, pre/post performance. |
| R1-3 | `VERIFIED_WITH_LIMITATIONS`; partial; 50.0% | No new clinical AF reference or longitudinal adjudication. | Clinical correctness, onset, incidence or first diagnosis. |
| R1-4 | `VERIFIED_WITH_LIMITATIONS`; partial; 25.0% | Reports May 41M jobs 13169/13172/13181 failed and includes launcher/preflight/test copies. | Original SQLite generations, complete trial history, selected configuration and trial-to-checkpoint link; A10 correction remains governed by PR #4. |
| R2-general | `NEW_EXPERIMENT_REQUIRED`; not satisfied; 50.0% | No compatible all-class reference population or validated `Other` output. | Complete ontology, `Other` performance and all-input utility. |
| R2-2b | `ACTIVE_RECOVERY_REQUIRED`; partial; 50.0% | No new source archive, creator record, rights grant or proof of depicted operations. | Creator/rightsholder and execution provenance. |
| R2-3a | `EVIDENCE_CEILING_REACHED`; partial; 50.0% | Four May cache pairs have reported zero exact source-record key overlap. | Patient-level and waveform separation; exact manifests consumed by released-checkpoint jobs. |
| R2-3c | `VERIFIED_WITH_LIMITATIONS`; partial; 66.7% | May cache summary reports positive-row counts for ALMI/ILMI/LAE; `PATHOLOGY_10_V2` duplicates `PATHOLOGY_10` bytes. | Effective loss masks/support, released-checkpoint supervision and class-specific evaluation. |
| R2-3d | `EVIDENCE_CEILING_REACHED`; not satisfied; 66.7% | Cache-level positive-label counts only. | Negative support, active masks, checkpoint/job linkage and evaluated performance. |
| R2-3e | `VERIFIED_WITH_LIMITATIONS`; partial; 50.0% | AF receipt reports an aggregate 23-row handoff count. | Per-record historical role, actual human review, and pre/post transitions. |
| R2-3f | `EVIDENCE_CEILING_REACHED`; partial; 25.0% | Reaffirms a 32,051-byte loader candidate differs from the expected 36,271-byte LF file/hash. | Exact original loader, morphology parity and strict replay equivalence; P4 residual remains `0.0006194115` vs `1e-5`. |
| R2-4a | `VERIFIED_WITH_LIMITATIONS`; partial; 75.0% | Cache-key checks and reported backbone hashes provide limited corroboration. | Untouched cohort or complete overlap checks across backbone pretraining/fine-tuning sources. |
| R2-4e | `EXPERIMENT_COMPLETED_WITH_LIMITATIONS`; partial; 50.0% | Two AF summaries report aggregate profile metrics and 23 handoff rows; gate is denied. | Per-record routing, checkpoint-linked inputs, complete no-label route, and equivalence of handoff with quarantine. |
| R2-4k | `EVIDENCE_CEILING_REACHED`; not satisfied; 0.0% | Reported AE digests match across summaries; 23 AF handoff rows; `valid_for_gate=0`. | Original policy/manifest bytes, score/threshold, full eligible denominator and pre/post ledger. Quarantine remains `NOT_ASSESSED`, not zero. |
| R2-5 | `VERIFIED_WITH_LIMITATIONS`; partial; 50.0% | No beat annotations, timing reference or episode outcomes. | Beat localization or episode-level performance. |

## Internal audits

| ID | Status retained | CEDIA REV2 impact |
|---|---|---|
| A-01 | `VERIFIED_COMPLETE` | Existing P4 units unchanged: 962 panel observations / 733 ECG / 676 linked patients. |
| A-02 | `VERIFIED_WITH_LIMITATIONS` | Cache-key checks only; no new signal-duplicate or public-table source reconciliation. |
| A-03 | `VERIFIED_WITH_LIMITATIONS` | AF aggregate metrics are reported by CEDIA, not independently recomputed from row predictions. |
| A-04 | `EVIDENCE_CEILING_REACHED` | Retry launcher exists; executed script, calibration inputs and linked outputs are unverified. |
| A-05 | `VERIFIED_COMPLETE` | No new tensor-architecture evidence. |
| A-06 | `EVIDENCE_CEILING_REACHED` | Launcher copies/failure states corroborated; no 41M database or trial-checkpoint edge. |
| A-07 | `VERIFIED_WITH_LIMITATIONS` | No new DOI or repository-availability evidence. |
| A-08 | `MANUSCRIPT_ONLY_PENDING` | No supplement assembled. |
| A-09 | `MANUSCRIPT_ONLY_PENDING` | No new bibliography/DOI evidence. |
| A-10 | `ACTIVE_RECOVERY_REQUIRED` | Expanded inventory does not establish complete provenance, rights or redistribution authorization. |
| A-11 | `NEW_EXPERIMENT_REQUIRED` | No new Grad-CAM/reader evidence. |
| A-12 | `NEW_EXPERIMENT_REQUIRED` | No reader records or approvals. |

## Guardrails

- `23` AF handoff rows are not the total eligible ECG population, a quarantine denominator, or a quarantine rate.
- The reported 1,895 rhythm and 2,105 pathology rows are evaluated-row counts, not full-input denominators. Reported metrics were not recalculated from per-record predictions.
- A completed SLURM state or submit-line digest does not prove exact script/input consumption or checkpoint production.
- May cache-key disjointness does not certify patient or waveform independence and does not establish June V4.5 checkpoint inputs.
- May V4 quarantine, V4.5 June quarantine, transfer performance and independent validation remain distinct scopes.
- No recovered code was executed, no new inference/training or CEDIA search was run, and PR #4/#5 and the manuscript were not modified.
