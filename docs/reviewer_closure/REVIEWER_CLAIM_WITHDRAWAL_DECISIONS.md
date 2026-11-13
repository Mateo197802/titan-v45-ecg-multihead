# Reviewer Claim Withdrawal Decisions

**Decision aid only; no manuscript claim has been edited.** The proposed dispositions below are limited to evidence currently present in PR #3 and the linked historical-evidence audit. Author approval is required before manuscript changes.

| Claim or phrase to audit | Proposed disposition | Evidence boundary / reason |
| --- | --- | --- |
| “Independent external validation” or “fully independent test” for the historical model | **Withdraw or narrow.** | V3F/V3AG full pretraining and fine-tuning manifests, patient maps and exact checkpoint-to-job chains are incomplete. SPH is a later transfer evaluation, but source independence from every historical training stage is not certified. |
| “Clinical validation,” clinical diagnosis, safe deployment or clinical utility | **Withdraw.** | SPH targets are coded ECG statements, not adjudicated clinical outcomes. No prospective outcome, reader-performance or deployment study was measured. |
| AF incident, new-onset or first-diagnosed disease | **Narrow to AF statement presence on that ECG.** | The available target is a code on one tracing, not longitudinal onset or first diagnosis. |
| Full end-to-end performance for all incoming patients/classes | **Withdraw unless a complete compatible denominator and routing ledger is supplied.** | Historical parent population, exclusions, all-class ontology, linked quarantine policy and all-input ledger are unavailable. SPH scores all source ECG under three profiles but does not reconstruct the June flow. |
| Primary6 95.19% accuracy / 80.09% macro-F1 as untouched external performance | **Narrow to development/model-selection evidence.** | Retained job 17314 contains an epoch sweep; 17315 names the V3H accepted/balanced manifest and the matching epoch-8 result. Exact 17314 script/manifest binding is missing, but evidence strongly supports V3H's role in selection. |
| Primary8 90.61% accuracy / 76.14% macro-F1 as a passed final model | **Withdraw gate-passing language; retain only as candidate result with stated metrics.** | It does not meet the project's full Primary8 gate. The later SPH endpoint transfer is not a substitute for that gate or for unsupported classes. |
| Primary4 80.23% mean binary-panel accuracy / 79.35% binary-panel macro-F1 as broad pathology validation | **Narrow to selected high-confidence panel evidence and project decision.** | It is 962 binary panel observations from 733 ECG and 676 linked patients. It is not all-input prevalence or independent validation. SPH statement endpoints show low PPV/F1 for rare statement targets and must be reported separately. |
| “No patient leakage” / certified patient-disjoint training and test | **Withdraw as a certified statement.** | Official fold membership verifies a selected mapping, not the actual manifests consumed by each historical job. Missing manifest-to-checkpoint edges mean `PATIENT_ISOLATION_NOT_CERTIFIED`; this is not the same as proving leakage occurred. |
| All 14 rhythm / seven pathology outputs are trained and validated | **Narrow to declared architecture/output contract.** | Output width and emitted scores do not prove class-specific supervision, support, calibration or measured performance. |
| ALMI, ILMI and LAE are validated predictions | **Withdraw performance claims; describe as auxiliary emitted scores only where relevant.** | Historical loss masks, positive/negative supports and checkpoint-linked validation are not established. |
| `Other arrhythmia` / `Other pathology` is available | **Withdraw unless a distinct trained, calibrated and evaluated class is evidenced.** | Neither NSR nor an empty set/fallback is `Other`. Current profile contracts do not establish a validated Other class. |
| A threshold fallback is quarantine, abstention or human review | **Withdraw.** | P8's forced top-1 is an algorithmic fallback. P6/P4 empty sets are not quarantine. No frozen uncertainty score/policy/ledger or measured human referral, human review or action survives. |
| Historical quarantine reduced errors or improved performance | **Withdraw; report not assessed.** | No checkpoint-linked pre/post ledger, policy, uncertainty scores, outcomes or valid denominator. The rate is undefined, not 0%. |
| Reproducibility of the exact historical loader | **Withdraw exact-reproduction wording.** | No candidate matches the expected 36,271-byte loader SHA-256. P4 decision agreement does not pass numerical tolerance; reconstructed processing remains labeled reconstructed. |
| Complete Optuna history or trial-to-checkpoint provenance | **Withdraw unless PR #4 evidence adds an original DB and binding.** | Partial trial exports and failed-job traces do not establish the full SQLite study or which trial produced released weights. Keep PR #4 separate. |
| A10 SHA table fully verifies every announced artifact | **Narrow to measured physical checkpoint artifacts.** | Five checkpoint file digests are verified separately; unavailable Optuna/prediction artifacts must remain explicitly unavailable rather than receive substitute hashes. Coordinate wording with PR #4. |
| Figure 2 proves every depicted workflow was executed | **Narrow to schematic/provenance only.** | Archive/file hash and dimension evidence identify the supplied visual; they do not prove authorship, rights, or execution of all depicted operations. |
| Grad-CAM/attention is clinical evidence or explanation validated by readers | **Withdraw strong clinical-explanation language.** | Existing evidence is not a reader study or clinical explanation validation. Retain only a narrowly described visualization analysis if source images, methods and claims are supported. |
| Model improves reader performance or human-in-the-loop outcomes | **Withdraw.** | No reader study or measured human referral/action/outcome was found in the current evidence set. |
| “All comments are resolved” or “ready for resubmission” | **Do not claim.** | 21 reviewer items still require manuscript edits, 12 are partially addressed, and 3 are not satisfied in the current source matrix. Editorial acceptance, authors' approval, external scope and final package assembly remain separate gates. |

## Decision rules for final revision

- Retain a claim only if its denominator, source, metric and evidence chain match the actual experiment.
- Narrow a claim when the measured evidence is real but supports fewer settings or endpoints than the current wording.
- Withdraw a claim when it requires an unperformed reader, clinical, all-input or independent-external experiment.
- Keep unresolved facts explicitly unresolved; do not turn missing records into zero, negatives or proof of no leakage.
- Apply changes only after author approval and line-by-line review of the final manuscript and supplement. The editor's response is unknown until received.

The [36-comment action plan](REVIEWER_36_CLOSURE_ACTION_PLAN.md), [reproducibility gaps](REVIEWER_REPRODUCIBILITY_GAPS.md), [code/formula audit](REVIEWER_CODE_AND_FORMULA_AUDIT.md) and [figure/table proposals](REVIEWER_FIGURE_TABLE_CORRECTIONS.md) are the supporting author-review materials.
