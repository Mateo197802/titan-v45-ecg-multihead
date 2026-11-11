# Specialist Hidden Width 192 vs 512

**Classification:** `CAUSA_HISTÓRICA_NO_RECUPERADA`

## What Is Established

- The hash-bound reconstructed rhythm waveform report records `declared=192`, `stored=512`, `metadata_matches=false` for both P6 and P8, with hashes for the release files used by that run.
- The current frozen loader reads `heads.0.1.weight.shape[0]` from the state dict, constructs a head of that stored width, and calls `load_state_dict(..., strict=True)`. The corresponding synthetic contract test verifies this loader behavior.
- The recovered `TRAINING/train_v3d_specialists_hpc.py` source sets `hidden_dim=512` for classwise rhythm heads. Its authenticated source hash is `8e8d59889a0458c47a90f9735ff6ba017c7e1a79582d11529a608e1816e671fe`.
- The CEDIA waveform report records successful loading/inference using tensor width 512. The earlier audit did not find physical files in the repo/cache paths it checked. **Superseding evidence from 2026-11-10:** all five published release weights, including P6/P8, were found in the authorized CEDIA model store; their size and SHA-256 match the release manifest. A fresh, read-only parser tokenized the actual P6/P8 `data.pkl` metadata and verified the eight-head shapes without unpickling. See [the new architecture reconciliation](SPECIALIST_ARCHITECTURE_RECONCILIATION.md) and [shape receipt](receipts/CHECKPOINT_TENSOR_SHAPE_AUDIT_2026-11-10.json).

## What Is Not Established

The recovered trainer is not cryptographically linked to the P6/P8 released checkpoint creation jobs. Its 512-wide training configuration therefore does not prove that it produced those weights or explain why their metadata says 192. The current code default of 192 also cannot establish the historical training architecture. A successful strict load establishes compatibility of the reconstructed loader with the stored tensors, not the historical intent that created the checkpoint.

There is no authenticated P6/P8 training source, serialization record or checkpoint metadata-generation trace that resolves whether 192 is stale metadata, a default copied from another model version, or a separate architecture field. No weights or metadata were modified.

## Verification Boundaries

| Question | Result | Evidence boundary |
|---|---|---|
| Does the retained replay report 192 declared and 512 stored for P6/P8? | Yes, within the hash-bound report. | `outputs/results/revision_20261107/rhythm_waveform.json`. |
| Can current code construct a head from stored width? | Yes; it uses 512 from the serialized tensor rather than declared metadata 192. | `src/titan_v45/models/frozen_rhythm.py`, synthetic contract test, and the new static shape receipt. |
| Do the physical P6/P8 release files match their pinned identities and contain eight 512-wide heads? | Yes, within file identity and static metadata scope. | [CEDIA hash receipt](receipts/CEDIA_RELEASE_CHECKPOINT_HASHES_2026-11-10.json), [tensor shape receipt](receipts/CHECKPOINT_TENSOR_SHAPE_AUDIT_2026-11-10.json). |
| Does recovered trainer source use 512 for classwise rhythm heads? | Yes. | Hash-pinned recovered trainer source archive. |
| Does that trainer prove which architecture produced the released P6/P8 tensors? | No. | No training-job/checkpoint hash edge. |
| Can the historical cause be named? | No. | Required training metadata/serialization source is missing. |

## Reopening Procedure

The physical release checkpoints and static dimensions are now verified. To resolve the historical cause, an authorized source must still supply the original training launcher/configuration, the exact job output hashes and the serialization code that wrote `rhythm_hidden_dim`. Compare those sources with the checkpoint bytes; do not rewrite checkpoint metadata or change the released files. Record the discrepancy even if the authentic cause remains unknown.

**Conclusion:** The tensor-width evidence supports 512 as the width used by the retained replay for those release checkpoints. The discrepancy's historical cause remains unresolved, so the required classification is `CAUSA_HISTÓRICA_NO_RECUPERADA`, not “metadata obsolete” or “explained.”
