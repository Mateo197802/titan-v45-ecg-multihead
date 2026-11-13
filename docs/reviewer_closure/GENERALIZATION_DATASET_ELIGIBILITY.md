# Generalization Dataset Eligibility

**As of:** 2026-11-10

**Disposition:** No untouched, fully eligible independent test cohort is currently available.

**Manuscript:** `SIN_EDITAR`.

## Eligibility decision

An external dataset is eligible for confirmatory evaluation only if access and redistribution rights are documented, the cohort was not used to select or tune the model, all relevant training/pretraining sources are checked for patient and signal overlap, the reference supports the endpoint, and the protocol and analysis are frozen before performance is inspected. A different institution name alone does not meet these conditions.

| Candidate/evidence set | Known role and evidence | Eligibility for a new independent test | Disposition |
| --- | --- | --- | --- |
| V3H accepted/balanced rhythm manifest | Job 17315 names it for the P6 epoch-8 gate; its metrics satisfy the explicit selection thresholds. Job 17314 records an epoch sweep with matching epoch-8 result. | No. It was used for model selection/gating. The exact sweep manifest digest is absent. | Development/model-selection evidence; never relabel as independent test. See [`CEDIA job receipt`](receipts/CEDIA_JOB_LOGS_2026-11-10.json). |
| V3S P4 high-confidence panels | Job 17296 names the external panel-index alias; its final aggregate matches released P4 headlines after rounding. Panel bytes, patient maps and checkpoint linkage are unavailable. | No. This is selected panel evidence and patient isolation is uncertified. | Retain as bounded historical evidence only; see [`checkpoint/job lineage`](CHECKPOINT_JOB_MANIFEST_VERIFICATION_FINAL.md). |
| SPH hospital-source transfer | 25,770 ECG scored under P6/P8/P4, 24,666 patient clusters for interval design, 14 compatible statement endpoints. The source was already consulted for transfer and exploratory PAC work. | No. Not untouched; labels are ECG statements, and complete historical pretraining/source lineage is unavailable. | Report only as later statement-level transfer with limitations. See [`SPH results`](../external_validation/sph_results.md). |
| MIMIC-IV-ECG v1.0 | No download or evaluation was performed in this task. Prior project context permits considering only automatic-report concordance; access, license, quota and source overlap are not established here. | Not currently eligible. Automatic reports would not be clinician-adjudicated truth. | Do not download or describe as available. Reassess only after access, rights, overlap and frozen protocol are documented. |
| New collaborator or public cohort | No source, permission, patient-level reference, deduplication evidence or untouched status has been supplied. | Unknown, therefore not eligible yet. | Require an auditable source package and protocol lock before performance access. |

## Independence boundary

The bounded CEDIA signal-screen result covers only retained packages and its stated signature method; the complete V3F/V3AG pretraining/fine-tuning inputs are not linked to released checkpoints. Therefore historical patient/signal independence is **not certified**. This does not prove leakage. No candidate above can be promoted to independent validation by changing its name or by using a later split of the already consulted SPH source.

## Evidence needed to change eligibility

1. Written access, permitted-use and publication terms for the cohort and reference labels.
2. Versioned source manifest and patient/group mapping; complete duplicate checks against all available pretraining, fine-tuning, calibration and selection sources.
3. A declaration that no evaluation labels, scores or summary metrics were used for development or threshold choice.
4. Frozen checkpoint, code, preprocessing, thresholds, endpoints, exclusions, failure handling and patient-clustered analysis before the first performance query.
5. Reference semantics stated precisely: automatic ECG statement, adjudicated ECG interpretation, or longitudinal clinical outcome.

Until those artifacts exist, the eligible-cohort count for a new confirmatory evaluation is **zero identified**, not zero records in the world.
