# TITAN V4.5 ECG Multihead

Code and reproducibility repository for TITAN V4.5 ECG analysis.

## Data

Full source ECG datasets are not stored in this repository. Their sources, links, versions, and licenses are documented in [`data/licenses`](data/licenses/README.md). Evaluation manifests are in [`data/manifests`](data/manifests/README.md). Published assets and their hashes are listed in [`release-manifest.json`](release-manifest.json).

Only the 14 PNG images referenced by the submitted manuscript are included; the manuscript source and PDF are not.

Distribution of the `v0.1.0` rhythm archive is on hold because some records have unresolved provenance and licensing. See the [source inventory](data/licenses/README.md).

## Run

Requires Python 3.10, 3.11, or 3.12.

```bash
python -m pip install -r requirements/requirements-dev.txt
python -m pytest
```

Write the frozen profile report (this does not run model inference):

```bash
python scripts/evaluation/evaluate_primary.py --profile rhythm_primary6_diagnostic --output outputs/results/primary/rhythm_primary6_diagnostic.json
```

Available results are in [`outputs/results`](outputs/results/README.md). Full retraining is not reproducible from this repository alone: it does not include all original datasets, checkpoints, or training logs. See [`docs/cedia-reproducibility.md`](docs/cedia-reproducibility.md) for CEDIA.

## License

Code is licensed under Apache-2.0. Model weights and datasets have separate terms; see [`MODEL_LICENSE.md`](MODEL_LICENSE.md) and [`data/licenses`](data/licenses/README.md).
