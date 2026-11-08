# Reviewer and audit disposition: pre-SPH baseline

This is a technical index, not a response to reviewers or proof of editorial
acceptance. SPH scoring was running when this baseline was prepared: no SPH
performance is attributed to any item. The submitted manuscript is unchanged.
The descriptions below are short project paraphrases, not reviewer quotations.

`EDITORIAL` means an edit or assembly remains; it does not imply that it has
been incorporated. `LIMITED` means the evidence cannot support the original
claim in full. `EXPERIMENT_PENDING` means no completed SPH result is claimed.

| ID | Concern | Baseline disposition | Evidence / remaining action |
| --- | --- | --- | --- |
| R1-1 | Independent external validation | EXPERIMENT_PENDING | [SPH protocol](../external_validation/sph_protocol.md); incomplete training lineage limits independence. |
| R1-2 | Population and flow denominator | LIMITED | [Selected-record waveform audit](../frozen-waveform-audit.md); historical preselection population unavailable. |
| R1-3 | AF incidence versus ECG statement | LIMITED | [AF reference contract](../af-reference-contract.md); no incident-AF claim. |
| R1-4 | Invalid artifact hashes | LIMITED | [Hash correction](../hash-correction-20261028.md); separate PR #4, missing historical artifacts remain unavailable. |
| R2-general | Excluded classes and Other | LIMITED | [Data dispositions](../revision-data-dispositions.md); Other is not a validated output. |
| R2-1a | Define P6 and P4 in abstract | EDITORIAL | Define terms in the future manuscript. |
| R2-1b | Define abbreviations on first use | EDITORIAL | Check first occurrence in the future manuscript. |
| R2-2a | Introduction references | EDITORIAL | Align citations with the final scope. |
| R2-2b | Origin and purpose of figures 1 and 2 | EDITORIAL | Verify figure provenance and descriptions. |
| R2-2c | Comparator selection | EDITORIAL | Reassess comparison table against final scope. |
| R2-2d | Unreported parameters and comparability | EDITORIAL | Mark missing parameters and avoid unequal comparisons. |
| R2-2e | SCP and abbreviations | EDITORIAL | Define terms and verify usage. |
| R2-2f | Introduction table placement | EDITORIAL | Resolve placement and claims in the future manuscript. |
| R2-3a | Datasets and splits | LIMITED | [Recovery status](../recovery-status-20261029.md); historical patient isolation not established. |
| R2-3b | Design versus evaluation | EDITORIAL | Distinguish design, historical development and reconstructed evaluation. |
| R2-3c | Auxiliary classes and training | LIMITED | [Feature contract](../recovered-feature-contract.md); outputs alone do not prove supervision. |
| R2-3d | ALMI, ILMI and LAE training | LIMITED | [Data dispositions](../revision-data-dispositions.md); checkpoint-linked supervision remains unverified. |
| R2-3e | Role definitions | LIMITED | [Waveform audit](../frozen-waveform-audit.md); distinguish code roles from historical routing. |
| R2-3f | Morphology and feature architecture | LIMITED | [Replay diagnostics](../replay-residual-diagnostics.md); exact historical loader unavailable. |
| R2-3g | Brier score in methods | EDITORIAL | Add definition and remove unsupported numerical methods claim. |
| R2-3h | Accuracy equations and tasks | EDITORIAL | Define rhythm and pathology endpoints separately. |
| R2-4a | External-development terminology | LIMITED | [Evidence status](../evidence-status.md); do not call selected development evidence independent. |
| R2-4b | Figure cross-reference | EDITORIAL | Correct figure reference. |
| R2-4c | Overstated F1 interpretation | EDITORIAL | Use measured values and qualified language. |
| R2-4d | Figure metrics versus confidence intervals | EDITORIAL | Describe what is actually plotted. |
| R2-4e | No threshold crossed | LIMITED | [Waveform audit](../frozen-waveform-audit.md); P8 fallback is not a full-population evaluation. |
| R2-4f | Confusion matrix presentation | EDITORIAL | Harmonize labels and denominators. |
| R2-4g | Duplicated figures | EDITORIAL | Reconcile figures against their source data. |
| R2-4h | ROC and PR tracing definition | EDITORIAL | Define plotted units and derivation. |
| R2-4i | AUROC wording | EDITORIAL | Qualify the interpretation of the reported value. |
| R2-4j | Frequency versus accuracy plot | EDITORIAL | Verify axes, bins and denominators. |
| R2-4k | Quarantine and pre/post rates | LIMITED | [Waveform audit](../frozen-waveform-audit.md); historical quarantine ledger and policy unavailable. |
| R2-4l | Rhythm top-1 | EDITORIAL | Define the decision and denominator. |
| R2-4m | Figure readability | EDITORIAL | Final layout and rendering remain pending. |
| R2-5 | PVC record versus beat level | LIMITED | Report ECG-statement scope, not beat-detection performance. |
| R2-6 | Distortion and citation claim | EDITORIAL | Remove unsupported general claim and verify citation. |
| A-01 | P4 panel versus unique ECG count | LIMITED | [Data dispositions](../revision-data-dispositions.md); preserve 962 panel rows and 733 distinct record keys. |
| A-02 | Source distribution and aliases | LIMITED | [Source evidence](../revision-evidence-20261029.md); aliases do not prove independence. |
| A-03 | Per-class metric inconsistencies | EDITORIAL | Use audited source tables and verify the final manuscript values. |
| A-04 | Thresholds and calibration isolation | LIMITED | [Data dispositions](../revision-data-dispositions.md); patient isolation remains unverified. |
| A-05 | Backbone relationships | EDITORIAL | Describe shared V3F and separate V3AG accurately. |
| A-06 | Optuna history and quarantine | LIMITED | Separate PR #4; original study database and promotion linkage are unavailable. |
| A-07 | Data availability URL | EDITORIAL | Cite the verified final artifact and restricted inputs. |
| A-08 | Missing supplement CSVs | EDITORIAL | Inventory only files actually included in the final supplement. |
| A-09 | Incorrect DOI | EDITORIAL | Verify replacement reference in the final bibliography. |
| A-10 | Mixed archive provenance and rights | LIMITED | [Licenses](../../data/licenses/README.md); mixed archive remains on HOLD. |
| A-11 | MC/Grad-CAM clinical claims | LIMITED | No clinical adjudication established; remove unsupported claims. |
| A-12 | Reader study | LIMITED | No reader study established; remove unsupported claims. |

Do not infer that an editorial disposition alone satisfies a requested
experiment. The final matrix must incorporate verified SPH results, exact
artifacts and any remaining human or editorial decisions.
