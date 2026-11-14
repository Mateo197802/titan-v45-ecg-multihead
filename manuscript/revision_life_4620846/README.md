# Expanded Life revision — life-4620846

The canonical manuscript is `latex/manuscrito.tex`, with six editable section inputs, tables and vector figures. This expands the authenticated 26-page original and preserves its title, scientific section sequence, verified selected-development results and A1–A10 subjects. Independent external evaluation is unfinished and contributes no performance results.

The user expressly requested LaTeX only. Final delivery comprises the compiled PDF, complete Overleaf source ZIP, aggregate supplement, editable `.tex` response drafts and cover letter, and verification reports. Word generation is discontinued.

The public source history retains the existing PR18 work and the current main evidence. The complete local submission ZIP additionally contains the legitimate original MDPI class and dependencies. Those journal template files, compiled journal documents, private reviewer correspondence and source ECG/record-level data are excluded from public source publication.

To compile the complete package, open `manuscrito.tex` in Overleaf and use pdfLaTeX, or run pdfLaTeX twice locally. The original `Definitions/mdpi.cls` is required. `build_revision.py` compiles without regenerating or overwriting scientific content; its optional `--bundle` argument supports a local Tectonic bundle.

To regenerate figures, run `scripts/build_figures.py` in the repository using NumPy 2 or newer and Matplotlib. It reads pinned archived prediction CSVs locally, checks the primary counts/F1 and exports aggregate recalculations only. It does not train models, perform waveform inference or export individual records.

See the change ledger, figure reconciliation, layout QA report and scientific QA JSON. Reviewer reconciliation and response drafts remain in the local author delivery. Missing original reviewer reports prevent guaranteed verbatim-report reconciliation; R1-1 and independent portions of R2-4a remain scientifically open.
