# Manuscript change ledger — life-4620846

The current approved editorial manuscript is **Modular CNN–Transformer Specialists for Multi-Source 12-Lead ECG Rhythm and Pathology Classification**, a 45-page English **AUTHOR-REVIEW DRAFT** with 18 figures. The authenticated 26-page original remains preserved separately. The earlier 27-page correction source and subsequent intermediate builds have historical scope.

## Scientific Revision and Preserved Evidence

| Subject | Final disposition | Evidence / boundary |
| --- | --- | --- |
| Title and author metadata | Author-requested Specialists title; all seven ORCIDs and author order preserved | Paulina Vizcaíno-Imacaña at UIDE is sole corresponding author; Fernando Villalba-Meneses retains the School of Biological Sciences and Engineering affiliation; Diego Almeida-Galarraga remains last |
| Introduction and state of the art | Expanded, cross-venue and task-bounded | Prior bibliography audit checked 33 primary or repository reference records and corrected the Zhu DOI/title; conceptual comparisons do not rank unmatched studies |
| Original 17 mathematical subjects | Preserved or corrected in the scientific revision, with added metric/risk formulas | Masked focal loss, stage-dependent multitask objective, binary ECE, and MC definitions retained without unsupported execution claims |
| Dataset methods | Expanded | Source/ontology table, historical partitions, units, exclusions, and overlap limits |
| Architecture | Corrected and expanded | Two separately fitted backbones with 58,352,219 parameters each; stored 512 specialist widths; actual morphology paths |
| P6 headline results | Preserved | 95.19% top-1 accuracy; 80.09% binary-panel macro-F1; 1,643 selected ECGs |
| P4 headline results | Preserved | 80.23% mean binary-panel accuracy; 79.35% binary-panel macro-F1; 962 panel observations across 733 ECGs |
| Macro-AP | Corrected during the earlier scientific revision, then preserved through the editorial passes | Recall-weighted AP: P6 85.61%, P4 87.85%; supersedes the stale original-PDF quantities |
| June quarantine, clinical review, and improved-accuracy assertions | Withdrawn as unauthenticated | No original all-input decision ledger; threshold-empty counts do not replace it |
| Original figure purposes and duplicate panel | Reconciled into 18 unique canonical figures | Distinct rhythm/pathology classwise metrics, actual error bars/counts, internal history, and two CODE figures |
| A1–A10 subjects | Retained and corrected; artifact table is A11 | Unavailable class temperatures/margins remain unauthenticated; full artifact hashes retained |
| Completed retrospective experiments | Added with stated limits | SPH denominator contrasts, LUDB/PTB references, residual heads, morphology studies, selective policy, and partial fallback |
| Later corrective development | Inspected without promoting candidate scores into release claims | Earlier PR15/16 work integrated through PR20/22; negative promotion decisions retained |
| CODE patient-held-out evaluation | Methods, four tables, two figures, paired intervals, and endpoint failures integrated | Within-source evaluation after supervised adaptation; 4,921 ECGs, 3,891 patients, five endpoints; macro-F1 60.27% (95% CI 56.46–63.41); failed promotion safeguards |
| Independent institutional and P4 external validation | Pending and result-free | Within-CODE adaptation does not close either independent-validation gap |

## Final Editorial Passes and Artwork

A full English editorial pass was followed by a targeted 22-paragraph clarity pass. These passes preserve the numerical scientific results, equations, evaluation boundaries, limitations, and cascade, abstention, and fallback content. No new model training, waveform inference, or statistical experiment was performed for the editorial revision. The manuscript's AI-use acknowledgment remains in place, with scientific responsibility retained by the authors.

Figures 1–6 use the six supplied native PNGs, embedded losslessly in PDF without cropping, resampling, recoloring, or upscaling. Figure 5 is the supplied 1586 × 992 architecture image. Their approved PDF pages are 2, 3, 6, 8, 13, and 14. The twelve other figure pairs retain vector content and are unchanged by these image imports. The [V2 receipt](audit/AUTHOR_SUPPLIED_FIGURES.json) covers all six supplied images; earlier five-image receipts describe historical provenance. See the [figure reconciliation](FIGURE_RECONCILIATION_AND_REPLACEMENT.md).

The original top-level `outputs/figures/` inventory of 14 images remains unchanged and historical. The canonical expanded inventory is [`latex/figures/`](latex/figures/). The previous five-supplied/thirteen-vector split is superseded by the current six-supplied/twelve-vector split.

## Authorized Public Package and Verification Scope

The public package consists of the [45-page PDF](artifacts/TITAN_V45_LIFE_4620846_EDITORIAL.pdf), [50-member complete LaTeX source ZIP](artifacts/TITAN_V45_LIFE_4620846_EDITORIAL_LATEX.zip), and [31-member aggregate supplementary ZIP](artifacts/TITAN_V45_LIFE_4620846_SUPPLEMENTARY.zip), identified by the [publication manifest](PUBLICATION_MANIFEST.json). The source ZIP adds `THIRD_PARTY_NOTICES.md` to the 49 compilation-package files. The supplementary package includes the six-image V2 import receipt. Final delivery is LaTeX/PDF; Word generation is discontinued.

Publication of the manuscript, licensed MDPI dependencies, images, and artifacts is authorized and supersedes the earlier local-only publication convention. Legitimate `Definitions` files are included with [attribution and retained third-party notices](latex/THIRD_PARTY_NOTICES.md). The supplied June 2026 class contains local draft-status wording changes; no byte-equivalence to the current official MDPI template is claimed. Original inputs remain preserved separately.

Confidential reviewer/editorial reports, responses, cover letters, raw ECGs, individual-record data, model weights, private execution paths, and credentials remain excluded from these publication artifacts. Public distribution as an author-review draft does not imply journal submission or acceptance.

The [layout report](MANUSCRIPT_LAYOUT_QA_REPORT.md) records the successful 45-page compile/render review, all 18 figures, no overflow or missing references/glyphs, and clean-source recompilation with identical normalized PDF text. The [publication validation record](audit/PUBLICATION_VALIDATION.json) adds seven passing publication tests, matching PDF page drawing streams after clean-ZIP compilation, 102 verified staged files, and a passing Ruff check. The full repository suite reports 782 passes, four failures, and four errors; the isolated baseline reports 780 passes with the same eight failures/errors. Publication packaging introduces no additional failing test IDs.
