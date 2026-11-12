# External reference contract under audit

MIMIC v1.0 supplies 18 machine statement fields (`report_0` to `report_17`), not the cardiologist free text. The candidate parser reads every field for development records; it treats only whole approved lexical templates as positive or explicitly negated. It separately records historical, uncertain, ambiguous, conflicting, unmentioned, and unmapped states. Compound templates that are not implemented are masked, not treated as negative. A missing phrase and a generic normal statement do not imply the absence of every pathology.

| Profile | Candidates for machine concordance | Not established |
|---|---|---|
| P6 | AFIB, SB, STACH, RBBB, 1AVB, PVC | Do not map flutter to AFIB, unspecified AV block to 1AVB, or incomplete RBBB to complete RBBB. |
| P8 | P6 plus PAC and explicit NSR | NSR is not Other and need not exclude all coexisting findings. |
| P4 | Exact ASMI, LVH, IMI templates, conditional on adequate two-sided support and review | ISC_ is unmapped. Historical or age-undetermined infarct is not a current positive. No clinical P4 adjudication. |
| CODE-15% | `AF`, `SB`, `ST`, `RBBB`, `1dAVb` are candidate shared columns | No PVC, PAC, or P4 truth. Do not map generic `normal_ecg` to NSR or LBBB to Other. |

No automatic output is interpreted as a clinically adjudicated diagnosis. No parser has been approved for performance evaluation: held-out labels must not be extracted before the grammar, ambiguity audit, minimum positive/negative support, exact endpoint definitions, and performance protocol are frozen. Other requires a dedicated multilabel reference, not a residual category for missing diagnoses.
