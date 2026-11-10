# Exploratory SPH PAC embedding probe results

This is a technical evidence report for the repository, not manuscript text.
The manuscript, submitted PDF and editor response were not modified. These
results are exploratory, post hoc and nonconfirmatory: the Primary8 PAC target
had already been inspected before this probe. They are not clinical accuracy,
clinical adjudication, independent external validation or a repair of the
historical V4.5 result.

## Execution and frozen inputs

The protocol was frozen at commit `73a167f51c35b10a825854a9d0f6591eb5754e4c`
before fitting. Its SHA-256 is
`2a3f81fb0304030b9738c79fba5507a750452b0d1a89fcaa0980d5adf8e6b921`.
The probe used the release-tag `v0.1.0` V3F backbone, SHA-256
`ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8`, frozen
without fine-tuning. Extractor job `32883` ran on an A100; fit job `32884` ran
on CEDIA CPU nodes. Current SLURM accounting reports both `COMPLETED`, exit
`0:0`. The fit receipt and its three-file checksum manifest were verified on
CEDIA. The public receipt records job `32884`; row-level extraction artifacts
and the fitted probe bundle remain in restricted CEDIA storage.

The SPH source files were hash-pinned in the protocol: `code.csv`
`4d22759fd19d37133c78d439a5726f9e0bc412cc17483c424926ce9abb33c8fc`,
`metadata.csv`
`c6f8dc5197758a3970aae554f8b6ee884d96656b121879bc0eb1adf367ea6d86`, and
`records.tar.gz`
`cebad89d7d25663272eeb45545712d76302d334bb107cdc23fd15390c9194e55`.
The CEDIA Python dependency archive SHA-256 is
`5ea9a481f100342a4b7c9aaf98294659340d05ba20dba645007f37a3fbb6cc45`.

The positive target is SPH primary code `30`; code `31` is excluded. This is
an ECG-level recorded statement. A missing code is not a clinical negative.
Preprocessing used the pinned reconstructed SPH rhythm pipeline (12 leads,
causal 0.5-45 Hz filter, polyphase 500-to-125 Hz resampling, per-lead z-score,
and 1,250-sample windows); physical-unit conversion was not inferred. The
frozen V3F representation contributes 640-dimensional transformer tokens;
per-window token mean and max are concatenated into 1,280 features, then
averaged across each record's 10-second windows.

All 25,770 source records were technically embedded, producing 34,200 windows
from 24,666 unique source patients. A fixed 80/20 split grouped patients and
exact-waveform-connected components, seed `20261109`, with component-level
stratification by PAC presence:

| Partition | ECGs | Patient/components | Code-30 positive | Code-30 not recorded |
| --- | ---: | ---: | ---: | ---: |
| Train | 20,627 | 19,733 | 433 | 20,194 |
| Exploratory holdout | 5,143 | 4,933 | 106 | 5,037 |

The holdout prevalence is 2.06%. Threshold `0.50` was fixed in advance; no
holdout-based threshold or model tuning was performed. The baseline is
weighted L2 logistic regression (`C=1`). The fixed MLP is a sensitivity model
with architecture `1280 -> 256 -> 64 -> 1`, ReLU, dropout `0.2`, AdamW, learning
rate `0.001`, weight decay `0.0001`, 100 epochs, batch size 256 and seed
`20261109`; it used training data only and no early stopping. Bootstrap
intervals are unstratified percentile intervals from 2,000 resamples of
patient/exact-waveform connected components; all requested replicates were
valid.

Exact-waveform audit found 168 duplicate groups, zero cross-patient exact
duplicate groups and one group with conflicting code-30 presence. Training
weights assigned each exact waveform total base weight one before training-only
class balancing. A prespecified sensitivity analysis removes both holdout ECGs
from the discordant group. Approximate waveform duplicate detection was not
performed.

## Primary holdout results

Point estimates are followed by 95% patient-component bootstrap intervals.
Confusion counts and metrics are verified against the recorded supports.

| Probe | TN | FP | FN | TP | Accuracy | Sensitivity | Specificity | Precision | F1 |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| Weighted L2 logistic | 4,277 | 760 | 22 | 84 | 0.847949 (0.837837-0.857503) | 0.792453 (0.714286-0.861386) | 0.849117 (0.838766-0.859075) | 0.099526 (0.080702-0.120099) | 0.176842 (0.145951-0.209588) |
| Fixed MLP, sensitivity analysis | 4,826 | 211 | 35 | 71 | 0.952168 (0.946098-0.957406) | 0.669811 (0.579437-0.756757) | 0.958110 (0.952494-0.963463) | 0.251773 (0.203570-0.303924) | 0.365979 (0.306003-0.426150) |

| Probe | AUROC | Average precision | Brier score | 10-bin ECE |
| --- | --- | --- | --- | --- |
| Weighted L2 logistic | 0.910248 (0.883207-0.934697) | 0.415497 (0.320026-0.512911) | 0.111165 (0.106419-0.116316) | 0.236459 (0.229874-0.242951) |
| Fixed MLP, sensitivity analysis | 0.909594 (0.877659-0.938626) | 0.435851 (0.335284-0.546563) | 0.036899 (0.032705-0.041473) | 0.043966 (0.039055-0.049161) |

The accuracy contrast is not a sufficient model comparison at this prevalence.
At the fixed threshold the logistic probe has higher sensitivity and more false
positives; the MLP has higher specificity, precision and F1. Their AUROCs are
similar and their intervals overlap substantially. The high MLP accuracy must
not be presented alone as evidence of useful PAC detection.

## Discordant-duplicate sensitivity

The two ECGs from the single conflicting exact-waveform group were excluded
only for this prespecified sensitivity analysis; the primary analysis above
retains every eligible holdout ECG.

| Probe | n (+/-) | TN / FP / FN / TP | Sensitivity | Specificity | Precision | F1 | AUROC | Average precision |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| Weighted L2 logistic | 5,141 (105/5,036) | 4,277 / 759 / 22 / 83 | 0.790476 (0.711993-0.863647) | 0.849285 (0.839136-0.859327) | 0.098575 (0.078850-0.119527) | 0.175290 (0.143008-0.208414) | 0.909989 (0.882109-0.934928) | 0.417311 (0.319051-0.512009) |
| Fixed MLP, sensitivity analysis | 5,141 (105/5,036) | 4,826 / 210 / 35 / 70 | 0.666667 (0.573894-0.754550) | 0.958300 (0.952531-0.963755) | 0.250000 (0.200000-0.301527) | 0.363636 (0.301567-0.423472) | 0.908958 (0.877729-0.938083) | 0.435521 (0.333866-0.540392) |

Sensitivity-analysis accuracy, Brier score and ECE are also in the aggregate
JSON. Removing the discordant group changes the estimates only slightly; it
does not resolve source-label validity or historical source independence.

## Files and reproduction

- Frozen protocol: [`pac_v3f_embedding_probe.md`](pac_v3f_embedding_probe.md)
  and [`pac_v3f_embedding_probe.json`](../../configs/external_validation/pac_v3f_embedding_probe.json).
- CEDIA aggregate: [`pac_probe_aggregate.json`](../../outputs/results/external_sph_pac/pac_probe_aggregate.json), SHA-256 `702022c4ee1e0672649dd732777c357952119fa268cee47f9309ad273765c54a`.
- CEDIA execution receipt: [`pac_probe_receipt.json`](../../outputs/results/external_sph_pac/pac_probe_receipt.json), SHA-256 `a25466470b1fcbde4966c8b98db23cee342e5e22026f98148ee69535b0b85071`.
- Aggregate-only figure: [`PNG`](../../outputs/figures/external_sph_pac/sph_pac_probe_exploratory.png) and [`PDF`](../../outputs/figures/external_sph_pac/sph_pac_probe_exploratory.pdf).
- Figure hashes, input hashes and generator hash: [`pac_probe_figure_manifest.json`](../../outputs/figures/external_sph_pac/pac_probe_figure_manifest.json).
- Validator and figure generator: [`plot_sph_pac_probe.py`](../../scripts/external_validation/plot_sph_pac_probe.py).
- Regression tests: [`test_sph_pac_public_artifacts.py`](../../tests/evaluation/test_sph_pac_public_artifacts.py).

From the repository root, regenerate the figure and its hash manifest with:

```powershell
python scripts/external_validation/plot_sph_pac_probe.py
python -m pytest tests/evaluation/test_sph_pac_public_artifacts.py -q
python scripts/external_validation/audit_sph_public_json.py outputs/results/external_sph_pac
```

The postprocessor fails closed on aggregate/receipt hash mismatch, configuration
hash mismatch, incompatible counts, confusion/metric disagreement, bootstrap
accounting errors or detected individual identifiers. It consumes only the
aggregate JSON, execution receipt and frozen configuration. Embeddings,
patient/record identifiers, waveform hashes, split assignments, row predictions
and fitted weights are not inputs to this postprocessing step and remain in
CEDIA.

## Scientific boundary

This is a patient-split holdout within SPH, not a new external cohort. The PAC
target was previously observed in Primary8, and full V3F historical training
source independence is not certified. SPH code-30 statement presence is not a
clinical adjudication; absence of code 30 is not a ruled-out diagnosis. No MIMIC
data were downloaded or consulted. The probe does not validate the complete
P6/P8/P4 cascade, `Other` classes, quarantine behavior, clinical utility or
reader performance. The separate frozen P6/P8/P4 SPH transfer results remain
in [`sph_results.md`](sph_results.md); these new PAC-head results must not be
substituted for those model outputs or historical metrics.
