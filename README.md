# TITAN V4.5 ECG Multihead

TITAN V4.5 is a research-only, 12-lead ECG model and reproducibility package. The repository publishes two separate operational lineages: a V3F rhythm branch and a V3AG pathology branch. They are intentionally not represented as one frozen checkpoint.

> **Research use only.** This software and its weights are not a medical device and must not be used for clinical decisions. See [NO_CLINICAL_USE.md](NO_CLINICAL_USE.md).

## Canonical Metrics

| Profile | Classes | External-development accuracy | Macro-F1 |
|---|---:|---:|---:|
| `rhythm_primary8` | 8 | 90.6065% | 76.1425% |
| `rhythm_primary6_diagnostic` | 6 | 95.1917% | 80.0938% |
| `pathology_primary4` | 4 | 80.2290% | 79.3456% |

Primary8, Primary6 diagnostic, and Primary4 are separate release profiles with fixed class orders, thresholds, hashes, and evaluation scripts. Primary6 diagnostic evaluates six rhythm classes as its own profile; Primary4 evaluates four pathology panels with classwise binary thresholds.

Machine-readable results are in [`outputs/results`](outputs/results/README.md). Dataset manifests and cohort reports are in [`data`](data/README.md).

## Architecture

The V3F/V3AG backbone accepts a `12 x 1250` signal at 125 Hz and combines a four-stage 1D residual encoder with a nine-layer, 640-dimensional Transformer. It exposes 14 rhythm outputs, 7 pathology outputs, quality, biometrics, morphology, and clinical-axis heads.

- Backbone parameters: **58,352,219**
- Global rhythms: `AFIB, SB, STACH, NSR, RBBB, PAC, 1AVB, PVC, Flutter, LBBB, 2AVB, 3AVB, LQTS, Paced`
- Global pathologies: `ASMI, LVH, IMI, ISC_, ALMI, ILMI, LAE`
- Primary8: `AFIB, SB, STACH, NSR, RBBB, PAC, 1AVB, PVC`
- Primary4: `ASMI, LVH, IMI, ISC_`

See [`docs/architecture.md`](docs/architecture.md) and the profile contracts in [`configs/profiles`](configs/profiles/README.md).

## Installation

Python 3.10, 3.11, and 3.12 are supported.

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements/requirements-cpu.txt
```

For development:

```bash
python -m pip install -r requirements/requirements-dev.txt
python -m pytest
python -m ruff check .
```

CEDIA users should load the cluster CUDA/PyTorch module first, then install `requirements/requirements-cedia-cuda.txt`.

## Release Assets

Weights and evaluated ECG cohorts are distributed through the `v0.1.0` GitHub Release, not Git LFS. Download `release-manifest.json` first, then fetch and verify all assets:

```bash
python scripts/artifacts/fetch_release_assets.py \
  --manifest release-manifest.json \
  --root release_downloads
python scripts/artifacts/verify_artifact_hashes.py \
  --manifest release-manifest.json \
  --root release_downloads
```

The strict loader rejects mismatched branch, SHA-256, class order, thresholds, or specialist output width. Model weights are governed by [MODEL_LICENSE.md](MODEL_LICENSE.md); dataset subsets retain their original CC BY 4.0 terms.

## Evaluation

Canonical primary reports use full-coverage top-1 accuracy for rhythm and macro-F1 over the declared classes. No top-k oracle or hidden abstention is used in the primary metrics.

```bash
python scripts/evaluation/evaluate_primary.py \
  --profile rhythm_primary6_diagnostic \
  --output outputs/results/primary/rhythm_primary6_diagnostic.json
python scripts/artifacts/audit_publication.py --root .
```

The uncertainty module implements MC-Dropout predictive entropy and mutual information with explicit quarantine. It is a research control, not a guarantee against incorrect predictions. Grad-CAM exports include time and per-lead attribution.

## Repository Layout

| Path | Purpose |
|---|---|
| `configs/profiles/` | Frozen public class, threshold, and hash contracts |
| `src/titan_v45/` | Modular data, model, training, evaluation, XAI, uncertainty, and artifact code |
| `scripts/` | Stable command-line wrappers for local and CEDIA workflows |
| `tests/` | Unit, integration, evaluation, and regression verification |
| `data/` | Sanitized manifests, cohort reports, dataset cards, licenses, and synthetic fixtures |
| `outputs/` | Weight asset manifests, metrics, CSV predictions, confusion matrices, and evaluation evidence |
| `reports/` | Human-readable metric, model, and dataset cards |
| `docs/` | Architecture, protocols, provenance, and scientific boundaries |

## Dataset Attribution

The release subsets contain the ECG records referenced by the public validation manifests. Upstream dataset licenses and citations remain attached to the released cohorts.

- PTB-XL: Wagner et al., *Scientific Data* 7, 154 (2020), PhysioNet version 1.0.3, CC BY 4.0.
- Chapman-Shaoxing-Ningbo: Zheng et al., *Scientific Data* 9, 136 (2022), PhysioNet version 1.0.0, CC BY 4.0.

See [`reports/dataset_cards`](reports/dataset_cards/README.md) for cohort-specific scope and limitations.

## Citation And Licenses

Citation metadata is provided in [`CITATION.cff`](CITATION.cff). Source code is Apache-2.0. Model weights use the research-only license in [`MODEL_LICENSE.md`](MODEL_LICENSE.md). ECG records preserve their upstream licenses.
