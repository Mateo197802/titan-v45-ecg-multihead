# Technical Reviewer Evidence Update: Recovery Round 2

As of 2026-11-10. The 15 IDs below are the technical reviewer items tracked in the existing execution register; the remaining 21 reviewer items are editorial-only, and the 12 A-items are project audits rather than additional reviewer comments. No item status or reviewer-satisfaction label changed in this round.

## Coverage rubric

For each existing subrequirement row, `VERIFIED_BOUNDED` receives 1 point. Explicitly bounded/indirect statuses listed in [`REVIEWER_15_EVIDENCE_UPDATE.json`](REVIEWER_15_EVIDENCE_UPDATE.json) receive 0.5. Unresolved, absent, failed, not-assessed or author-action statuses receive 0. The sum divided by the existing row count is the technical subrequirement coverage estimate. It is not a probability of acceptance and does not convert a partial response into a satisfied reviewer request.

The recovery package itself was inspected and integrity-checked 38/38 files (100% of this package). A percentage of the total documentary ceiling is not estimable: the universe of possible backups is unknown, and no general local or CEDIA search was performed in this task. Every item's requirement-coverage delta is 0 percentage points because no previously unmet reviewer subrequirement was completed.

## Item-by-item disposition

| ID | Technical coverage | Satisfaction | Round-2 contribution | Still required |
|---|---:|---|---|---|
| R1-1 | 50.0% | Partial | Corroborates that exact source/manifests and full independence remain unverified. | Complete model-source lineage and genuinely untouched validation if claimed. |
| R1-2 | 33.3% | Partial | Authenticated S4/U plan code and job states clarify that these are model/class decision gates, not the original all-input clinical flow. | June parent population, exclusions, full transitions and authentic quarantine ledger. |
| R1-3 | 50.0% | Partial | No new AF reference or longitudinal evidence. | Clinical adjudication/temporal reference or ECG-level wording only. |
| R1-4 | 25.0% | Partial | Bounded search again did not recover 41M SQLite bytes or complete trial export; known jobs remain failed. | Original database/history and trial-to-checkpoint chain; A10 remains in PR #4. |
| R2-general | 50.0% | Not satisfied | No validated `Other` reference or all-class evaluation. | Compatible ontology/labels and a new prespecified study if retained. |
| R2-2b | 50.0% | Partial | No new figure-source, creator, rights or process evidence. | Author/rightsholder confirmation and later editorial action. |
| R2-3a | 50.0% | Partial | Additional submission references, but no consumed manifests or patient maps. | Exact manifests, read receipts, patient grouping and exclusions per checkpoint. |
| R2-3c | 66.7% | Partial | S4/U viability code and S5 curation code are authenticated, but not linked to released heads. | Checkpoint-linked labels, masks, supports, losses and class metrics. |
| R2-3d | 66.7% | Not satisfied | No new ALMI/ILMI/LAE training/evaluation support. | Checkpoint-linked auxiliary supervision and metrics, or withdraw performance claim. |
| R2-3e | 50.0% | Partial | S5 proposes manual Flutter/PAC labeling/teacher review; this is not evidence a reviewer acted on V4.5 records. | Historical role policy/ledger or narrow later definition of `Role`. |
| R2-3f | 25.0% | Partial | The 192/512 source reading is corroborative, not a new source; loader identity and score equivalence remain open. | Exact loader hash and strict replay equivalence under frozen `1e-5` tolerance. |
| R2-4a | 75.0% | Partial | No change to SPH independence or historical development-use evidence. | Complete source lineage and separate independent validation if retained. |
| R2-4e | 50.0% | Partial | S4/U source is selection logic, not per-ECG no-threshold routing for released profiles. | Distinguish empty sets, fallback and quarantine; historical all-input behavior remains absent. |
| R2-4k | 0.0% | Not satisfied | New plan code/jobs reinforce that decision gates are not an ECG quarantine ledger; no ledger was recovered. | June V4.5 policy, scores, denominator, references and pre/post transitions. |
| R2-5 | 50.0% | Partial | No beat-annotated reference data. | Restrict to record-level claims or run a distinct beat-level study. |

**Counts:** 12/15 partially addressed; 3/15 not satisfied; 0 technical-status upgrades; 0 reviewer-satisfaction upgrades. The 21 editorial-only reviewer comments and 12 internal audit items are not reclassified by this addendum.

## Evidence boundaries

The strongest new contribution is authenticated source bytes for S4/S5/U plan code plus additional SLURM state and submission metadata. The plan-to-job links are supported but not cryptographically linked: the exact executed script digest and expected outputs are missing. Static inspection establishes what the recovered code says; it does not establish that the released checkpoint ran it or that its outputs were used.

See [`HISTORICAL_PROVENANCE_GRAPH.md`](HISTORICAL_PROVENANCE_GRAPH.md) for edge states, [`NEW_RECOVERY_EVIDENCE_INTEGRATION.md`](NEW_RECOVERY_EVIDENCE_INTEGRATION.md) for package validation and [`REMAINING_CRITICAL_ARTIFACTS.md`](REMAINING_CRITICAL_ARTIFACTS.md) for the exact missing evidence. The authoritative 48-item matrix is unchanged because this round does not justify a satisfaction/status transition.
