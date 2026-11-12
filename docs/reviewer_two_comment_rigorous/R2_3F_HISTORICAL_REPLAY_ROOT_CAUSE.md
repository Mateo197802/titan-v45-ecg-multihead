# R2-3f: What explains historical replay differences?

**Historical verdict: `HISTORICAL_PROVENANCE_UNVERIFIED`.** This is not a
failed identity check of the released model bytes. It is the inability to
bind the original loader, environment and per-run inputs to those scores.

## Authenticated mechanisms

The [October source recovery](../recovery-status-20261029.md) restored
ten of eleven inventoried files. The missing target is
`DATA_PIPELINE/data_loader_ultra.py`, 36,271 bytes, SHA-256
`fc8d7367f9f2c108376839435021ec3172fe2757faa4a615f0ef5d39cbf1e855`.
The 36,465-byte reconstructed candidate does not match. The new scoped
file check searched the live V4.5 project, the source checkout and the
historical-replay tree to depth four for that basename, variants and
the inventoried size; it found no candidates. A reachable local Git
path-history search also returned no candidate by that name. These
negative searches are bounded, not proof that the loader never existed.

| Hypothesis | Evidence and disposition |
| --- | --- |
| Lead mapping and missing leads | An early replay matched lead names case-sensitively and wrongly zeroed AVR/AVL/AVF. The recorded canonical name mapping restored them. The recovered trainer's softmax was also restored. Softmax alone had 168 disagreements; the joint source-backed correction brought P4 to zero across 962 selected panel decisions. It did not establish numerical equivalence. |
| Morphology, filter, sample rate and scaling | The candidate follows the verified reconstructed pipeline; actual inputs and sensitivity are measured on authorized LUDB. These observations distinguish mechanisms, not the historical input configuration. Morphology finite extremes are not winsorized; the derived vector is bounded by clipping. |
| Checkpoint and metadata selection | SHA-256 and strict stored-tensor loading bind the released inference. Rhythm width metadata says 192 whereas stored weights require 512. Loading from tensor width is structural evidence, not score fitting or proof that a historical loader made the same choice. |
| Batch shape, precision, libraries and hardware | The [prior fixed-input probe](../replay-residual-diagnostics.md) reproduced size-32 GPU outputs exactly. Size 1 versus 32 differed by up to 0.0007278 with one IMI call change outside the historical matched panel. The new traced replay adds CPU/CUDA and batching perturbations on a different, fixed authorized input set. The original library stack, kernels and exact batch construction are not authenticated. |
| P6 ranking | The only archival top-1 disagreement inverted the same two nearly tied classes: gaps about 0.00001994 in the archive and 0.00005590 after replay. Both are nonzero, and the emitted binary sets agree. This explains the ordering mechanism, not the upstream source of the numeric difference. |

## Unchanged equivalence rule

Historical P4 still fails the original absolute tolerance of `1e-5`
with zero relative tolerance: **836/962** score pairs outside tolerance,
**0/962** decision disagreements in the selected comparison. P6 had one
top-1 difference; P8 had none in 2,193 records. There is no threshold
relaxation, parameter search against archived outputs, or selection of
a perturbation because it happens to move scores toward the archive.
Neither clinical intervals nor an exact June execution can be inferred
from the reconstructed forward pass.

The archive comparison and new perturbations answer different questions.
If the original loader is recovered later, require an inventory match
and original execution linkage before comparing on an authorized cohort.
