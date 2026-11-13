# Reviewer Reproducibility Gaps

**As of:** 2026-11-10. This is an evidence map, not a claim that every requested experiment has been satisfied. The submitted manuscript, PDF and response letter remain unchanged.

## Reproducibility is component-specific

| Component | Evidence currently available | Reproducibility demonstrated | Not demonstrated |
| --- | --- | --- | --- |
| Saved P6 decisions | 1,643 selected ECG; reconstructed top-1 agrees on 1,642/1,643 and binary sets agree. | High decision concordance on the selected saved cohort. | Exact score reproduction, training isolation, or untouched evaluation. The 1,643-record V3H cohort informed epoch selection. |
| Saved P8 decisions | 2,193 selected ECG; top-1 and binary sets agree on 2,193/2,193, including 58 fallback cases. | Decision-rule agreement on saved fields. | Exact historical preprocessing, independent validation, or passage of the full Primary8 project gate. |
| Saved P4 decisions and scores | 962 panel observations across 733 ECG and 676 linked patients; decisions agree on 962/962. | Thresholded panel decisions agree. | Numerical equivalence: maximum probability difference is `0.0006194115`, above the prefixed `1e-5` tolerance. Do not widen the tolerance. |
| Released weights and architecture | Release-manifest sizes and whole-artifact SHA-256 values, checkpoint tensor contracts and strict state-dict loading are documented. | Identity/integrity of the released files and compatibility with the current declared architecture. | Which exact historical code, manifests and patient partitions produced each checkpoint. |
| Reconstructed waveform inference | Frozen P6/P8/P4 weights were run on selected development waveforms and on the full SPH V1 source; the SPH scoring receipt reports 25,770/25,770 ECG per profile. | Repeatable execution of the versioned reconstructed pipeline and reproducible aggregate checks within the recorded protocol. | Exact equivalence to the missing original 36,271-byte loader or historical June preprocessing. |
| Original training | Selected manifests, checkpoint metadata, retained logs and scheduler accounting survive for some stages. Ten of eleven inventoried source files were recovered. | Bounded evidence of particular jobs, configuration declarations and selected descendants. | Complete job -> script/config -> manifest bytes actually read -> patient mapping -> output checkpoint hash chain for V3F/V3AG/V3M/V3H/V3S/V3P/V3Q. |
| Selection and split isolation | Job 17315 names the V3H accepted/balanced manifest and the P6 epoch-8 checkpoint; job 17314 records an epoch sweep with matching result values. | Strong evidence that V3H informed P6 model selection. | Exact manifest/script binding for job 17314, parent population and exclusion ledger, or patient-level train/validation/calibration/test disjointness for all released weights. `PATIENT_ISOLATION_NOT_CERTIFIED`; this is not a finding of leakage. |
| Calibration | Job 17296 log/script and job 17305 log/script survive; P4 threshold values agree with checkpoint metadata. | Threshold-vector consistency and existence of calibration diagnostics. | Patient isolation or cryptographic output-checkpoint binding to the released P4/P6 files. The P4 job's logged output name is a different artifact. |
| Later SPH transfer evaluation | Frozen protocol, scoring/aggregation receipts, 25,770 ECG from 24,666 patients, 14 compatible statement endpoints, aggregate figures and independent metric/interval computations. | The declared reconstructed transfer analysis and its aggregate computations. | A truly untouched cohort relative to all historical backbone training/tuning, clinical adjudication, incident disease, clinical utility, quarantine, or complete workflow performance. |
| Exploratory PAC embedding probe | V3F embeddings frozen; 80/20 train/holdout grouped by patient and exact-waveform components; logistic baseline and MLP sensitivity; jobs 32883/32884 complete. | Reproduction of the post hoc exploratory probe under its pinned inputs and protocol. | Confirmation of V4.5's original PAC head, clinical PAC diagnosis, independence from prior target inspection, or independent external validation. |

## Seven distinct reproducibility claims

1. **Saved prediction reconstruction:** supported for decision concordance only; P4 score tolerance fails, and P6 has one top-1 mismatch.
2. **Reconstructed inference:** executable and versioned for selected development and SPH inputs; it remains a new reconstruction where the original loader is missing.
3. **Weights and parameter contract:** whole-artifact hashes and tensor/architecture compatibility are checkable; this is not a training receipt.
4. **Original training:** not fully reproducible. A completed SLURM state is accounting evidence, not proof of the exact files read or weights emitted.
5. **Data selection:** selected descendants survive, but parent populations, exclusions and several actual manifests do not.
6. **Original calibration:** thresholds and retained job records can be compared; full patient isolation and output-checkpoint identity remain unverified.
7. **Later validation:** SPH transfer results are measured against coded ECG statements. They do not establish complete historical independence or clinical validation.

## Reopen conditions

Reopen historical training/split claims only with the exact checkpoint digest, submitted script/config bytes, job receipt, manifests actually read, dataset version, patient/group mapping, split roles, and checkpoint hash recorded by the producing job. Reopen quarantine only with the original uncertainty scores, frozen policy/version, all-input transition ledger, reference outcomes and denominators. Reopen the loader claim only with a source matching the expected raw SHA-256 or a verified normalized-byte identity plus the complete dependency/contract chain.

The inspected archives and the NOC-reviewed 2026-09-04 backup provide a bounded evidence ceiling, not proof that every offline or institutional archive was searched. The negative result applies only to the documented paths and sources checked. See [source triage](EVIDENCE_SOURCE_TRIAGE.md), [recovered versus missing evidence](RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md), [split lineage](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md), [loader replay disposition](HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md) and [SPH delivery audit](SPH_DELIVERY_AUDIT.md).
