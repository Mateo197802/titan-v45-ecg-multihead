# TITAN V4.5 ECG Multihead

Code and evidence repository for TITAN V4.5 ECG research. This repository is not a manuscript or conversation archive; the canonical results and their limits are summarized here and linked to machine-readable evidence.

## Reported Results

These are repeated external-development evaluations. They are not untouched external-final validation or clinical validation.

| Profile | Evidence size | Reported result | Status |
| --- | ---: | --- | --- |
| Rhythm Primary6 | 1,643 records | 95.19% top-1 accuracy; 80.09% binary-panel macro-F1 | Six-class diagnostic branch reported in the paper ([metrics](outputs/results/external_dev/rhythm_primary6_metrics.json)). |
| Pathology Primary4 | 962 panel rows / 733 ECGs / 676 linked patients | 80.23% mean binary-panel accuracy; 79.35% macro-F1 | Accepted by project decision; observed accuracy remains 80.23% ([metrics](outputs/results/external_dev/pathology_primary4_metrics.json)). |
| Rhythm Primary8 | 2,193 records | 90.61% top-1 accepted-label accuracy; 76.14% binary-panel macro-F1 | Candidate only; it does not meet the 97% accuracy and 80% macro-F1 gates ([metrics](outputs/results/external_dev/rhythm_primary8_metrics.json)). |

Primary8's separate single-target diagnostic accuracy is 85.27% (1,870/2,193); it is not the 90.61% accepted-label metric. See the [evidence status and metric definitions](docs/evidence-status.md) before citing these values.

**Waveform reproduction remains unresolved.** Two full-cohort CEDIA runs of the fixed public-runtime/candidate-preprocessing contract disagreed with **166 of 962** archived Primary4 panel decisions. This failed historical-equivalence check is [reported with its provenance](docs/revision-evidence-20261028.md#waveform-replay-finding); successful saved-prediction recomputation and matching weight hashes do not resolve it. Primary6/Primary8 replay additionally requires the missing original signal-event extractor. Linked patient counts do not establish historical train/validation isolation.

## Verify Reported Metrics

The [October 2026 revision analysis](docs/revision-evidence-20261028.md) adds per-class metrics, explicit ECG/panel denominators, ECG-clustered bootstrap intervals and findings from the surviving CEDIA model files and historical logs. Its scope and remaining waveform-replay limitations are recorded separately from the historical release.

From the repository root, recompute the reported metrics from the tracked per-record prediction tables and check them against the canonical reports, cohort manifests, and release hashes:

```bash
python scripts/evaluation/verify_release_evidence.py
```

The command prints a JSON report with the recomputed values and SHA-256 hashes of its inputs after normalizing text line endings to LF. This keeps evidence hashes stable between Windows and Linux. The repository also includes the checked-in [verification report](outputs/results/release_evidence_verification.json); regenerate it with:

```bash
python scripts/evaluation/verify_release_evidence.py --output outputs/results/release_evidence_verification.json
```

The verifier checks saved prediction evidence; it does not rerun waveform inference or model training. Run the full test suite with `python -m pytest`.

The [submitted hash-table correction](docs/hash-correction-20261028.md) distinguishes the invalid A10 example values from measured model hashes. Run `python scripts/evaluation/verify_release_hashes.py` to validate declarations and any available physical files; add `--require-models` where all model assets are installed. Missing assets are not reported as physically verified.

## Data

Full source ECG datasets are not stored in this repository. Their sources, links, versions, and licenses are documented in [`data/licenses`](data/licenses/README.md). Evaluation manifests are in [`data/manifests`](data/manifests/README.md). Published assets and their hashes are listed in [`release-manifest.json`](release-manifest.json).

The 14 current manuscript figure PNGs are included. The manuscript source and compiled PDF are outside this repository.

Distribution of the `v0.1.0` rhythm archive is on hold because some records have unresolved provenance and licensing. See the [source inventory](data/licenses/README.md).

## Run

Requires Python 3.10, 3.11, or 3.12.

```bash
python -m pip install -r requirements/requirements-dev.txt
python -m pytest
```

Export a profile summary from the canonical registry (this does not recompute predictions):

```bash
python scripts/evaluation/evaluate_primary.py --profile rhythm_primary6_diagnostic --output outputs/results/primary/rhythm_primary6_diagnostic.json
```

Available results are in [`outputs/results`](outputs/results/README.md). Full retraining is not reproducible from this repository alone: it does not include all original datasets, checkpoints, or training logs. See [`docs/cedia-reproducibility.md`](docs/cedia-reproducibility.md) for CEDIA.

## License

Code is licensed under Apache-2.0. Model weights and datasets have separate terms; see [`MODEL_LICENSE.md`](MODEL_LICENSE.md) and [`data/licenses`](data/licenses/README.md).
