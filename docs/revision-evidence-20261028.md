# Revision Evidence, 28 October 2026

This revision adds a reproducible saved-prediction analysis and an audit of surviving CEDIA artifacts. The versioned results are in [`outputs/results/revision_20261028`](../outputs/results/revision_20261028). Historical release predictions remain unchanged.

## Recompute the Analysis

```bash
python scripts/evaluation/build_revision_report.py --output-dir /path/to/new/report --seed 2026 --n-bootstrap 2000 --figures
```

The report reads released prediction CSVs. It does not run waveform inference or training. The JSON records exact input/code hashes, missing-score denominators, metric definitions, class supports, source supports and bootstrap settings. PNG/PDF output requires Matplotlib.

Primary6 top-1 accuracy accepts a prediction present in the reference label set. Its macro-F1 is computed from six thresholded binary panels, not from a single-target confusion matrix. Primary8 additionally reports the single-target view separately. Primary4 reports unweighted mean panel accuracy separately from pooled panel-observation accuracy.

Primary4 contains **962 panel observations and 733 distinct record IDs**, all carrying the source label `PTBXL_FULL_100HZ_DERIVED`. These counts are not interchangeable with patient counts. Repeated panel observations for an ECG are resampled together. Bootstrap sampling units are `(source, record_id)` ECG clusters; no patient-level independence is asserted. The selected panels do not preserve a clinical population's natural prevalence.

The recovered upstream PTB-XL metadata maps all 733 ECGs to **676 patient identifiers**, with all ECGs assigned to fold 10. A separate [patient-cluster sensitivity analysis](../outputs/results/revision_20261028/primary4_patient_sensitivity.json) retains all ECGs and panel observations for each patient in the same bootstrap draw. Its 2,000-replicate intervals are macro-F1 [0.761516, 0.824779] and mean panel accuracy [0.777538, 0.827820]. This establishes the available cohort mapping, not isolation from historical training/calibration manifests, which remain to be recovered. No individual patient identifiers are included in the exported report.

To reproduce this sensitivity analysis after obtaining the corresponding upstream metadata:

```bash
python scripts/evaluation/bootstrap_primary4_patients.py --ptbxl-metadata /path/to/ptbxl_database.csv --output /path/to/patient_sensitivity.json
```

## CEDIA Recovery

The SHA-256 values calculated from the five physical model files on CEDIA match the release manifest. A compute-node inspection completed as SLURM job `31402` (`COMPLETED`, exit `0:0`) with Python 3.11.14 and PyTorch 2.10.0+cu128. The module is named `pytorch/2.2`; the runtime version was measured rather than inferred from that module name.

Surviving historical logs `slurm-17315.out` and `slurm-17296.out` contain the reported Primary6 and Primary4 aggregate results and frozen thresholds. Original private logs remain in the audit workspace; their fingerprints and sanitized findings are recorded in [`cedia_artifact_recovery.json`](../outputs/results/revision_20261028/cedia_artifact_recovery.json).

The Primary6 specialist checkpoint records `v3h_rhythm_external_gate_holdout_accepted_balanced_manifest.csv` as its rhythm validation manifest. This is affirmative evidence of development use. The released evaluation must not be described as an untouched external-final test.

The Primary6/Primary8 checkpoint feature configuration includes 12 signal-event features in addition to morphology and backbone outputs. Their exact original extractor has not yet been recovered in this audit. The surviving loader and a morphology extractor from a separate V4 source tree are recovery candidates, not a certified byte-identical V4.5 preprocessing implementation. Any forensic replay using those candidates must disclose that limitation and retain prediction discrepancies.

## Waveform Replay Finding

SLURM job `31415` completed a forensic Primary4 forward pass on all **733 ECGs / 962 panel observations**, using the public backbone/specialist implementation and declared feature order with candidate preprocessing recovered from surviving sources. It produced **166 decision disagreements**, maximum absolute probability difference **0.697892**, and mean absolute difference **0.119857** against the archived predictions. The candidate morphology hash and execution-code hash are recorded in the [replay finding](../outputs/results/revision_20261028/primary4_forensic_replay.json).

This is a failed historical-equivalence check. It does not establish that the archived predictions are false or that a particular preprocessing step caused the discrepancy. The full original processing and feature policy must be recovered before waveform-to-output reproducibility can be certified. Archived scientific results are preserved; these replay probabilities are not substituted for them. No threshold or class-order search was performed to improve agreement.

The portable repository entry point completed independently as job `31416`, reproducing those discrepancy counts and probability differences on the same full cohort. It verifies the released model/archive hashes and accepts an explicit morphology candidate. Example within a configured SLURM compute environment:

```bash
python scripts/cedia/forensic_replay_primary4.py \
  --repo-root /path/to/checkout \
  --release-root /path/to/release-root \
  --morphology-module scripts/cedia/recovery_candidates/morphology_features_v4.py \
  --work-dir /path/to/new/replay-output --scratch-dir /path/to/node-local-scratch
```

Install the data dependencies listed by the repository, including WFDB, SciPy and Zstandard. Release root uses the relative asset layout in `release-manifest.json`. Stage dependencies on node-local storage when shared-filesystem import latency is excessive. A `0` limit evaluates all ECGs; `--limit N` is a compatibility pilot, not full-cohort verification. The included morphology module is explicitly a recovered candidate; its provenance and limits are documented beside it.

## Interpretation and Open Work

- Correct class counts, metrics and thresholds from the identified prediction contract and original logs. Do not choose between inconsistent tables by their higher performance.
- Keep P6 and P4 backbone instances separate in architecture descriptions and parameter accounting.
- Treat complete-workflow routing, coverage and quarantine performance as unverified until real record-level decisions support the reported counts. A class-role registry is not a measured routing result.
- Recover original training/calibration manifests and patient mappings before certifying split isolation. A path containing `training/` is not itself proof of overlap.
- Evaluate a genuinely new source or a correctly isolated source-held-out experiment before making independent external-generalization claims.
- Report missing provenance and data rights explicitly. No new mixed-source waveform redistribution is authorized by this statistical analysis.
- Synthetic uncertainty and Grad-CAM tests establish code-path behavior only. They do not measure the benefit of human review or establish clinical safety.

File hashes establish byte identity. They do not establish clinical validity, historical test independence, or complete training reproducibility. Evidence statuses are independent: saved-prediction recomputation can pass while waveform replay or provenance remains unresolved.
