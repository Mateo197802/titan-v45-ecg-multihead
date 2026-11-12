# External reference contract under audit

MIMIC v1.0 supplies 18 machine statement fields (`report_0` to `report_17`), not the cardiologist free text. The candidate parser reads every field for development records; it treats only whole allowlisted lexical templates as positive or explicitly negated. It separately records historical, uncertain, ambiguous, conflicting, unmentioned, and unmapped states. Compound templates that are not implemented are masked, not treated as negative. A missing phrase and a generic normal statement do not imply the absence of every pathology.

| Profile | Candidates for machine concordance | Not established |
|---|---|---|
| P6 | AFIB, SB, STACH, RBBB, 1AVB, PVC | Do not map flutter to AFIB, unspecified AV block to 1AVB, or incomplete RBBB to complete RBBB. |
| P8 | P6 plus PAC and explicit NSR | NSR is not Other and need not exclude all coexisting findings. |
| P4 | Exact ASMI, LVH, IMI templates, conditional on adequate two-sided support and review | ISC_ is unmapped. Historical or age-undetermined infarct is not a current positive. No clinical P4 adjudication. |
| CODE-15% | `AF`, `SB`, `ST`, `RBBB`, `1dAVb` are candidate shared columns | No PVC, PAC, or P4 truth. Do not map generic `normal_ecg` to NSR or LBBB to Other. |

No automatic output is interpreted as a clinically adjudicated diagnosis. No parser has been approved for performance evaluation: held-out labels must not be extracted before the grammar, ambiguity audit, minimum positive/negative support, exact endpoint definitions, and performance protocol are frozen. Other requires a dedicated multilabel reference, not a residual category for missing diagnoses.

## Executed development support audit

SLURM job 33293 joined all 5,770 selected development ECGs and applied the frozen [support screen](REFERENCE_AUDIT_GATE.json). Across all endpoints, the maximum explicit-negative patient support was zero in train, validation, and calibration. No endpoint passed the necessary two-sided gate. This is a result about the implemented strict reference contract, not proof that all possible references are absent from MIMIC. The 1,014 retained ECG labels were not extracted. No heads were trained and no performance result was computed. A revised machine-reference study would require an independently reviewed new contract, not relabeling missing statements or weakening the same gate after seeing these results.
