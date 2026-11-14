# Figure reconciliation and replacement

The approved 45-page English **AUTHOR-REVIEW DRAFT**, **Modular CNN–Transformer Specialists for Multi-Source 12-Lead ECG Rhythm and Pathology Classification**, contains 18 unique figures in [`latex/figures/`](latex/figures/): six author-supplied raster illustrations, ten code-generated vector figures, and two authenticated CODE vector figures. The source ZIP uses the PDF figures; native supplied PNGs remain in the repository.

The original archive had 15 figure calls but 14 unique image names. The revision preserves their scientific purposes, replaces the duplicate pathology panel with a distinct plot, adds an aggregate internal-history figure, and integrates the two CODE figures. The original 14-image top-level `outputs/figures/` inventory remains unchanged and historical. It is separate from the canonical inventory below.

## Canonical Inventory

| Figure | Final source basename | Purpose / evidence | Current format and disposition |
| --- | --- | --- | --- |
| 1 | `fig00_ecg_ai_context` | Conceptual 12-lead ECG workflow | Author-supplied native PNG; lossless raster PDF wrapper; page 2 |
| 2 | `fig00b_ecg_ai_evolution_gap` | Conceptual distinction among reference units | Author-supplied native PNG; lossless raster PDF wrapper; page 3 |
| 3 | `fig01_graphical_abstract` | Separate fitted specialists | Author-supplied native PNG; lossless raster PDF wrapper; page 6 |
| 4 | `fig02_data_processing_bias_workflow` | Signal preparation and evidence stages | Author-supplied native PNG; lossless raster PDF wrapper; page 8 |
| 5 | `fig03_internal_architecture` | Architecture design and head-specific tensor inputs | Author-supplied 1586 × 992 PNG; lossless raster PDF wrapper; page 13 |
| 6 | `fig03_cascade_contract` | Reporting contracts | Author-supplied native PNG; lossless raster PDF wrapper; page 14 |
| 7 | `fig06_rhythm_confusion` | Archived P6 predictions; single-reference subset | Code-generated vector PDF and 320-dpi PNG companion |
| 8 | `fig08_class_metrics` | Archived P6 predictions; 1,000 confusion-multinomial bootstrap replicates, seed 4620846 | Code-generated vector PDF and 320-dpi PNG companion |
| 9 | `fig07_pathology_confusion` | Archived P4 panel predictions; panel-specific denominators | Code-generated vector PDF and 320-dpi PNG companion |
| 10 | `fig08b_pathology_class_metrics` | Archived P4 predictions; 1,000 confusion-multinomial bootstrap replicates, seed 4620846 | Distinct P4 class metrics replace the original duplicate panel; vector PDF and 320-dpi PNG companion |
| 11 | `fig09_roc_curves` | Archived P6/P4 probabilities; grouped distinct score thresholds | Code-generated vector PDF and 320-dpi PNG companion |
| 12 | `fig10_precision_recall_curves` | Archived P6/P4 probabilities; grouped distinct score thresholds; recall-weighted AP | Code-generated vector PDF and 320-dpi PNG companion |
| 13 | `fig11_calibration` | Archived binary probabilities; 10 equal-width bins, nonempty bins only | Code-generated vector PDF and 320-dpi PNG companion |
| 14 | `fig12_source_performance` | Archived P6 source aliases and correctness; Wilson ECG intervals | Code-generated vector PDF and 320-dpi PNG companion |
| 15 | `fig13_error_flows` | Archived P6 single-reference top-1 confusions; ten largest observed counts | Vector bar chart and 320-dpi PNG; supersedes unsupported Sankey/quarantine-interception caption |
| 16 | `fig_code_sensitivity_ppv` | `docs/external_evidence/figures/figure_03_sensitivity_ppv.pdf` | Authenticated CODE vector PDF and 300-dpi PNG, copied byte-for-byte |
| 17 | `fig_code_observed_pr` | `docs/external_evidence/figures/figure_05_observed_precision_recall.pdf` | Authenticated CODE vector PDF and 300-dpi PNG, copied byte-for-byte |
| 18 | `fig16768_internal_history` | `supplementary/JOB_16768_AGGREGATE_EPOCHS.csv`; historical internal run only | Code-generated vector PDF and 320-dpi PNG companion |

## Supplied Artwork and Provenance

Figures 1–6 retain the supplied RGB PNG bytes without pixel edits, cropping, resampling, recoloring, or upscaling. Their PDF wrappers are lossless raster embeddings. Figure 5 replaces the earlier generated architecture drawing; it remains an illustration of the documented contracts. The other twelve figure pairs and numerical results are unchanged by the supplied-image replacements. The [six-image V2 receipt](audit/AUTHOR_SUPPLIED_FIGURES.json) records native dimensions and PNG/PDF hashes; the [Figure 5 receipt](supplementary/FIGURE5_AUTHOR_IMPORT.json) records its specific import. Earlier five-image receipts describe the preceding import stage and remain historical.

The [provenance manifest](audit/FIGURE_MANIFEST.json) and [figure file manifest](latex/figures/figure_manifest.json) cover all 18 figures. The CODE figures originate from the authenticated public evidence package at source commit `63c74b3fde2c51f7f8cde4ad396d77a1bd16cb29`. Original files remain preserved separately. Historical artwork alone does not establish creator identity or redistribution rights; current supplied illustrations and generated graphics have distinct provenance records.

## Scientific and Verification Boundaries

Baseline bootstrap intervals describe row-level resampling; CODE intervals resample patient clusters. Source accuracy intervals are Wilson ECG intervals. ROC/AP calculations group distinct score thresholds; AP is recall-weighted precision. P6 remains 95.19% top-1 accuracy and 80.09% binary-panel macro-F1 on 1,643 ECGs. P4 remains 80.23% mean binary-panel accuracy and 79.35% binary-panel macro-F1 across 962 observations from 733 ECGs.

CODE is a within-source, patient-held-out evaluation after supervised adaptation: 4,921 ECGs, 3,891 patients, five endpoints, macro-F1 60.27% (95% CI 56.46–63.41). The candidate failed promotion safeguards. Independent institutional and P4 external validation remain pending, and no figure depicts results for those unfinished evaluations. Conceptual illustrations do not establish clinical validity or complete training lineage.

The 45-page build/render review and clean-source comparison are recorded in the [layout QA report](MANUSCRIPT_LAYOUT_QA_REPORT.md). The [publication validation record](audit/PUBLICATION_VALIDATION.json) confirms seven passing publication tests, identical page drawing streams after clean-ZIP compilation, six lossless image checks, and 102 verified staged files. Ruff passes. The full suite retains the same eight failures/errors found on the isolated baseline. The [publication manifest](PUBLICATION_MANIFEST.json) identifies the authorized PDF, 50-member source ZIP, and 31-member aggregate supplementary ZIP. Confidential editorial/reviewer material and restricted individual-record data are outside these publication artifacts.
