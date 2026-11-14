# Figure Evidence and Limits

## Current Publication Inventory

The approved English editorial manuscript, **Modular CNN–Transformer Specialists for Multi-Source 12-Lead ECG Rhythm and Pathology Classification**, is a 45-page **AUTHOR-REVIEW DRAFT** containing 18 figures. Its source and bibliography are available in the [canonical LaTeX directory](../manuscript/revision_life_4620846/latex/), with the [PDF](../manuscript/revision_life_4620846/artifacts/TITAN_V45_LIFE_4620846_EDITORIAL.pdf), [complete source ZIP](../manuscript/revision_life_4620846/artifacts/TITAN_V45_LIFE_4620846_EDITORIAL_LATEX.zip), and [aggregate supplementary ZIP](../manuscript/revision_life_4620846/artifacts/TITAN_V45_LIFE_4620846_SUPPLEMENTARY.zip) published separately. The [publication manifest](../manuscript/revision_life_4620846/PUBLICATION_MANIFEST.json) identifies the public package.

The canonical figure directory is [`manuscript/revision_life_4620846/latex/figures/`](../manuscript/revision_life_4620846/latex/figures/). It contains six author-supplied raster schematics and twelve vector figures. The six supplied PNGs retain their native pixels without cropping, resampling, recoloring, or upscaling; their PDF wrappers embed those pixels losslessly. Raster content remains raster content inside a PDF.

| Figure | Source basename | Native PNG dimensions | Page in approved PDF |
| --- | --- | --- | --- |
| 1 | `fig00_ecg_ai_context` | 1683 × 935 | 2 |
| 2 | `fig00b_ecg_ai_evolution_gap` | 1683 × 935 | 3 |
| 3 | `fig01_graphical_abstract` | 1683 × 935 | 6 |
| 4 | `fig02_data_processing_bias_workflow` | 1683 × 935 | 8 |
| 5 | `fig03_internal_architecture` | 1586 × 992 | 13 |
| 6 | `fig03_cascade_contract` | 1672 × 941 | 14 |

The [six-image V2 import receipt](../manuscript/revision_life_4620846/audit/AUTHOR_SUPPLIED_FIGURES.json) records PNG hashes and pixel-preserving PDF imports. Figure 5 also has a [specific import receipt](../manuscript/revision_life_4620846/supplementary/FIGURE5_AUTHOR_IMPORT.json). Earlier five-image receipts describe a historical import stage. The [current figure provenance report](../manuscript/revision_life_4620846/audit/FIGURE_MANIFEST.json), [figure file manifest](../manuscript/revision_life_4620846/latex/figures/figure_manifest.json), and [reconciliation](../manuscript/revision_life_4620846/FIGURE_RECONCILIATION_AND_REPLACEMENT.md) distinguish supplied artwork, ten code-generated vector figures, and two authenticated CODE vector figures.

The context and architecture illustrations are conceptual. They do not establish comparative performance or independent validation. Quantitative figures retain their documented evaluation populations: selected P6/P4 results, a historical internal training trajectory, or the later within-CODE patient-held-out evaluation after supervised adaptation. None supplies results for the pending independent institutional or P4 external validation.

## Historical Inventory

The 14 PNGs at the top level of `outputs/figures/` and their `figure_manifest.json` are the unchanged original manuscript inventory. They are distinct from the expanded 18-figure canonical publication inventory. Their manifest records names, archive source paths, and SHA-256 hashes. Historical verification of that exact set, archive hash, TeX references, or byte equality applies to the original package only. It does not establish the integrity of the expanded publication package. Separate report figures have their own subdirectories and manifests.

Development figures generated for tests are separate from both publication inventories. The committed tables and external-development evidence do not independently reproduce model training, establish completeness of the upstream raw ECG cohort, or validate a claim beyond its documented metric/profile contract.

## Attribution Illustration

The development-only `fig15_gradcam_contract` illustration is drawn from `data/fixtures/synthetic/synthetic_ecg_12x1250.csv`. Its overlay is a normalized signal-slope/amplitude heuristic, not a model activation, class-conditioned explanation, Grad-CAM result, real patient ECG, or clinical evidence. It is outside the canonical 18-figure manuscript inventory. Actual model Grad-CAM is generated separately by `scripts/evaluation/generate_gradcam.py` and requires the specified model and input artifacts.

## Reproduction and Review Boundary

The current source ZIP contains 50 members, including legitimate MDPI `Definitions` dependencies and [third-party notices](../manuscript/revision_life_4620846/latex/THIRD_PARTY_NOTICES.md). The 31-member supplementary ZIP provides aggregate evidence and the six-image V2 receipt. Native supplied PNGs are retained in the repository; the compilation ZIP uses their PDF wrappers. The authorized manuscript publication supersedes the earlier local-only publication convention. Confidential editorial/reviewer material, raw ECGs, individual-record data, and weights remain excluded from these artifacts.

The [layout report](../manuscript/revision_life_4620846/MANUSCRIPT_LAYOUT_QA_REPORT.md) records the prior successful 45-page compile/render review and clean-source ZIP comparison. The [publication validation record](../manuscript/revision_life_4620846/audit/PUBLICATION_VALIDATION.json) confirms the GitHub-copy archive/source checks and seven passing publication tests. Repository-wide Ruff passes; eight unrelated full-suite failures/errors also occur on the isolated baseline. Availability of the source and bibliography permits direct inspection, but does not itself certify every citation, full training reproduction, source-cohort assembly, or clinical validity. Those broader claims still require the corresponding evidence, data access, exact configurations, checkpoints, random-state records, and execution logs.
