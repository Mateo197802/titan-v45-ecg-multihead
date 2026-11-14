# Life revision life-4620846 — English publication draft

**Modular CNN–Transformer Specialists for Multi-Source 12-Lead ECG Rhythm and Pathology Classification** is the approved editorial manuscript for public distribution as an **AUTHOR-REVIEW DRAFT**. It contains 45 pages and 18 figures. Public distribution does not imply journal submission, acceptance, or publication in Life.

## Public Downloads and Source

- [Editorial manuscript PDF](artifacts/TITAN_V45_LIFE_4620846_EDITORIAL.pdf)
- [Complete LaTeX source ZIP — 50 members](artifacts/TITAN_V45_LIFE_4620846_EDITORIAL_LATEX.zip)
- [Aggregate supplementary ZIP — 31 members](artifacts/TITAN_V45_LIFE_4620846_SUPPLEMENTARY.zip)
- [Publication manifest](PUBLICATION_MANIFEST.json)

The canonical source is [`latex/manuscrito.tex`](latex/manuscrito.tex), with editable section inputs, equations, tables, bibliography, figures, and legitimate MDPI `Definitions` dependencies. The 50-member source ZIP comprises the 49 compilation-package files plus `THIRD_PARTY_NOTICES.md`; it uses the PDF figures required for compilation. Native author-supplied PNGs are also retained in the repository's [`latex/figures/`](latex/figures/) directory. The supplementary ZIP contains aggregate evidence and the six-image V2 import receipt. Word is outside the final LaTeX/PDF delivery.

The user has authorized publication of these manuscript sources, dependencies, images, and artifacts, superseding the earlier local-only publication convention. Confidential response drafts, cover letters, reviewer/editorial reports, raw ECGs, individual-record data, and model weights are excluded from the public publication packages.

## Editorial and Scientific Scope

The revision expands the authenticated 26-page original while retaining its scientific section sequence and A1–A10 subjects. A full English editorial pass was followed by a targeted 22-paragraph clarity pass. Numerical results, equations, scientific limitations, and cascade, abstention, and fallback content remain unchanged by these editorial passes. No new training, waveform inference, or statistical experiment was performed for the editorial revision. The manuscript's AI-use acknowledgment remains in place, and authors retain responsibility for the scientific content.

All seven ORCIDs and the author order are preserved. Paulina Vizcaíno-Imacaña at UIDE remains the sole corresponding author; Fernando Villalba-Meneses retains the School of Biological Sciences and Engineering affiliation; Diego Almeida-Galarraga remains last author.

| Evaluation | Population and unit | Preserved result and boundary |
| --- | --- | --- |
| Primary6 | 1,643 selected ECGs | 95.19% top-1 accuracy; 80.09% binary-panel macro-F1 |
| Primary4 | 962 binary-panel observations across 733 ECGs | 80.23% mean binary-panel accuracy; 79.35% binary-panel macro-F1 |
| CODE after supervised adaptation | Within-source, patient-held-out evaluation; 4,921 ECGs, 3,891 patients, five endpoints | Macro-F1 60.27% (95% CI 56.46–63.41); candidate failed promotion safeguards |

Selected P6/P4 development results and within-CODE adaptation do not establish independent institutional validation. Independent institutional and independent P4 external validation remain pending.

## Figures and Evidence

The canonical 18-figure inventory contains six author-supplied raster schematics (Figures 1–6), ten code-generated vector figures, and two authenticated CODE vector figures. The supplied PNGs are retained at native resolution and embedded losslessly in PDF without cropping, resampling, recoloring, or upscaling. Figure 5 is the author-supplied 1586 × 992 architecture image. Figures 1–6 occur on pages 2, 3, 6, 8, 13, and 14 of the approved PDF. Their [V2 receipt](audit/AUTHOR_SUPPLIED_FIGURES.json) covers all six images; earlier five-image receipts have historical scope.

The original 14-image top-level `outputs/figures/` inventory remains unchanged and historical. It is separate from the expanded canonical inventory. See the [figure reconciliation](FIGURE_RECONCILIATION_AND_REPLACEMENT.md) and [figure evidence guide](../../docs/figure-evidence.md) for provenance and metric boundaries.

The [CODE integration audit](audit/CODE_EVIDENCE_INTEGRATION.json) records the prior authentication of the separate CODE evidence package: 57 members and 46 source trace rows against original Git blobs. Those counts describe the CODE provenance audit, not the current publication ZIP sizes. Macro-F1 intervals and paired contrasts are authenticated patient-bootstrap aggregates; other macro intervals remain unavailable. Confusion-derived metrics were recalculated, while private-score AUROC/AP and bootstrap bounds were authenticated through sealed receipts. See the [CODE evidence README](supplementary/CODE_EVIDENCE_README.md).

[Supplementary Table S1](supplementary/SUPERVISION_AND_CLASS_EVIDENCE.tex) and its companion CSV distinguish global logits, recovered supervision, published specialist results, and later experimental evidence for eleven endpoints. Additional CSVs record partition evidence states, morphology formula/code checks, and five verified model-artifact download URLs. These aggregate evidence records do not establish complete historical training lineage.

## Compilation, Licensing, and Verification

Extract the complete source ZIP, open `manuscrito.tex` as the main file, and use pdfLaTeX in Overleaf, or run pdfLaTeX twice locally to resolve cross-references. The bibliography is embedded in the source. Keep `Definitions/`, section inputs, tables, and PDF figures together. The prior local compile/render review is recorded in the [layout QA report](MANUSCRIPT_LAYOUT_QA_REPORT.md); the hosted Overleaf service was not invoked for that review.

The [official MDPI template](https://www.overleaf.com/latex/templates/mdpi-article-template/fcpwsspfzsph) identifies MDPI as author and CC BY 4.0 as its license; [MDPI's LaTeX guidance](https://www.mdpi.com/authors/latex) links the official template. The retained supplied June 2026 class includes local draft-status wording changes. No byte-equivalence to the current publisher template is asserted. See [`latex/THIRD_PARTY_NOTICES.md`](latex/THIRD_PARTY_NOTICES.md) for attribution and retained third-party notices; these dependencies are not relicensed under the repository's Apache-2.0 code license. Original inputs remain preserved separately.

The [change ledger](MANUSCRIPT_CHANGE_LEDGER.md) and [editorial plan](audit/EDITORIAL_PLAN.md) describe the completed revision and remaining scientific boundaries. The [publication validation record](audit/PUBLICATION_VALIDATION.json) confirms the clean 50-member ZIP build, matching PDF drawing streams, all six supplied-image pixel checks, archive/source hashes, seven passing publication tests and repository-wide Ruff. The full repository suite has 782 passing tests and eight failures/errors; the isolated baseline has the same eight failures/errors, so the suite is not presented as fully passing.
