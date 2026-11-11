# Technical Closure Execution: 15 Reviewer Items

**As of:** 2026-11-11<br>
**Baseline:** PR #3 branch at `0a32a57a32b50c421fc05323454507dba4265bb0`<br>
**Manuscript:** `SIN_EDITAR`. No submission PDF, response letter, historical checkpoint, prediction table or threshold was modified.

This is an execution addendum to the [48-item source matrix](REVIEWER_48_DETAILED.md), not a replacement. It covers the 15 technically substantive reviewer items. The other 21 reviewer items remain editorial-only in the existing [36-comment action plan](REVIEWER_36_CLOSURE_ACTION_PLAN.md); the 12 `A-*` records remain project audits, not peer-review comments. Reviewer satisfaction and technical evidence status remain separate.

The execution baseline is commit `0a32a57`. The matrix bytes used for the recorded baseline digest are independently verified at matrix commit `01beb7a` (SHA-256 `2586de1a1212dd898a9c4201e39e6dda18b59c11e74d7369da02bb1ec2290b52`); those are distinct commit roles because the matrix changed after the execution baseline. A later evidence-only update adds the CEDIA cleanup-manifest receipt to A-06; the current matrix SHA-256 is recorded separately in the execution JSON. No technical status or reviewer-satisfaction label changed.

**Recovery round 2:** the 2026-11-10 directed package has been validated and reconciled in [`NEW_RECOVERY_EVIDENCE_INTEGRATION.md`](NEW_RECOVERY_EVIDENCE_INTEGRATION.md). It adds authenticated source bytes for S4/S5/U plans and bounded SLURM metadata, but does not complete an original reviewer subrequirement. The 15-item update and its explicit coverage rubric are in [`REVIEWER_15_EVIDENCE_UPDATE.md`](REVIEWER_15_EVIDENCE_UPDATE.md); the source/job/checkpoint graph is in [`HISTORICAL_PROVENANCE_GRAPH.md`](HISTORICAL_PROVENANCE_GRAPH.md). Technical and reviewer-satisfaction states remain unchanged.

**CEDIA REV2 follow-up:** the newer CEDIA export is reconciled in [`HISTORICAL_RECOVERY_CANONICAL_INDEX.md`](HISTORICAL_RECOVERY_CANONICAL_INDEX.md) and [`REVIEWER_15_CEDIA_REV2_ADDENDUM.md`](REVIEWER_15_CEDIA_REV2_ADDENDUM.md). It adds reported job/AF summaries and bounded cache-key checks, not original policy/ledger bytes, job-consumed manifests or independent patient/signal certification. Its item states and coverage values are preserved as the previous-round record.

**CEDIA REV3-REV6 integration (2026-11-11):** all four cumulative packages passed the supplied-byte audit. The [recovery report](CEDIA_FINAL_RECOVERY_REPORT.md), [audit receipt](receipts/CEDIA_REV3_REV6_PACKAGE_AUDIT_2026-11-11.json), and [source-copy authentication table](CEDIA_SOURCE_CODE_AUTHENTICATION.md) record hashes and boundaries. Zero new original V4.5 artifacts are newly linked to both a producing job and released checkpoint. Static source evidence adds 0.5 credit to one subrequirement each for R2-3c and R2-3d; reviewer-satisfaction labels and overall item statuses do not change. Coverage is now 19.5/40 = 48.75% (+2.5 pp). R2-3f's possible P4 512/192 report-writer mismatch is not job-linked and does not explain P6/P8; it earns no added credit. No change to the manuscript, historical metrics, weights or thresholds was made.

## Result

No targeted reviewer-satisfaction label changed: 12 items remain `PARTIALLY_ADDRESSED`, and R2-general, R2-3d and R2-4k remain `NOT_SATISFIED`. The new checks verify two static-source subrequirements, but do not turn selected development results into independent validation, recover missing historical lineage, or satisfy a missing experiment. Coverage is a count of rubric subrequirements, not a proxy for scientific completion.

| ID | Bounded evidence now verified or retained | What remains open |
| --- | --- | --- |
| R1-1 | Full-source SPH aggregate reconciles: 25,770 ECG, 24,666 source patients, three profiles, 14 compatible endpoints. | Full training-source independence, exact P6 sweep manifest, adjudicated validation and any untouched independent cohort. |
| R1-2 | SPH full denominator and selected profile units remain explicit. | Original June parent population, exclusions, original-prevalence all-class flow and authentic quarantine ledger. |
| R1-3 | Fresh AF flag/code audit: P6 1,643 and P8 2,193 rows, 390 positive per overlapping profile, zero mismatches or unresolved rows. | Clinical adjudication and longitudinal incident/first-diagnosis truth. |
| R1-4 | The five-checkpoint A10 correction is documented in separate PR #4 evidence. | Original Optuna database and generic prediction artifact; no one-to-one recovery of every A10 row. |
| R2-general | The 14-rhythm/seven-pathology global output contract and 14 compatible SPH endpoints are verified. | Validated `Other`, a complete compatible ontology and all-class performance. |
| R2-2b | Figure archive identity and recorded purpose are documented. | Creator, rights and proof that all depicted process steps occurred. |
| R2-3a | Selected cohort and P4 panel/patient units are verified; selected P4 fold mapping is bounded. | Exact manifests consumed by historical jobs and complete patient isolation across stages. |
| R2-3c | P6/P8 class contracts and NSR interpretation are verified. | Checkpoint-linked supervision and performance of secondary rhythm outputs. |
| R2-3d | ALMI/ILMI/LAE are declared and were emitted by reconstructed P4 inference. | Historical masks, positive/negative supports, calibration and performance. |
| R2-3e | Current reconstructed code and selected transitions are inspectable. | Authentic historical role ledger and evidence of actual human review/action. |
| R2-3f | Candidate morphology and replay behavior are documented; P4 strict numerical replay still fails. | Exact original loader, historical arrow semantics and explanation of stale specialist width metadata. |
| R2-4a | Selected development and later SPH source-transfer populations are distinguished. | Full historical use/selection chain and complete model-source independence. |
| R2-4e | SPH empty sets/fallbacks and selected replay are separately counted. | These are not quarantine, `Other` or human-review outcomes; original all-input routing remains unknown. |
| R2-4k | Quarantine remains explicitly `not assessed`, not zero. | Policy, scores, denominator, pre/post outcomes and authentic historical ledger. |
| R2-5 | PVC reference is ECG-statement-level, with 1,067 positive and 24,703 negative SPH statements. | Beat annotations, localization, temporal matching and beat-level performance. |

## Checks Executed

1. `audit_af_reference_contract.py` reran from the saved P6/P8 prediction tables. Its aggregate-only output and full input-file hashes are in [AF_REFERENCE_RECHECK_2026-11-10.json](receipts/AF_REFERENCE_RECHECK_2026-11-10.json). The audit confirms agreement between two retained fields; it does not validate the clinical diagnosis.
2. `verify_release_evidence.py` recomputed canonical release summaries from saved predictions and manifests. See [RELEASE_METRICS_RECHECK_2026-11-10.json](receipts/RELEASE_METRICS_RECHECK_2026-11-10.json). This is a metric/manifest verification, not fresh ECG inference or training replay.
3. `validate_sph_aggregate.py` checked the frozen protocol against the committed aggregate: 25,770 source records, three profiles and 14 endpoints. See [SPH_AGGREGATE_VALIDATION_2026-11-10.json](receipts/SPH_AGGREGATE_VALIDATION_2026-11-10.json). This validator checks arithmetic and protocol reconciliation, not the waveform inference itself.
4. Existing selected-waveform cascade outputs were read and SHA-256 fingerprinted, not rerun. Their selected-population scope, score residuals, fallback counts and `quarantine_not_assessed` states remain explicit.

Commands, artifact hashes, output hashes and limits are recorded in [reproducibility verification receipts](REPRODUCIBILITY_VERIFICATION_RECEIPTS.md). All receipts are aggregate-only; no ECG or patient identifiers are present.

## Individual Dispositions

### R1-1

**Request:** Distinguish an external-development holdout from independent validation and report source/split coverage or evaluate a genuinely independent cohort.<br>
**Coverage:** SPH's full transfer aggregate is internally reconciled. The bounded signature screen found no candidates against the retained selected-source packages, but full V3F/V3AG training sources are unavailable. Jobs 17314/17315 support V3H selection exposure; job 17314's exact manifest edge is missing.<br>
**Conclusion:** Partial transfer evidence only; full historical independence is **not certified**. A new untouched cohort is still a separate experiment.

### R1-2

**Request:** Complete workflow denominator, classes, quarantine, errors inside/outside quarantine and predictive values at the relevant prevalence.<br>
**Coverage:** SPH's later source denominator is verified; selected development counts and units are separately documented. Neither recovers the June parent cohort.<br>
**Conclusion:** The original end-to-end workflow remains incomplete. Historical quarantine is **not assessed**, not zero. The SPH transfer is not an independent clinical validation.

### R1-3

**Request:** Explain source-level AF reference creation/conflict handling and avoid incident/first-diagnosed claims without longitudinal evidence.<br>
**Coverage:** The fresh audit reconciles AF flags with code `164889003` in both saved profiles. The AF/NSR code co-occurrence is retained as observed, not adjudicated. P6 is nested in P8.<br>
**Conclusion:** Saved ECG-reference consistency is verified; clinical adjudication and longitudinal truth are not.

### R1-4

**Request:** Replace unsupported A10 hashes and provide a verifiable artifact route.<br>
**Coverage:** The five measured checkpoint hashes/sizes and correction route belong to PR #4. This PR #3 pass did not modify PR #4 or re-hash its physical assets.<br>
**Conclusion:** A10 is partially corrected; do not treat the original Optuna database or generic prediction file as recovered.

### R2-general

**Request:** Represent excluded classes as `Other` or otherwise provide realistic all-class assessment.<br>
**Coverage:** The global contract has 14 rhythm and seven pathology outputs. P6/P8/P4 are six/eight/four-class operational profiles. SPH has 14 compatible endpoint comparisons; NSR is normal sinus rhythm, not `Other`.<br>
**Conclusion:** Not satisfied for validated `Other` or complete all-class performance. This requires a justified ontology and a new compatible training/evaluation design if retained.

### R2-2b

**Request:** State the purpose and source of Figures 1 and 2.<br>
**Coverage:** The source archive and image identities/purpose are recorded. Hash agreement does not establish creator, rights or execution truth.<br>
**Conclusion:** Partial; author/rightsholder confirmation remains necessary before the figures are retained.

### R2-3a

**Request:** Report databases, classes, split counts and ECG/patient units.<br>
**Coverage:** P6 is 1,643 ECG; P8 is 2,193 and contains P6; P4 is 962 panel observations across 733 ECG/676 linked patients. The selected P4 mapping is in official fold 10 and does not overlap official folds 1-9 in that mapping.<br>
**Conclusion:** Selected denominators are verified; historical job-consumed manifests and patient isolation are not. Status: `PATIENT_ISOLATION_NOT_CERTIFIED`. No leakage finding is made.

### R2-3c

**Request:** Explain primary/cascade/auxiliary rhythm labels and avoid calling NSR a rare arrhythmia.<br>
**Coverage:** Output order and current code paths are verified; SPH records 16,700 NSR P8 top-1 outputs. Training supports for secondary outputs are not linked to the released checkpoints.<br>
**Conclusion:** Contract and NSR interpretation are bounded; auxiliary supervision/performance remains unproven.

### R2-3d

**Request:** Clarify historical training/evaluation versus merely logged ALMI, ILMI and LAE.<br>
**Coverage:** They are declared as auxiliary outputs and emitted on 733 selected ECG by the reconstructed P4 run.<br>
**Conclusion:** Historical supervision and measured performance are not established; output emission is not proof of either.

### R2-3e

**Request:** Define `Role` and explain assignment.<br>
**Coverage:** Current primary/secondary behavior is inspectable; selected P8 fallback and status transitions are recorded. The runner explicitly has no frozen auxiliary action policy.<br>
**Conclusion:** Current implementation semantics are bounded. The historic per-record role ledger and human actions are absent.

### R2-3f

**Request:** Define ten morphology features and explain diagram arrows/connections.<br>
**Coverage:** A candidate ten-feature implementation is hash-pinned, not authenticated as the original loader. P4 replay decisions agree 962/962, but the maximum probability residual `0.0006194114685058594` exceeds the frozen `1e-5` criterion. The retained waveform report also records specialist hidden width `192` in metadata versus `512` in stored tensors; the current loader builds from tensor shape and strict-loads weights.<br>
**Conclusion:** Strict numerical equivalence and exact original preprocessing are **not verified**. Neither the residual nor metadata mismatch is corrected by changing a tolerance or relabeling the candidate.

### R2-4a

**Request:** Define the external-development package and use accurate test terminology.<br>
**Coverage:** Selected P6/P8/P4 evidence is separated from SPH transfer. The SPH signature screen is bounded to retained sources and cannot cover missing pretraining data.<br>
**Conclusion:** Terminology is technically clear in the evidence package; historical usage and full independence remain limited. Manuscript edits have not been made.

### R2-4e

**Request:** Explain no-threshold behavior and counts.<br>
**Coverage:** In SPH: P6 has 16,785 empty threshold sets; P4 8,343; P8 has 801 forced top-1 fallbacks. The selected waveform replay has 58 P8 fallbacks.<br>
**Conclusion:** These software behaviors/counts are verified within those populations; none is quarantine, `Other`, abstention or human review.

### R2-4k

**Request:** Define quarantine rate and pre/post accuracy.<br>
**Coverage:** No authentic historical policy, uncertainty-score input, ledger or denominator is linked to the released checkpoints. SPH and selected replay store quarantine as unassessed.<br>
**Conclusion:** Not satisfied. A historical rate is not calculable; a prospective workflow would be a new study.

### R2-5

**Request:** Separate ECG-level PVC classification from beat-level detection.<br>
**Coverage:** The SPH endpoint is code-60 ECG-statement presence/absence; its denominator is 1,067/24,703. There is no beat annotation or temporal matching protocol.<br>
**Conclusion:** Record-level statement evaluation only; beat-level sensitivity/localization remains unmeasured.

## Human and New-Study Boundaries

No human decision is required to interpret the software checks above. Custodian evidence is needed only if an exact missing historical artifact or rights record is claimed to exist. Authors must approve scientific scope, attribution/rights, the manuscript changes and any new protocol; an editor's acceptance cannot be inferred. A truly independent validation, all-class `Other` assessment, beat-labeled PVC study or quarantine-effectiveness study must be performed as a separately declared experiment if those claims are retained.

The [checkpoint-manifest-job edge audit](CHECKPOINT_MANIFEST_JOB_EDGE_VERIFICATION.md), [cohort independence audit](GENERALIZATION_AND_COHORT_INDEPENDENCE_AUDIT.md), [class and routing audit](FULL_CLASS_COVERAGE_AND_ROUTING_AUDIT.md) and [quarantine disposition](QUARANTINE_HISTORICAL_VS_PROSPECTIVE.md) contain the supporting technical detail.

## CEDIA REV3–REV6 and targeted follow-up (2026-11-11)

The four cumulative packages passed the bounded static validation recorded in [`CEDIA_REV3_REV6_PACKAGE_AUDIT_2026-11-11.json`](receipts/CEDIA_REV3_REV6_PACKAGE_AUDIT_2026-11-11.json). REV6 adds static source evidence for a generic 14-rhythm/7-pathology loss route, a separate P8/P4 fine-tuning route, and a possible P4-only 512/192 report-writer mismatch; none is linked to the published checkpoint-producing job. It also corroborates a `parent_checkpoint` path string, not file identity or job read/write hashes. These source findings account only for the existing +2.5 pp partial coverage increase on R2-3c/R2-3d; they do not change reviewer satisfaction.

A live, read-only CEDIA filename/metadata follow-up found no matching target in the known V4.5 project root or filename-matching candidate archives/bundles under the named backup directories. The bounded receipt is [`CEDIA_TARGETED_RECOVERY_SEARCH_2026-11-11.json`](receipts/CEDIA_TARGETED_RECOVERY_SEARCH_2026-11-11.json). This adds no subrequirement points and does not establish global nonexistence. Consequently, all 15 reviewer statuses, all 40 subrequirement scores other than the prior static-code gains, and the 21 editorial-only items remain unchanged. PR #4's separate update is commit `1d556ba5a58255b1eef97221da8107a9c8d120b0`; PR #5 was not touched.
