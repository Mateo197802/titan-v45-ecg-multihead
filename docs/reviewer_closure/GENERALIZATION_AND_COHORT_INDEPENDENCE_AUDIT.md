# Generalization and Cohort Independence Audit

This audit distinguishes selected external-development evidence, later source transfer, and independent clinical validation. “Different dataset” or “different hospital” alone does not establish patient or signal independence from every training stage.

## Cohort and unit ledger

| Evidence set | Records / observations | Patients | Role and overlap | Independence conclusion |
| --- | ---: | ---: | --- | --- |
| Selected P6 rhythm profile | 1,643 ECG | Not certified from complete historical split chain | P6 records are included in P8. Job 17315 names the V3H accepted/balanced gate manifest; V3H is development/model-selection evidence. | Not an untouched holdout. |
| Selected P8 rhythm profile | 2,193 ECG | Not certified from complete historical split chain | Includes the selected P6 cohort. | Candidate development result; not a separate independent cohort. |
| Selected P4 pathology panels | 962 binary panel observations across 733 ECG | 676 linked patients | Four panel rows may correspond to the same ECG; use panel, ECG and patient units separately. Selected ECGs map to PTB-XL fold 10. | Selected mapping has no overlap with official folds 1-9; historical job inputs remain unverified. |
| SPH frozen transfer | 25,770 ECG | 24,666 source patients | Three fixed profiles, 14 compatible ECG-statement endpoints; 2,000 patient-component bootstrap replicates. | Distinct hospital source is supported; full historical model-source independence is not certified. |
| SPH PAC embedding probe | 5,143 record exploratory patient holdout | From same SPH source | V3F embeddings, logistic baseline and MLP sensitivity; PAC target had already been inspected. | Exploratory model-assisted association, not an independent V4.5 clinical test or historical PAC-head result. |

Never sum P6 and P8 as unique records. The selected P8/P4 union is 2,926 record keys, not 2,926 unique patients. The P4 962 denominator is panel observations, not unique ECG or patients.

## Evidence supporting a distinct-source transfer

The SPH data identify a hospital source not named in the known selected P6/P8 and P4 development packages. The bounded CEDIA signature screen (job 32633) compared the 25,770 SPH signals against the retained 2,193 Chapman/Shaoxing/Ningbo ECG and 733 selected PTB-XL ECG. Under its preregistered first-10-second, 12-by-1,250, per-lead-standardized, 0.001-quantized signature rule, it found zero cross-source candidate groups and zero technical failures. The aggregate hash is `6b290dd80d9d30aa0758aa16e7ac3963b950894ad43d501236804637dd9f47d8`; the execution/staging receipt hash is `a117e0ed4df666ff3267120e7beb0070dcea1b3baefad0c0f56859615d5f329f`.

This screen is bounded to those retained packages and that signature method. It is not a complete near-duplicate search, a patient-identity match, or a comparison against unavailable V3F/V3AG pretraining and fine-tuning inputs. A separate Chapman/Ningbo duplicate finding already prevents treating dataset/source names as proof of disjointness. No identities or signal hashes are reproduced here.

## Development exposure and historical lineage

- P6 job 17314 contains an epoch sweep but no exact manifest name; its submitted script is missing. Job 17315 names the V3H accepted/balanced manifest and records the same epoch-8 result and thresholds. This strongly supports selection exposure but is not a cryptographic same-manifest proof.
- V3F/V3AG pretraining and fine-tuning source lists, exact manifests and patient maps are incomplete.
- V3P/V3M train and validation manifests and patient mappings are missing. A checkpoint metadata path is not evidence that a job opened that file.
- PTB-XL fold membership for the selected P4 map is not a checkpoint-to-job receipt.
- Original Optuna SQLite and complete trial-to-checkpoint linkage are not recovered; those files cannot certify selection isolation.

The NOC response covers the reviewed 2026-09-04 backup listing and reports no requested June paths, loader or Optuna database in that listing. It is not a search of every institutional archive. See [source triage](EVIDENCE_SOURCE_TRIAGE.md) and [checkpoint-to-manifest edges](CHECKPOINT_MANIFEST_JOB_EDGE_VERIFICATION.md).

## Technical conclusion

**Can patient independence be certified historically? No.** The bounded selected P4 fold check and SPH retained-source screen are positive, limited pieces of evidence, but historical checkpoint-to-source/patient lineage is incomplete. There is no finding that leakage occurred; the correct status is `PATIENT_ISOLATION_NOT_CERTIFIED`.

**Can SPH be described as a distinct-source transfer? Yes, with limitations.** The hospital/source distinction and bounded screen support a transfer description. The labels are ECG statements, not clinical adjudication, and the full historical training lineage is unknown.

**Can SPH be called a fully independent external clinical validation? No.** No new patient cohort, source provenance, label adjudication or model-development isolation is established by the current evidence.

## Routes to stronger evidence

1. Historical recovery: obtain exact training/validation/calibration/selection manifests, patient mappings, source versions, job scripts/configs and checkpoint hashes from a custodian-approved snapshot. Compare exact and signal-level duplicates across all model stages. No further broad CEDIA search is justified without a new source or path lead.
2. New validation: if the authors retain an independent-validation claim, freeze cohort access, rights, inclusion/exclusion, patient and signal deduplication, code/weights/configuration, endpoints, thresholds and analysis before examining performance. A new external cohort must not have been consulted for development. A prospectively approved dataset is not the only option, but any alternative must have documented source eligibility and reference quality.
3. Clinical validation: requires a clinically appropriate reference, prespecified adjudication and study governance. The current SPH code statements are not a substitute.

No MIMIC data were downloaded or evaluated. Access remains unknown, and a prior user decision limited any possible MIMIC-IV-ECG v1.0 use to automatic-report concordance rather than adjudicated clinical reference.
