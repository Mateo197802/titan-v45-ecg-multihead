# Expanded Life revision — life-4620846

The canonical manuscript is `latex/manuscrito.tex`, with editable section inputs, tables and vector figures. This expands the authenticated 26-page original and preserves its title, scientific section sequence, verified selected-development results and A1–A10 subjects. Dedicated CODE methods, results and discussion inputs add a completed patient-held-out evaluation after supervised adaptation: 4,921 ECGs from 3,891 patients, five endpoints, macro-F1 60.27% (95% CI 56.46–63.41). The candidate failed promotion safeguards. Independent institutional and P4 external validation remain unperformed.

The user expressly requested LaTeX only. Final delivery comprises the compiled PDF, complete Overleaf source ZIP, aggregate supplement, editable `.tex` response drafts and cover letter, and verification reports. Word generation is discontinued.

The public source history retains the existing PR18 work and the current main evidence. The complete local submission ZIP additionally contains the legitimate original MDPI class and dependencies. Those journal template files, compiled journal documents, private reviewer correspondence and source ECG/record-level data are excluded from public source publication.

To compile the complete package, open `manuscrito.tex` in Overleaf and use pdfLaTeX, or run pdfLaTeX twice locally. The original `Definitions/mdpi.cls` is required. `build_revision.py` compiles without regenerating or overwriting scientific content; its optional `--bundle` argument supports a local Tectonic bundle.

To regenerate baseline figures, run `scripts/build_figures.py` in the repository using NumPy 2 or newer and Matplotlib. It reads pinned archived prediction CSVs locally, checks the primary counts/F1 and exports aggregate recalculations only. It retains the two byte-identical CODE aggregate figures from `docs/external_evidence/figures`. The figure manifests cover all 18 figures. No model training, waveform inference or individual-record export is performed.

The supplied evidence ZIP is byte-identical to the public `docs/external_evidence` package. Its standalone verifier passed all 57 members and 46 source trace rows against the original Git blobs. See `audit/CODE_EVIDENCE_INTEGRATION.json` and `supplementary/CODE_EVIDENCE_README.md`. Macro-F1 intervals and paired contrasts are authenticated patient-bootstrap aggregates; other macro intervals are unavailable. Public confusion-derived metrics were recalculated, while private-score AUROC/AP and bootstrap bounds were authenticated through their sealed receipts.

See the change ledger, figure reconciliation, layout QA report and scientific QA JSON. Reviewer reconciliation and response drafts remain in the local author delivery. Missing original reviewer reports prevent guaranteed verbatim-report reconciliation; R1-1 and independent portions of R2-4a remain scientifically open.

A Spanish [technical decision and results summary](RESUMEN_TECNICO_Y_RESULTADOS.tex) documents the evidence used, the scope of the CODE comparison, the principal positive and negative findings, and the checks performed. It is a standalone LaTeX companion; compile it separately from `latex/manuscrito.tex`.
