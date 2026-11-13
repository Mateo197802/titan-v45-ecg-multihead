# Specialist Head Stage A Execution

**Study:** `specialist-heads-20261111-v2`

**Protocol:** V2 and amendment 01, frozen before model-performance evaluation

**Scope:** post-hoc head-only development experiment; not historical V4.5 training

**Independent external validation:** `NOT_RUN`

## Execution record

The published V3F/V3AG backbones and V3P/V3Q/P4 specialists were loaded as read-only baselines. The new trainable modules were class-wise specialist heads; both backbones stayed frozen. The V2 config SHA-256 is `6be93477c3905c38a7cdd257cf6007a6a1246ce27354d067024ef1f5f5c9c14c`. Feature extraction used commit `7cc45eb45a256d2495b352aa3ad614d2142de9a5`; training and evaluation used commit `341d022e5f524f7af514cacf234ce48da8309b0a`. The training receipt records that all feature-pipeline paths were unchanged between these revisions.

The bounded design compared weighted BCE, source-balanced BCE, and focal loss at one fixed `ClassWiseBinaryMLP` architecture (hidden width 192, dropout 0.25), three declared seeds, AdamW, and a maximum of 40 epochs with validation-based early stopping. Candidate thresholds were selected on the separate calibration split. The fixed primary candidate was `weighted_bce_seed_20261111`; ablations were descriptive and were not promoted based on source-holdout scores. No Optuna search or partial-backbone fine-tuning was run.

| CEDIA job | State | Result |
|---|---|---|
| 33133 | Cancelled | Sequential feature scan was stopped after slow serial storage reads; no feature cache or metrics were produced. |
| 33139 | Failed | Feature-extraction path defect; no usable result. |
| 33142 | Completed | 11,133/11,133 rhythm records and 6,205/6,205 P4 records extracted; 13,725 rhythm windows; zero extraction errors. |
| 33166 | Failed | Threshold dictionary ordering defect detected before fitting; no model result. |
| 33171 | Failed/incomplete | All 29 candidates trained, but final summary serialization failed. Its partial outputs remain preserved as an unsuccessful attempt and are not used in the reported results. |
| 33182 | Completed | Successful Stage A: 29 training runs/checkpoints; 34 model-comparison rows and 208 per-class result rows. |

The failed and cancelled attempts remain preserved in CEDIA. The successful job's row-level feature cache, candidate checkpoint files, private training receipt, per-record metadata and predictions remain in authorized CEDIA storage and are not included in this repository.

## Results

Results below compare the frozen published baseline and the fixed primary candidate on the same eligible records and endpoints. They do not establish superiority across sources or clinical utility.

| Profile and evaluation | Baseline macro-F1 | Primary candidate macro-F1 | Paired delta (95% CI) | Unit for interval | Interpretation |
|---|---:|---:|---:|---|---|
| P4, PTB-XL fold-9 internal evaluation | 0.7336 | 0.8504 | +0.1168 [0.0612, 0.1759] | Patient-grouped | Internal patient-separated split; not external validation. The candidate misses the predeclared maximum sensitivity-drop target. |
| P6, Georgia development-source holdout | 0.7184 | 0.7204 | +0.0020 [-0.0261, 0.0297] | Record-grouped, not patient | Small difference; interval includes zero. |
| P8, Georgia development-source holdout | 0.6877 | 0.6902 | +0.0025 [-0.0251, 0.0298] | Record-grouped, not patient | Small difference; interval includes zero. NSR has no positive support in Georgia and is not scored there. |
| P6, CPSC leave-one-source-out sensitivity | 0.9476 | 0.8394 | -0.1083 [-0.1254, -0.0909] | Record-grouped, not patient | Candidate is substantially worse on this measured development source. |
| P8, CPSC leave-one-source-out sensitivity | 0.8657 | 0.7275 | -0.1382 [-0.1581, -0.1183] | Record-grouped, not patient | Candidate is substantially worse on this measured development source. |

The table is a concise rendering of the full sanitized aggregate CSVs. The paired intervals use 2,000 bootstrap replicates with seed `20261111`. The P4 and rhythm source results are not pooled because they have different endpoints, populations and split designs.

## Decision and limits

The candidate's P4 macro-F1 increase does not satisfy the Stage A success target because sensitivity falls by 0.0889 for LVH, 0.1579 for IMI and 0.1154 for ISC_. P6 Georgia sensitivity falls by 0.2533 for RBBB and 0.0769 for PVC. P8 Georgia sensitivity falls by 0.0962 for PAC and 0.0400 for RBBB. In the CPSC sensitivity analysis, P6 RBBB falls by 0.2489 and P8 PAC by 0.4702. Do not promote this candidate as a general improvement and do not change thresholds after inspecting these results.

Georgia and CPSC do not provide validated patient IDs. Their confidence intervals are record-grouped and must not be described as patient-clustered. The frozen backbones' exact historical source exposure is not fully linked to consumed training manifests. Byte-identical waveform checks found no remaining exact duplicates among included records, but do not rule out re-encoded or near-duplicate signals. SPH, V3H, fold 10, and manual-review/locked data were not used.

These are new post-hoc experiments on frozen public weights. They do not recover original V4.5 training, prove historical patient isolation, or constitute independent external or clinical validation. No manuscript or historical result was modified.

## Reproducible outputs

- [`SPECIALIST_MODEL_COMPARISON.csv`](../../outputs/results/specialist_heads/20261111-v2/SPECIALIST_MODEL_COMPARISON.csv): all 34 sanitized comparison rows, including negative and exploratory results.
- [`SPECIALIST_PER_CLASS_RESULTS.csv`](../../outputs/results/specialist_heads/20261111-v2/SPECIALIST_PER_CLASS_RESULTS.csv): all 208 sanitized per-class rows; no record-level identifiers.
- [`SPECIALIST_DATASET_SPLITS.json`](../../outputs/results/specialist_heads/20261111-v2/SPECIALIST_DATASET_SPLITS.json): aggregate split counts only.
- [`SPECIALIST_AGGREGATE_AUDIT.json`](../../outputs/results/specialist_heads/20261111-v2/SPECIALIST_AGGREGATE_AUDIT.json): arithmetic/privacy verifier receipt.
- [`verify_aggregate_results.py`](../../scripts/specialist_experiments/verify_aggregate_results.py): rechecks confusion-derived metrics, macro-F1, deltas and identifier-like columns.

The public aggregate SHA-256 values are recorded in `SPECIALIST_AGGREGATE_AUDIT.json`. Private feature/cache and candidate-checkpoint hashes are deliberately retained only in CEDIA.
