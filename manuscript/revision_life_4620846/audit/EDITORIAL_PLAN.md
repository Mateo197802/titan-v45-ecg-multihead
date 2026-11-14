# Editorial plan and completed scope — life-4620846

The current English manuscript is **Modular CNN–Transformer Specialists for Multi-Source 12-Lead ECG Rhythm and Pathology Classification**, a 45-page **AUTHOR-REVIEW DRAFT** with 18 figures. The authenticated 26-page original is preserved separately. Intermediate correction text and earlier build reports have historical scope; they do not define the current publication package.

## Completed Revision

1. Retain the architecture, scientific section sequence, valid equations, and original A1–A10 subjects, while bounding independence, quarantine, clinical utility, and training-lineage statements to the recovered evidence.
2. Expand dataset/source ontology, partition accounting, output supervision, morphology, optimization, and evaluation definitions. Preserve selected P6 results of 95.19% top-1 accuracy and 80.09% binary-panel macro-F1 on 1,643 ECGs, and selected P4 results of 80.23% mean binary-panel accuracy and 79.35% binary-panel macro-F1 across 962 observations from 733 ECGs.
3. Include completed retrospective SPH/LUDB/PTB analyses and negative morphology/selective findings. Present the later within-CODE patient-held-out evaluation explicitly as following supervised adaptation: 4,921 ECGs, 3,891 patients, five endpoints, macro-F1 60.27% (95% CI 56.46–63.41), with failed promotion safeguards.
4. Reconcile the canonical 18 figures: six native author-supplied PNGs embedded losslessly in PDF, ten code-generated vector figures, and two authenticated CODE vector figures. Figure 5 uses the supplied 1586 × 992 architecture image. Figures 1–6 appear on pages 2, 3, 6, 8, 13, and 14. Keep the original 14-image `outputs/figures/` inventory unchanged as historical evidence.
5. Complete a full English editorial pass, followed by a targeted 22-paragraph clarity pass, without changing numerical scientific results, evaluation boundaries, equations, or cascade/fallback content. Retain the manuscript's AI-use acknowledgment and human author responsibility.
6. Preserve all seven ORCIDs and the author order, Paulina Vizcaíno-Imacaña at UIDE as sole corresponding author, Fernando Villalba-Meneses's School of Biological Sciences and Engineering affiliation, and Diego Almeida-Galarraga as last author.
7. Deliver the public PDF, complete 50-member LaTeX source ZIP, and 31-member aggregate supplementary ZIP, including the six-image V2 import receipt. Word generation is discontinued. Confidential response drafts, cover letters, and reviewer/editorial reports remain outside the public package.

## Publication and Template Handling

Public distribution of the manuscript, licensed dependencies, images, and artifacts is authorized and supersedes the earlier local-only publication convention. The [publication manifest](../PUBLICATION_MANIFEST.json) identifies the downloads. This authorization does not imply journal submission or acceptance.

The complete source includes legitimate MDPI `Definitions` files and [`THIRD_PARTY_NOTICES.md`](../latex/THIRD_PARTY_NOTICES.md). The official publisher template identifies MDPI as author and CC BY 4.0 as its license. The supplied June 2026 class retains local draft-status wording changes; no official byte-equivalence is asserted. Original inputs remain preserved separately. Raw ECGs, individual-record data, weights, private execution paths, and credentials remain excluded from the publication artifacts.

## Verification and Remaining Work

The manuscript review verified 45 pages, all 18 figures, no visible overflow, no missing references or glyphs, and clean-source compilation with identical normalized PDF text. See the [layout QA report](../MANUSCRIPT_LAYOUT_QA_REPORT.md). The [publication validation record](PUBLICATION_VALIDATION.json) confirms seven passing publication tests, matching page drawing streams after clean-ZIP compilation, six lossless image checks, 102 verified staged files, and a passing Ruff check. The full suite reports 782 passes with four failures and four errors; all eight failing/error test IDs also occur on the isolated baseline. These preexisting issues remain unresolved.

Independent institutional validation and independent P4 external validation remain pending and result-free. The completed CODE adaptation study does not close those gaps. Editorial revisions and publication packaging do not upgrade the evidence into independent clinical validation or certify complete historical training lineage. Confidential review reconciliation remains separate from public publication documentation.
