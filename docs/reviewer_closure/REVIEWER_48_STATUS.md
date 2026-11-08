# Reviewer and audit disposition

This is a technical index, not a response to reviewers or proof of editorial
acceptance. SPH scoring and statement-level aggregation have been performed;
their source-independence limitations remain. The submitted manuscript is unchanged.
The descriptions below are short project paraphrases, not reviewer quotations.
The [commit and job index](EVIDENCE_COMMITS.md) records the public evidence chain.

`MANUSCRIPT_UPDATE_ONLY` means editing or assembly remains, not that it has been
incorporated. `VERIFIED_WITH_LIMITATIONS` identifies evidence that does not
support the original claim in full. `CLAIM_WITHDRAWAL_REQUIRED` means the claim
needs removal or restriction; that is not equivalent to the requested study.
`EXPERIMENT_COMPLETED` describes the executed SPH analysis, not certified
historical independence or reviewer acceptance.

| ID | Concern | Disposition | Evidence / remaining action |
| --- | --- | --- | --- |
| R1-1 | Independent external validation | EXPERIMENT_COMPLETED | [SPH results](../../outputs/results/external_sph/sph_aggregate_normalized_32669.json), jobs 32668/32669/32672; 25,770 ECG, but historical independence is not certified. |
| R1-2 | Population and flow denominator | VERIFIED_WITH_LIMITATIONS | [SPH full-source flow](../../outputs/results/external_sph/sph_aggregate_normalized_32669.json) covers 25,770 ECG; [historical selected-record audit](../frozen-waveform-audit.md) cannot recover the original preselection population. |
| R1-3 | AF incidence versus ECG statement | VERIFIED_WITH_LIMITATIONS | [AF reference contract](../af-reference-contract.md); no incident-AF claim. |
| R1-4 | Invalid artifact hashes | VERIFIED_WITH_LIMITATIONS | [Hash correction](../hash-correction-20261028.md); separate PR #4, missing historical artifacts remain unavailable. |
| R2-general | Excluded classes and Other | CLAIM_WITHDRAWAL_REQUIRED | SPH covers 14 compatible endpoints; [data dispositions](../revision-data-dispositions.md) show Other is not a validated output. |
| R2-1a | Define P6 and P4 in abstract | MANUSCRIPT_UPDATE_ONLY | Define terms in the future manuscript. |
| R2-1b | Define abbreviations on first use | MANUSCRIPT_UPDATE_ONLY | Check first occurrence in the future manuscript. |
| R2-2a | Introduction references | MANUSCRIPT_UPDATE_ONLY | Align citations with the final scope. |
| R2-2b | Origin and purpose of figures 1 and 2 | MANUSCRIPT_UPDATE_ONLY | Verify figure provenance and descriptions. |
| R2-2c | Comparator selection | MANUSCRIPT_UPDATE_ONLY | Reassess comparison table against final scope. |
| R2-2d | Unreported parameters and comparability | MANUSCRIPT_UPDATE_ONLY | Mark missing parameters and avoid unequal comparisons. |
| R2-2e | SCP and abbreviations | MANUSCRIPT_UPDATE_ONLY | Define terms and verify usage. |
| R2-2f | Introduction table placement | MANUSCRIPT_UPDATE_ONLY | Resolve placement and claims in the future manuscript. |
| R2-3a | Datasets and splits | VERIFIED_WITH_LIMITATIONS | [Recovery status](../recovery-status-20261029.md); historical patient isolation not established. |
| R2-3b | Design versus evaluation | MANUSCRIPT_UPDATE_ONLY | Distinguish design, historical development and reconstructed evaluation. |
| R2-3c | Auxiliary classes and training | VERIFIED_WITH_LIMITATIONS | [Feature contract](../recovered-feature-contract.md); outputs alone do not prove supervision. |
| R2-3d | ALMI, ILMI and LAE training | VERIFIED_WITH_LIMITATIONS | [Data dispositions](../revision-data-dispositions.md); checkpoint-linked supervision remains unverified. |
| R2-3e | Role definitions | VERIFIED_WITH_LIMITATIONS | [Waveform audit](../frozen-waveform-audit.md); distinguish code roles from historical routing. |
| R2-3f | Morphology and feature architecture | VERIFIED_WITH_LIMITATIONS | [Replay diagnostics](../replay-residual-diagnostics.md); exact historical loader unavailable. |
| R2-3g | Brier score in methods | MANUSCRIPT_UPDATE_ONLY | Add definition and remove unsupported numerical methods claim. |
| R2-3h | Accuracy equations and tasks | MANUSCRIPT_UPDATE_ONLY | Define rhythm and pathology endpoints separately. |
| R2-4a | External-development terminology | VERIFIED_WITH_LIMITATIONS | [Evidence status](../evidence-status.md); do not call selected development evidence independent. |
| R2-4b | Figure cross-reference | MANUSCRIPT_UPDATE_ONLY | Correct figure reference. |
| R2-4c | Overstated F1 interpretation | MANUSCRIPT_UPDATE_ONLY | Use measured values and qualified language. |
| R2-4d | Figure metrics versus confidence intervals | MANUSCRIPT_UPDATE_ONLY | Describe what is actually plotted. |
| R2-4e | No threshold crossed | VERIFIED_WITH_LIMITATIONS | [Waveform audit](../frozen-waveform-audit.md); P8 fallback is not a full-population evaluation. |
| R2-4f | Confusion matrix presentation | MANUSCRIPT_UPDATE_ONLY | Harmonize labels and denominators. |
| R2-4g | Duplicated figures | MANUSCRIPT_UPDATE_ONLY | Reconcile figures against their source data. |
| R2-4h | ROC and PR tracing definition | MANUSCRIPT_UPDATE_ONLY | Define plotted units and derivation. |
| R2-4i | AUROC wording | MANUSCRIPT_UPDATE_ONLY | Qualify the interpretation of the reported value. |
| R2-4j | Frequency versus accuracy plot | MANUSCRIPT_UPDATE_ONLY | Verify axes, bins and denominators. |
| R2-4k | Quarantine and pre/post rates | CLAIM_WITHDRAWAL_REQUIRED | [Waveform audit](../frozen-waveform-audit.md); historical policy and ledger unavailable; SPH quarantine is not assessed. |
| R2-4l | Rhythm top-1 | MANUSCRIPT_UPDATE_ONLY | Define the decision and denominator. |
| R2-4m | Figure readability | MANUSCRIPT_UPDATE_ONLY | Final layout and rendering remain pending. |
| R2-5 | PVC record versus beat level | VERIFIED_WITH_LIMITATIONS | Report ECG-statement scope, not beat-detection performance. |
| R2-6 | Distortion and citation claim | MANUSCRIPT_UPDATE_ONLY | Remove unsupported general claim and verify citation. |
| A-01 | P4 panel versus unique ECG count | VERIFIED_WITH_LIMITATIONS | [Data dispositions](../revision-data-dispositions.md); preserve 962 panel rows and 733 distinct record keys. |
| A-02 | Source distribution and aliases | VERIFIED_WITH_LIMITATIONS | [Source evidence](../revision-evidence-20261029.md); aliases do not prove independence. |
| A-03 | Per-class metric inconsistencies | MANUSCRIPT_UPDATE_ONLY | Use audited source tables and verify the final manuscript values. |
| A-04 | Thresholds and calibration isolation | VERIFIED_WITH_LIMITATIONS | [Data dispositions](../revision-data-dispositions.md); patient isolation remains unverified. |
| A-05 | Backbone relationships | MANUSCRIPT_UPDATE_ONLY | Describe shared V3F and separate V3AG accurately. |
| A-06 | Optuna history and quarantine | CLAIM_WITHDRAWAL_REQUIRED | Separate PR #4; remove unsupported historical optimization claims: original study database and promotion linkage are unavailable. |
| A-07 | Data availability URL | MANUSCRIPT_UPDATE_ONLY | Cite the verified final artifact and restricted inputs. |
| A-08 | Missing supplement CSVs | MANUSCRIPT_UPDATE_ONLY | Inventory only files actually included in the final supplement. |
| A-09 | Incorrect DOI | MANUSCRIPT_UPDATE_ONLY | Verify replacement reference in the final bibliography. |
| A-10 | Mixed archive provenance and rights | VERIFIED_WITH_LIMITATIONS | [Licenses](../../data/licenses/README.md); mixed archive remains on HOLD. |
| A-11 | MC/Grad-CAM clinical claims | CLAIM_WITHDRAWAL_REQUIRED | No clinical adjudication established; remove unsupported claims. |
| A-12 | Reader study | CLAIM_WITHDRAWAL_REQUIRED | No reader study established; remove unsupported claims. |

Do not infer that an editorial disposition or a withdrawn claim satisfies a
requested experiment. Authors must review the scientific scope and final text;
the editor decides whether the submitted revision addresses the comments.
