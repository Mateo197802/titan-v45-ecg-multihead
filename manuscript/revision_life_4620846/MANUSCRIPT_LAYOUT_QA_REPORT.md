# Manuscript layout QA — life-4620846

This report records the prior compile/render review of the approved English editorial manuscript, **Modular CNN–Transformer Specialists for Multi-Source 12-Lead ECG Rhythm and Pathology Classification**. The current manuscript is a 45-page **AUTHOR-REVIEW DRAFT** with 18 figures. The authenticated 26-page original and earlier intermediate builds have historical scope.

## Prior Build Review

The canonical source compiled successfully with Tectonic/XeTeX and the legitimate supplied MDPI dependencies. The approved build has no undefined or missing references, overfull boxes, missing glyphs, or visible overflow. All 45 pages were rendered and inspected, including front matter, section transitions, figures, tables, equations, declarations, appendices, and references. Quantitative plot labels and long artifact hashes were reviewed at manuscript size. Remaining underfull-box notices concern justified narrow table text; the cache's lineno UTF-8 warning did not produce a missing document glyph.

The layout retains the journal class dimensions without a smaller document-class font, reduced margins, artificial blank pages, unconditional H floats, or resize-to-fit tables. Equations and tables remain native editable LaTeX. pdfLaTeX is the intended Overleaf compiler; the hosted Overleaf service itself was not invoked for the prior local review.

Clean extraction and recompilation of the approved source ZIP were previously verified, with matching compilation content and identical normalized PDF text. The complete public source ZIP contains 50 members: the 49 compilation-package files plus `THIRD_PARTY_NOTICES.md`. The aggregate supplementary ZIP contains 31 members and the six-image V2 import receipt. The attribution notice does not change the manuscript's scientific content.

## Figure Review

All 18 unique figures are present: six author-supplied raster schematics embedded losslessly in PDF and twelve vector figures, comprising ten code-generated figures and two authenticated CODE figures. The supplied PNGs retain their native pixel dimensions without cropping, resampling, recoloring, or upscaling. A PDF wrapper does not convert raster artwork into vectors. Native PNGs remain in the repository; the source ZIP uses the PDF figures needed for compilation.

| Figure | Source basename | Native pixels | Approved PDF page |
| --- | --- | --- | --- |
| 1 | `fig00_ecg_ai_context` | 1683 × 935 | 2 |
| 2 | `fig00b_ecg_ai_evolution_gap` | 1683 × 935 | 3 |
| 3 | `fig01_graphical_abstract` | 1683 × 935 | 6 |
| 4 | `fig02_data_processing_bias_workflow` | 1683 × 935 | 8 |
| 5 | `fig03_internal_architecture` | 1586 × 992 | 13 |
| 6 | `fig03_cascade_contract` | 1672 × 941 | 14 |

The [six-image V2 receipt](audit/AUTHOR_SUPPLIED_FIGURES.json), [Figure 5 receipt](supplementary/FIGURE5_AUTHOR_IMPORT.json), and [figure reconciliation](FIGURE_RECONCILIATION_AND_REPLACEMENT.md) identify the current artwork and provenance. The earlier five-image receipt and the unchanged original 14-image `outputs/figures/` inventory describe historical scopes. The final twelve vector figure pairs and numerical results remain unchanged by the supplied-image replacements.

## Editorial and Metadata Review

The full English editorial pass was followed by a targeted 22-paragraph clarity pass. Scientific values, evaluation units, equations, limitations, and cascade/fallback content were preserved. All seven ORCIDs remain present. Paulina Vizcaíno-Imacaña at UIDE remains the sole corresponding author, Fernando Villalba-Meneses retains the School of Biological Sciences and Engineering affiliation, and Diego Almeida-Galarraga remains last author. The manuscript's AI-use acknowledgment remains in place.

The supplied June 2026 MDPI class has local draft-status wording changes. The public PDF is explicitly an author-review draft. Retained legitimate template dependencies and attribution are documented in [`latex/THIRD_PARTY_NOTICES.md`](latex/THIRD_PARTY_NOTICES.md); no byte-equivalence to the current official template is claimed. Original inputs remain preserved separately.

## Verification Boundary

This is a manuscript layout and package review, not independent clinical adjudication. The P6/P4 results and the within-CODE patient-held-out evaluation after supervised adaptation are unchanged. The CODE candidate failed promotion safeguards; independent institutional and P4 external validation remain pending. No figure presents results for those unfinished studies.

The [publication validation record](audit/PUBLICATION_VALIDATION.json) records the completed GitHub-copy clean build, matching PDF drawing streams, 102 staged-file byte checks, native-image pixel checks, seven passing publication tests and repository-wide Ruff. The full suite retains eight failures/errors reproduced on the isolated baseline; no fully passing suite is claimed. Confidential reviewer/editorial reports, response drafts, cover letters, raw ECGs, individual-record data, and weights are outside the public manuscript artifacts and this layout report.
