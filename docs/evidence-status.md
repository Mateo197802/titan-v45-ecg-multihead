# V4.5 Evidence and Claim Boundaries

This page summarizes the released V4.5 evaluations, metric definitions, and
evidence boundaries. The repository contains code, result tables, evaluation
manifests, and model-asset hashes, together with the authorized English
publication draft and its complete LaTeX and aggregate supplementary packages.

## Publication Status

**Modular CNN–Transformer Specialists for Multi-Source 12-Lead ECG Rhythm and
Pathology Classification** is available as an **AUTHOR-REVIEW DRAFT**, with
45 pages and 18 figures: six author-supplied raster PDF wrappers with native
PNGs retained in the repository, and twelve vector figures. The manuscript
received a full English editorial pass followed by a targeted 22-paragraph
clarity pass. Reported scientific results and evaluation boundaries remain
unchanged, and the manuscript's AI-use acknowledgment remains in place.

The public [PDF](../manuscript/revision_life_4620846/artifacts/TITAN_V45_LIFE_4620846_EDITORIAL.pdf),
[50-member complete source ZIP](../manuscript/revision_life_4620846/artifacts/TITAN_V45_LIFE_4620846_EDITORIAL_LATEX.zip),
and [31-member aggregate supplementary ZIP](../manuscript/revision_life_4620846/artifacts/TITAN_V45_LIFE_4620846_SUPPLEMENTARY.zip)
are described by the [publication manifest](../manuscript/revision_life_4620846/PUBLICATION_MANIFEST.json).
The source includes the legitimate MDPI dependencies and their
[attribution notice](../manuscript/revision_life_4620846/latex/THIRD_PARTY_NOTICES.md).
This public distribution does not establish journal submission or acceptance.
Confidential editorial/reviewer material, raw ECGs, individual-record data,
and weights are excluded from the publication artifacts.

The [layout report](../manuscript/revision_life_4620846/MANUSCRIPT_LAYOUT_QA_REPORT.md)
records the manuscript build checks. The [publication validation record](../manuscript/revision_life_4620846/audit/PUBLICATION_VALIDATION.json) confirms the clean source build, archive hashes, all seven publication tests and repository-wide Ruff. The full suite retains the same eight failures/errors observed on the isolated baseline and is not fully passing. The unchanged original 14-image inventory has a
historical scope; see [figure evidence](figure-evidence.md) for the current
18-figure inventory.

## Reported Profile Performance

| Configuration | Evaluation unit and support | Reported metrics | Protocol |
| --- | ---: | --- | --- |
| Primary6 | 1,643 selected ECGs | 95.1917% top-1 accuracy; 80.0938% binary-panel macro-F1 | Six rhythm and conduction classes on the eligible mixed-source subset. |
| Primary4 | 962 binary-panel observations, 733 ECGs, 676 linked patients | 80.2290% mean panel accuracy; 79.3456% macro-F1 | Four separately evaluated pathology panels from PTB-XL fold 10. |
| Primary8 | 2,193 selected ECGs | 90.6065% top-1 accepted-label accuracy; 76.1425% binary-panel macro-F1 | Eight rhythm and conduction classes on the mixed-source cohort; includes the Primary6 records. |

All three numbers describe repeated external-development evaluation. They are not an untouched external-final validation or a clinical performance claim. Primary6 and Primary4 use separate model branches: Primary6 uses the V3F rhythm backbone and its Primary6 specialist; Primary4 uses the separately fine-tuned V3AG pathology backbone and its calibrated specialist.

## Later CODE Evaluation

The [CODE evidence package](external_evidence/README.md) reports a completed
within-source, patient-held-out evaluation **after supervised adaptation**
to CODE. On 4,921 ECGs from 3,891 patients, the five-endpoint candidate
achieved macro-F1 60.27% (95% CI 56.46–63.41). The interval is a
patient-bootstrap aggregate. The comparison uses the same held-out ECGs
for three systems; it does not replace the selected P6/P4 release results.
The candidate failed promotion safeguards. Independent institutional
validation and independent P4 external validation remain pending.

## Metric Definitions

- **Primary6 accuracy:** a record is correct when its top-1 `pred_label` appears in the multi-label `true_labels` field. The published `correct` flag is checked against that rule.
- **Primary6 macro-F1:** the arithmetic mean of six one-versus-rest F1 values, recalculated from each class's `truth_<class>` and `threshold_pass_<class>` columns. It is not recomputed from the top-1 label alone.
- **Primary4 accuracy and macro-F1:** calculate accuracy and F1 separately for `ASMI`, `LVH`, `IMI`, and `ISC_`, then take the unweighted mean across the four panels. The support count is 962 panel observations.
- **Primary8 accepted-label accuracy:** a record is correct when its top-1 `predicted_label` belongs to the reference `accepted_labels` set. The corresponding `accepted_correct` flag is checked against this rule.
- **Primary8 macro-F1:** calculate one-versus-rest panel counts by comparing reference `accepted_labels` with model `predicted_labels`, then average the eight class F1 values.
- **Primary8 single-target accuracy:** `target_label == predicted_label` for 1,870/2,193 records (85.2713%). This is a separate measure and must not be substituted for the accepted-label accuracy.

## Evidence Chain

The [canonical profile report](../outputs/results/primary/canonical_profiles.json) records the class order, support, metrics, and release role for each profile. The detailed metric reports link each aggregate to panel confusion counts. Per-record predictions are compared with the public cohort manifests, and cohort row totals are checked against the cohort reports.

The standalone verifier recomputes the values from those rows and emits SHA-256 hashes for its input tables, reports, and verifier code. Text line endings are normalized to LF before hashing so fingerprints match on Windows and Linux:

```bash
python scripts/evaluation/verify_release_evidence.py
```

To preserve its output as a file, pass `--output path/to/report.json`. The verifier uses Python's standard library. It confirms consistency among the released prediction evidence, manifests, canonical profiles, and metric reports. It does not rerun inference on ECG waveforms, retrain any model, or establish the provenance or rights of source waveforms.

Model weight filenames, release URLs, byte sizes, and SHA-256 values are recorded in [`release-manifest.json`](../release-manifest.json) and [`release_weight_manifest.json`](../outputs/models/release_weight_manifest.json). The V3F and V3AG assets are separate branches; no single checkpoint represents both reported specialist results.

## Supporting Analyses and Limits

Cascade outputs ([summary](../outputs/results/cascade/cascade_secondary_summary.json)), Primary4 calibration ([report](../outputs/results/internal/pathology_primary4_calibration.json)), uncertainty ([summary](../outputs/results/uncertainty/mc_dropout_synthetic_smoke_summary.json)), and Grad-CAM ([smoke summary](../outputs/results/gradcam/gradcam_synthetic_smoke_summary.json)) are supporting analyses. They do not replace the Primary6, Primary4, or Primary8 metrics above. Synthetic Grad-CAM and MC-Dropout smoke results verify code paths only; they are not clinical explanations or performance estimates.

Full training and end-to-end inference are not reproducible from this repository alone: the complete source cohorts, every training checkpoint, and all training logs are not included. Distribution of the historical rhythm archive remains on hold while source attribution and licensing are unresolved. See the [CEDIA runbook](cedia-reproducibility.md), [evaluation protocol](evaluation-protocol.md), [scientific scope](scientific-boundaries.md), and [data rights inventory](../data/licenses/README.md).
