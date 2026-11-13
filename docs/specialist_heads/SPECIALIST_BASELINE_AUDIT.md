# Specialist Baseline Audit

**Audit date:** 2026-11-11
**Experiment branch:** `codex/titan-specialist-heads-20261111`
**Base commit:** `2677a3333069c16915cb71acd55d0f0176570bcf`
**Protocol:** [`PROTOCOL_FREEZE_20261111.md`](PROTOCOL_FREEZE_20261111.md)

## Frozen published comparators

| Profile | Published backbone | Published specialist | SHA-256 |
|---|---|---|---|
| P6 rhythm | `backbone-v3f-original.pt` | `specialists-v3p-e008-primary6-diagnostic.pt` | `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8`; `9c5a9265a7155e1206c551cc4e6d645b86363ba3dbdeb7baf7b9f173c314be3d` |
| P8 rhythm | `backbone-v3f-original.pt` | `specialists-v3q-primary8-best-candidate.pt` | `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8`; `b30cb2bbb45f1231c93ff1c196aa966b57b49831cadb296131c0283e7b0ceb02` |
| P4 pathology | `backbone-v3ag-pathology.pt` | `specialists-v3ag-primary4-calibrated.pt` | `bf71e4cf8acc34031cb3611c7031e0649822e705fd7dcea354a3ea583ce920ee`; `cf5091e962fffb3254b1a71fe57236dd82ea0139093df192511499d931391dbc` |

These are immutable release-asset hashes. The current CEDIA feature-extraction stage is required to verify the bytes again before inference; pointer files in Git alone are not physical checkpoints.

## Historical reference results

The project-provided canonical references are P6 macro-F1 0.8009 on 1,643 selected ECGs, P8 macro-F1 0.7614 on 2,193 selected ECGs, and P4 macro-F1 0.7935 on 962 panel observations (733 ECGs, 676 linked patients). These are different populations, tasks, and denominators. They are context only and are not pooled or treated as a directly comparable baseline for the new source-defined evaluation.

The new comparison will re-score the frozen published weights and candidate heads on the same reconstructed waveform inputs, same eligible records, same endpoints, and source-specific references. That is a paired post-hoc development comparison, not a replay of the historical data loader or original training and not independent external validation.

Historical training-source exposure for every published specialist is not fully linked to exact consumed manifests and checkpoint bytes. Consequently, a Georgia/CPSC result can demonstrate candidate transfer to that measured development source under this protocol, but it cannot prove that the published comparator itself had never seen that source.

## Architecture and supervision boundary

The released global backbone contract declares 14 rhythm outputs and 7 pathology outputs. P6 and P8 are separate binary specialist profiles; P4 has four binary pathology outputs. The rhythm specialist input contract is 681 features and P4 is 670 features. The new experiment trains only replacement heads on frozen V3F/V3AG representations.

The 14/7 global output widths do not prove that every auxiliary class was supervised or evaluated. This experiment does not train ALMI, ILMI, LAE, or auxiliary rhythm labels; it uses only P6, P8, and P4 targets with the source-specific masks in the frozen protocol.

## Status at freeze

- No new model-performance metrics had been inspected when the protocol was frozen.
- The Stage-A trainer, data preflight, feature extraction, and evaluation code are new post-hoc experimental code, not historical V4.5 training code.
- No Stage-B backbone fine-tuning or Optuna search has been launched.
- No new training job had started at this audit point.
- CEDIA raw waveforms, individual labels, feature matrices, predictions, and new checkpoint files remain private.
- `INDEPENDENT_EXTERNAL_VALIDATION = NOT_RUN`.

## Data-source audit prerequisites

The prior authorized cache inventory found partial waveform availability: Chapman-Shaoxing, CPSC2018, Georgia, and a partial PTB-XL low-resolution waveform cache. The Stage-A preflight must re-count usable files and class support, record sampling rates/durations/leads from headers, verify source licenses, remove exact-byte duplicates before scoring, and fail closed on source-contract or hash mismatch. The exact usable counts from that new preflight supersede preliminary cache counts, but not historical V4.5 denominators.

Challenge-2021 SNOMED grouping is tied to the official challenge mapping; PTB-XL zero-likelihood SCP entries remain unknown rather than negative. [PhysioNet/CinC Challenge 2021 label mappings](https://moody-challenge.physionet.org/2021/papers/2021ChallengePaperPMEA.pdf), [PTB-XL v1.0.3 documentation](https://physionet.org/content/ptb-xl/1.0.3/).
