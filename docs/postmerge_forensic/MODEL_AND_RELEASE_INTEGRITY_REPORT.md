# Model and release integrity

The SHA-256 ledger compares the original Git release declarations with
actual files from the CEDIA cache. GitHub release digests are a separate
metadata observation, not a second read of the payload bytes. Experimental
checkpoint hashes are not promoted into release identities.

| Model | Release SHA-256 | Contract |
|---|---|---|
| V3F | `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8` | CNN-Transformer, 12×1250 signal, 12 lead mask, 10 morphology values; 14 rhythm / 7 pathology global outputs |
| V3AG | `bf71e4cf8acc34031cb3611c7031e0649822e705fd7dcea354a3ea583ce920ee` | Separate pathology backbone with the same reconstruction dimensions |
| P6 | `9c5a9265a7155e1206c551cc4e6d645b86363ba3dbdeb7baf7b9f173c314be3d` | 681 inputs; AFIB, SB, STACH, RBBB, 1AVB, PVC exposed; stored eight-logit specialist before profile projection |
| P8 | `b30cb2bbb45f1231c93ff1c196aa966b57b49831cadb296131c0283e7b0ceb02` | 681 inputs; AFIB, SB, STACH, NSR, RBBB, PAC, 1AVB, PVC |
| P4 | `cf5091e962fffb3254b1a71fe57236dd82ea0139093df192511499d931391dbc` | 670 inputs; ASMI, LVH, IMI, ISC_ |

Stored 512 hidden units override stale rhythm metadata 192; these
values are not the vector dimensions or a release-asset mismatch.
Morphology directly enters both specialist inputs and the global
rhythm head, but not the global pathology input or the shared waveform
embedding. The P4 specialist also receives global rhythm probabilities.

P6 applies sigmoid after mean logits; P8 uses mean window membership
probabilities and its own fallback contract; P4 uses one selected
window. Frozen thresholds: P6 0.82, 0.835, 0.775, 0.515, 0.57,
0.43; P8 0.8, 0.55, 0.8, 0.525, 0.725, 0.45, 0.775, 0.725; P4
0.67, 0.705, 0.635, 0.595. See the
[architecture reconciliation](../reviewer_closure/SPECIALIST_ARCHITECTURE_RECONCILIATION.md).
This verifies the reconstructed contract, not a missing historical loader.

CEDIA job 33847 independently rehashed and deserialized all five files
with `weights_only=True` and completed `0:0`. This was a restricted
deserialization check, **not** a new strict forward execution. Strict
loading and actual repeated inference on the same five release hashes
are supported by the prior native job 33796. The newly queued synthetic
CPU fixture has its own status in the native audit receipt. Serialized
tensor elements include buffers and are not trainable parameter counts.
A local V3F copy independently matched the same declared byte count and
SHA-256. The two dataset archives were checked against GitHub release
metadata; this audit did not reopen their protected waveform payloads.

Native checkpoint SHA identities without a producer/parent binding are
retained as such. For historical weights, the exact output digest from
16768 and actual parent read by 16781 remain absent; only the archived
V3F path-to-release digest link is corroborated. No weight was trained,
changed, or exported by the forensic runs.
