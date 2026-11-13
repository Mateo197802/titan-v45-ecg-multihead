# R2-3f: historical preprocessing and replay equivalence

This disposition distinguishes identity of historical code, agreement of
selected decisions and strict numerical equivalence. It does not amend the
manuscript, replace canonical predictions, or establish a new validation.

## Code identity: partial, not complete

The inventoried historical `DATA_PIPELINE/data_loader_ultra.py` is 36,271 LF
bytes with SHA-256
`fc8d7367f9f2c108376839435021ec3172fe2757faa4a615f0ef5d39cbf1e855`.
That exact loader was not recovered in the searches described in the
[recovery record](../recovery-status-20261029.md); the known alternative
copies have different hashes. Its execution in a particular checkpoint's
training is not established merely by a matching interface or feature count.
The [ten-feature morphology candidate](../recovered-feature-contract.md) is
documented but not certified as the exact historical V4.5 extractor.

Ten of eleven inventoried historical source files, including backbone, trainer
and runtime, were recovered with matching bytes after specified LF
normalization. The restored trainer includes the 12-event code and the
softmax-based specialist input. Inventory matches establish identity with the
inventory, not which environment or configuration executed for a checkpoint.
The [feature contract](../recovered-feature-contract.md) separates those
recovered event functions from the candidate morphology implementation.

The reconstructed workflow uses explicit named-lead mapping, filters,
resampling, centering, padding and branch-specific windows. Their actual
implementation is inspectable in [reconstructed preprocessing](../../src/titan_v45/data/reconstructed.py)
and the [waveform audit](../frozen-waveform-audit.md); it must not be described
as the missing original loader. The later SPH source's physical units were not
certified from HDF5 attributes, and its native relative-scale contract does not
resolve the historical training signal-unit question.

## Decision agreement: selected P4 panels only

The [preserved stage record](../../outputs/results/revision_20261029/p4_replay_stage_summary.json)
retains the original 166 disagreements. Softmax alone, job `31577`, produced
168 disagreements, not an improvement. With source-backed softmax plus
named-lead mapping, jobs `31604` and `31605` each matched 962/962 binary panel
decisions over 733 ECG keys. The latter reproduced the documented per-panel
batch-32 procedure. These are selected-cohort decisions, not a demonstration
of full historical code identity or generalization to new inputs.

The later independent reconstructed waveform job `32448` likewise matched
962/962 decisions. Its execution and [receipt](../../outputs/results/revision_20261107/execution.json)
are distinct from jobs 31604/31605 and must not be reported as the same run.
For rhythm, the later P6 replay differed on 1/1,643 top-1 outcomes while P8
matched 2,193/2,193; this does not imply exact probability reproduction.

## Numerical equivalence: not established

The P4 success criterion was fixed before the historical replay: zero binary
decision disagreements and maximum absolute score difference at most `1e-5`,
with relative tolerance zero. Both conditions must pass for strict equivalence.
Job 31604's maximum difference was 0.0005892813; job 31605's was 0.0005390644.
Both fail the unchanged tolerance despite matching decisions. The later job
32448's maximum difference was 0.0006194115. In the later matched comparison,
836/962 probabilities exceeded `1e-5`; see the
[residual diagnostics](../replay-residual-diagnostics.md).

The fixed-input batch probe `32576` shows that batch size can affect outputs:
batch 1 versus batch 32 had maximum difference 0.0007278 and one IMI decision
flip among 2,932 emitted ECG-class scores. That flip was outside the 962
matched panel rows. The probe does not prove the original batch configuration
or identify the complete cause of the historical residual. No batch, filter,
threshold or tolerance was chosen by observed test accuracy.

## Reopening and manuscript boundary

The evidence ceiling applies only to sources inspected. Reopen on receipt of
the hash-matching loader, its imported morphology module, locked environment,
configuration and a job/checkpoint linkage; confirm identities before running a
new replay and predefine the comparison criterion. Preserve all previous stages.
The future manuscript may report selected decision agreement and the failed
numerical criterion together, explicitly labeling reconstructed preprocessing.
It cannot claim an exact historical preprocessing or probability replay on the
current evidence. The outstanding numerical mismatch is not automatically
evidence that the original study results were fabricated.
