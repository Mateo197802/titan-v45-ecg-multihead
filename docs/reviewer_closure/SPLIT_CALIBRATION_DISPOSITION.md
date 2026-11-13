# R2-3a and A-04: splits and calibration isolation

This document distinguishes recorded threshold configuration from demonstrated
patient-level isolation. A named file, saved flag or official dataset fold is
not a substitute for the actual run-linked patient manifests. Historical split
isolation is **not certified**; this is not a finding that leakage occurred.

## Rhythm P6 and P8

The sanitized [P6 calibration lineage](../../outputs/results/revision_20261029/p6_calibration_lineage_summary.json)
records job `17315`, internal zero-bias F1 tuning, 192 ECG and 276 windows,
and the same six thresholds in the internal and selected development reports.
The class order and threshold vector agree with the
[P6 profile](../../configs/profiles/rhythm_primary6_diagnostic.json), allowing
for floating-point representation. The selected P6 development cohort contains
1,643 ECG and is a subset of selected P8, not an independent population.

The P6 checkpoint metadata identifies the selected V3H development manifest as
a rhythm validation input; it is therefore not an untouched final test. The
reported V3P training-manifest name points to V3J plus INCART/SVDB windows,
but the actual historical manifest and patient mapping are not recovered.
P8's separate specialist and retained development results do not supply an
independent train/calibration/patient-overlap audit. See
[historical artifact recovery](../../outputs/results/revision_20261028/cedia_artifact_recovery.json).

The live CEDIA Slurm accounting and logs add a selection warning: job `17314`
(`p6_v3p_sweep`) records 12 distinct V3O checkpoint epochs with external
metrics; epoch 8 is the only logged epoch passing both the 0.95 accuracy and
0.80 macro-F1 gates. Job `17315` names the V3H accepted/balanced manifest,
`v3o_rhythm_specialist_epoch_008.pt`, and reports the same 1,564/1,643
decisions, 0.951917 accuracy, 0.800938 macro-F1 and six thresholds. This is
strong evidence that the V3H gate informed P6 selection, not a pristine final
test. The 17314 submitted script and exact manifest name are missing, so the
same-file linkage remains an inference, not a cryptographic proof. The P6
six-class threshold vector matches its profile configuration; the separate
eight-class vector in checkpoint metadata belongs to Primary8 and is not a
threshold discrepancy. See the detailed
[checkpoint-to-split lineage](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md).

## Pathology P4

The [P4 internal calibration summary](../../outputs/results/internal/pathology_primary4_calibration.json)
and [P4 profile](../../configs/profiles/pathology_primary4.json) agree on
ASMI, LVH, IMI and ISC_ thresholds. The summary declares internal validation
and no external data for threshold selection; that declaration is not an
independent reconstruction of all patients or upstream backbone exposures.
The historical job `17296` is recorded as completed and its retained log is
fingerprinted in the artifact receipt. Archived log summaries describe 1,492
window-panel observations; they are not 1,492 unique ECG or patients.
The recovered submit-script candidate and live CEDIA copy have matching
SHA-256 values, and the log's final four thresholds match the P4 checkpoint
metadata. The script calls V3D calibration code and writes a V3D-named output
checkpoint, however; no output hash binds that result to the released P4
artifact. The missing V3M panel files and patient rows still prevent a
calibration-isolation check.

The [official PTB-XL fold audit](../../outputs/results/revision_replay_diagnostics_20261107/p4_official_fold_coverage.json)
links 733 selected P4 ECG to 676 patients in official fold 10 and finds no
selected-patient overlap with official folds 1-9. This verifies a property of
the official metadata and selected identifiers only. It does not demonstrate
that the historical backbone or specialist actually trained only on the
official folds indicated by a filename, nor does it establish calibration
isolation or the unknown historical candidate population.

## What would close the isolation gap

Obtain the exact V3F/V3AG backbone and specialist train, internal-validation,
calibration and model-selection manifests with patient identifiers in
authorized storage, their source versions and duplicate mappings; retain the
configuration, logs and checkpoint hashes establishing which files each job
actually read. For V3M request the specific train/val manifests, internal
panel index and four panel files listed in the
[R1-2 evidence-ceiling disposition](R1_2_EVIDENCE_CEILING.md); for rhythm
request the listed V3P training and calibration manifests and V3H parent.
Then compare patients and exact/near-duplicate signals across all stages,
including the backbone, while keeping row-level data restricted.

Until those inputs exist, retain recorded thresholds and selected results but
do not assert that patient leakage was excluded or that external-development
performance is a certified independent test. The documentation and tests here
verify consistency of the surviving artifacts, not the missing experiment.
