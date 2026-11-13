# Specialist Stage A: Reviewer-Evidence Boundary

This experiment adds evidence about a **new** post-hoc head-only adaptation of the released V3F/V3AG representations. It does not change the historical V4.5 artifacts, original metrics, manuscript, or reviewer-response letter.

## What the experiment supports

- The published baseline heads and fixed new head candidates were run on matched eligible records under a versioned, frozen data/label/split contract.
- Aggregate split counts, per-class confusion counts, comparison metrics, code revisions and CEDIA jobs are traceable. The public result tables pass a reproducible arithmetic and identifier-column audit.
- A patient-grouped internal PTB-XL P4 comparison is available for the new experiment, with a clear macro-F1 gain and material class-specific sensitivity losses.
- Two rhythm source-transfer settings were measured, and the negative CPSC sensitivity results are retained rather than hidden.

## What it does not resolve

- It does not authenticate the original historical V4.5 training manifests, exact loader or all checkpoint-to-job edges.
- It does not establish that the frozen backbone was never exposed to the measured sources.
- Georgia/CPSC lack validated patient identifiers; exact-byte deduplication does not prove patient or near-duplicate independence.
- It does not provide independent external or clinical validation. SPH and V3H were not reused; `INDEPENDENT_EXTERNAL_VALIDATION = NOT_RUN`.
- It does not validate historical quarantine/fallback behavior, auxiliary-label supervision, reader performance, or claims that were withdrawn from the paper.
- It does not justify replacing historical V4.5 results with these post-hoc results.

The evidence may inform a future author-approved scope decision or a separately designed study. It is not a manuscript correction and does not satisfy a reviewer request for independent validation. Do not insert these findings into the submitted or revised manuscript without author approval and a fresh editorial decision about scope.
