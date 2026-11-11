# Independent External Eligibility

**Current state: `INDEPENDENT_EXTERNAL_VALIDATION = NOT_RUN`.**

SPH has already been examined and V3H was used in prior selection; neither is a new independent confirmation set. PTB-XL fold 10 is excluded from this experiment. Georgia and CPSC are development-source holdouts in the new protocol, not confirmatory external cohorts; prior model exposure, patient identity limitations, and the development role prohibit an independent clinical-validation claim. PTB-XL fold 9 is an internal patient-grouped evaluation split.

MIMIC-IV-ECG v1.0 was previously considered only for agreement with automated report statements. No authorized download, exposure audit, patient/signal overlap check, locked protocol, or confirmatory inference is part of this run. Automated statements would not constitute adjudicated clinical reference labels. No external data are downloaded in this task.

A future external evaluation requires documented permissions, source versions, patient and signal overlap checks against training/pretraining, compatible endpoints, a frozen population and score policy, and a single predeclared inference run. Until then, report only development-source transfer and internal evaluation.
