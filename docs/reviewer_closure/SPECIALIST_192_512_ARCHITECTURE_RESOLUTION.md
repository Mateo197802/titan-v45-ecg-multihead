# Specialist Hidden Width 192 vs 512

**Classification:** `CAUSA_HISTÓRICA_NO_RECUPERADA`

## What Is Established

- The hash-bound reconstructed rhythm waveform report records `declared=192`, `stored=512`, `metadata_matches=false` for both P6 and P8, with hashes for the release files used by that run.
- The current frozen loader reads `heads.0.1.weight.shape[0]` from the state dict, constructs a head of that stored width, and calls `load_state_dict(..., strict=True)`. The corresponding synthetic contract test verifies this loader behavior.
- The recovered `TRAINING/train_v3d_specialists_hpc.py` source sets `hidden_dim=512` for classwise rhythm heads. Its authenticated source hash is `8e8d59889a0458c47a90f9735ff6ba017c7e1a79582d11529a608e1816e671fe`.
- The CEDIA waveform report records successful loading/inference using tensor width 512. The physical checkpoint files were not present in the checked CEDIA repo/cache paths during this audit, so no new raw tensor inspection was performed.

## What Is Not Established

The recovered trainer is not cryptographically linked to the P6/P8 released checkpoint creation jobs. Its 512-wide training configuration therefore does not prove that it produced those weights or explain why their metadata says 192. The current code default of 192 also cannot establish the historical training architecture. A successful strict load establishes compatibility of the reconstructed loader with the stored tensors, not the historical intent that created the checkpoint.

There is no authenticated P6/P8 training source, serialization record or checkpoint metadata-generation trace that resolves whether 192 is stale metadata, a default copied from another model version, or a separate architecture field. No weights or metadata were modified.

## Verification Boundaries

| Question | Result | Evidence boundary |
|---|---|---|
| Does the retained replay report 192 declared and 512 stored for P6/P8? | Yes, within the hash-bound report. | `outputs/results/revision_20261107/rhythm_waveform.json`. |
| Can current code construct and strictly load a head from stored width? | Yes, tested synthetically; prior replay reports actual strict-load inference. | `src/titan_v45/models/frozen_rhythm.py`, `tests/evaluation/test_frozen_rhythm_contract.py`, replay receipt. |
| Does recovered trainer source use 512 for classwise rhythm heads? | Yes. | Hash-pinned recovered trainer source archive. |
| Does that trainer prove which architecture produced the released P6/P8 tensors? | No. | No training-job/checkpoint hash edge. |
| Can the historical cause be named? | No. | Required training metadata/serialization source is missing. |

## Reopening Procedure

If an authorized source supplies the original P6/P8 checkpoint files and training source, first verify their SHA-256 against the release manifest and the recovered artifact receipt. Then inspect every state-dict tensor shape with a safe, read-only loader; compare the declared fields, constructor arguments, exact job source/config and serialized checkpoint metadata. Do not rewrite checkpoint metadata or change the released files. Record the discrepancy even if the authentic cause remains unknown.

**Conclusion:** The tensor-width evidence supports 512 as the width used by the retained replay for those release checkpoints. The discrepancy's historical cause remains unresolved, so the required classification is `CAUSA_HISTÓRICA_NO_RECUPERADA`, not “metadata obsolete” or “explained.”
