# TITAN V4.5 ECG Multihead

TITAN V4.5 is a research framework for 12-lead electrocardiogram (ECG)
analysis. It combines a one-dimensional residual encoder and a Transformer
with specialist configurations for rhythm and ECG pathology classification.
This repository provides the implementation, evaluation evidence, and
reproducibility tools. The reported results do not establish independent
institutional or prospective clinical validation.

## Publication Draft and Downloads

The English manuscript, **Modular CNN–Transformer Specialists for Multi-Source
12-Lead ECG Rhythm and Pathology Classification**, is available as an
**AUTHOR-REVIEW DRAFT**. Public distribution is authorized; this status does
not imply journal submission, acceptance, or publication in Life.

- [Editorial manuscript PDF — 45 pages](manuscript/revision_life_4620846/artifacts/TITAN_V45_LIFE_4620846_EDITORIAL.pdf)
- [Complete LaTeX source ZIP — 50 members](manuscript/revision_life_4620846/artifacts/TITAN_V45_LIFE_4620846_EDITORIAL_LATEX.zip)
- [Aggregate supplementary ZIP — 31 members](manuscript/revision_life_4620846/artifacts/TITAN_V45_LIFE_4620846_SUPPLEMENTARY.zip)
- [Publication manifest](manuscript/revision_life_4620846/PUBLICATION_MANIFEST.json)

The [canonical manuscript source](manuscript/revision_life_4620846/latex/manuscrito.tex)
uses 18 figures: six author-supplied raster illustrations embedded losslessly
in PDF, with their native PNGs retained in the repository, and twelve vector
figures. The complete source includes the legitimate MDPI `Definitions`
dependencies and [third-party attribution](manuscript/revision_life_4620846/latex/THIRD_PARTY_NOTICES.md).
See the [manuscript guide](manuscript/revision_life_4620846/README.md) for
editorial scope, compilation, and the prior layout review. Confidential
editorial correspondence, raw ECGs, individual-record data, and model
weights are excluded from these publication artifacts.

## System Architecture

The original profiles process ten-second, 12-lead windows at 125 Hz.
The V3F rhythm and V3AG pathology branches use separately fine-tuned
backbones. Each released profile pairs a backbone and specialist with a
class contract and thresholds. See the [architecture](docs/architecture.md)
and [evaluation protocol](docs/evaluation-protocol.md) for the input and
output contracts.

## Evaluated Configurations and Performance

| Configuration | Task | Evaluation data | Reported metrics |
| --- | --- | --- | --- |
| Primary6 | Six-class cardiac rhythm classification | 1,643 selected ECGs from the mixed-source rhythm evaluation | 95.19% top-1 accuracy; 80.09% binary-panel macro-F1 ([report](outputs/results/external_dev/rhythm_primary6_metrics.json)) |
| Primary8 | Eight-class cardiac rhythm classification | 2,193 selected ECGs from the mixed-source rhythm evaluation, including the Primary6 records | 90.61% top-1 accepted-label accuracy; 76.14% binary-panel macro-F1 ([report](outputs/results/external_dev/rhythm_primary8_metrics.json)) |
| Primary4 | Four-class ECG pathology classification | PTB-XL fold-10 panels: 962 observations across 733 ECGs and 676 linked patients | 80.23% mean binary-panel accuracy; 79.35% binary-panel macro-F1 ([report](outputs/results/external_dev/pathology_primary4_metrics.json)) |

These are selected external-development evaluations with different class
definitions and denominators. Primary6 top-1 accuracy checks membership
in its reference label set. Primary8 accepted-label accuracy checks the
profile's accepted reference set; its separate single-target accuracy
is 85.27% (1,870/2,193). Rhythm macro-F1 averages the classwise binary
results, not top-1 decisions. Primary4 gives equal weight to the four
binary panels, and an ECG can occur in more than one panel. See the
[metric definitions](docs/evidence-status.md#metric-definitions) and
[cohort manifests](data/manifests/README.md).

The later [CODE-15% evidence package](docs/external_evidence/README.md)
compares three systems on the same held-out ECGs within CODE-15% after
supervised adaptation of the candidate to that source. It is separate from
the release results above. This within-source, patient-held-out evaluation
covered 4,921 ECGs from 3,891 patients and five endpoints, with macro-F1
60.27% (95% CI 56.46–63.41). The candidate failed promotion safeguards.
Independent institutional validation and independent P4 external validation
remain pending.

## Reproducibility

Use Python 3.10, 3.11, or 3.12. From the repository root:

```bash
python -m pip install -e '.[dev,data,optuna]'
python scripts/evaluation/verify_release_evidence.py
python scripts/evaluation/verify_release_hashes.py
python -m pytest
```

Current [publication integration checks](manuscript/revision_life_4620846/audit/PUBLICATION_VALIDATION.json) passed all seven artifact/publication tests and repository-wide Ruff. The full suite has eight failures/errors that are also present on the isolated previous commit; it is not reported as fully passing.

The [verification report](outputs/results/release_evidence_verification.json)
recalculates published metrics from archived predictions, not from a new
waveform inference run. Hash verification distinguishes missing assets
from verified local files; add `--require-models` when all weights are
installed. See the [CEDIA runbook](docs/cedia-reproducibility.md) and the
[results index](outputs/results/README.md) for other verification paths.

## Model Assets and Data

The [v0.1.0 release](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/tag/v0.1.0)
contains the original model assets. The [release manifest](release-manifest.json)
records filenames, byte sizes, and SHA-256 digests. Full source datasets
are not stored in Git. The mixed-source rhythm archive should not be
republished while upstream provenance and redistribution rights remain
unresolved; see the [source and rights inventory](data/licenses/README.md).

## Limitations

The selected cohorts do not establish full-input coverage, historical
patient isolation, or independent clinical performance. The [waveform
replay](docs/frozen-waveform-audit.md) reproduced all 962 Primary4 binary
decisions but did not meet the frozen probability tolerance. The exact
original loader and the historical all-input cascade are not certified.
The complete original training lineage cannot be reproduced from the
public repository alone.

## Licensing

Code is licensed under Apache-2.0 ([license](LICENSE)). Model weights and
datasets have separate terms ([model license](MODEL_LICENSE.md),
[data sources and licenses](data/licenses/README.md)).
Bundled MDPI template files retain their own notices and attribution;
see [third-party notices](manuscript/revision_life_4620846/latex/THIRD_PARTY_NOTICES.md).

## Scientific References and Supporting Evidence

Use [CITATION.cff](CITATION.cff) for software attribution and cite the
source datasets as specified in their
[dataset cards](reports/dataset_cards/chapman-shaoxing-external-dev.md)
and [PTB-XL card](reports/dataset_cards/ptb-xl-external-dev.md).
The [documentation index](docs/README.md) links the methods, evidence,
and historical audits. The 14 PNGs in the original top-level
`outputs/figures/` inventory remain historical assets. The expanded
18-figure publication inventory is in
[`manuscript/revision_life_4620846/latex/figures/`](manuscript/revision_life_4620846/latex/figures/);
see [figure evidence and limits](docs/figure-evidence.md) for their distinct
provenance and verification scopes.
