# Final technical evidence closure for V4.5

**Scope:** technical and forensic disposition of the 48 Round 1 review/audit
observations. **The submitted manuscript and response letter were not edited.**
This file is not an editorial decision and does not represent author or
coauthor approval.

## Current evidence state

The [detailed matrix](REVIEWER_48_DETAILED.md) contains all 48 observations,
the separate technical and reviewer-satisfaction statuses, evidence links,
observed populations/results, recovery ceilings, experiments still required,
future editorial actions and scientific risks. The source comments are
paraphrased from the author-supplied platform transcript. The separately
attached PDF is a manuscript draft, not the reviewer report. Twelve `A-*`
items are project audit observations, not peer-review comments.

| Technical status | Count | Meaning |
| --- | ---: | --- |
| `VERIFIED_COMPLETE` | 2 | Bounded evidence is complete for the stated audit scope. |
| `EXPERIMENT_COMPLETED_WITH_LIMITATIONS` | 3 | New transfer/coverage or replay evidence was executed, with material limits. |
| `VERIFIED_WITH_LIMITATIONS` | 9 | Only the restricted interpretation stated in the matrix is supported. |
| `EVIDENCE_CEILING_REACHED` | 6 | Bounded recovery found no qualifying evidence in inspected sources. |
| `ACTIVE_RECOVERY_REQUIRED` | 2 | A concrete provenance/source request remains actionable. |
| `NEW_EXPERIMENT_REQUIRED` | 3 | A missing study is required if the corresponding claim is retained. |
| `MANUSCRIPT_ONLY_PENDING` | 23 | No further technical work is required for the bounded point, but author-approved editing/assembly remains. |

| Reviewer-satisfaction status | Count | Meaning |
| --- | ---: | --- |
| `FULLY_ADDRESSED_BY_EVIDENCE` | 0 | No peer-review observation is declared fully satisfied at this stage. |
| `PARTIALLY_ADDRESSED` | 12 | Some requested evidence exists, but a material part remains. |
| `ADDRESSED_BY_SCOPE_RESTRICTION` | 0 | No restriction has yet been implemented in the manuscript. |
| `NOT_SATISFIED` | 3 | The requested class/quarantine evidence or experiment is absent. |
| `EDITORIAL_ACTION_ONLY` | 21 | The remaining action is author-approved text, reference, table, figure or supplement work. |
| `NOT_APPLICABLE_AUDIT` | 12 | Internal audit items, not reviewer comments. |

The reviewer-satisfaction column is not a probability of acceptance. Even
`EDITORIAL_ACTION_ONLY` means the change is still pending; it is not a claim
that the reviewer has accepted a draft or that an editor has approved a
reduced scope.

## Evidence executed and preserved

- The frozen SPH transfer covers 25,770 ECG from 24,666 source patients,
  25,770/25,770 records per P6/P8/P4, zero technical exclusions and zero
  inference failures. It contains 14 reference-compatible statement-level
  endpoint comparisons, patient-component intervals and duplicate sensitivity.
  Historical V3F/V3AG exposure is incomplete, so complete independence is not
  certified. See [SPH delivery audit](SPH_DELIVERY_AUDIT.md) and
  [all-input flow coverage](ALL_INPUT_FLOW_COVERAGE.md).
- The selected-development key counts are 2,193 P8 (including all 1,643 P6
  keys) and 733 P4 ECG across 962 binary panel rows; their verified P8/P4
  record-key union is 2,926. These are not patient counts or the historical
  preselection universe.
- SPH no-threshold behavior is measured: P6 has 16,785 empty sets, P4 8,343,
  and P8 applies a forced top-1 fallback on 801 records. Quarantine remains
  `not_assessed`, never zero. No `Other` performance or human review is inferred.
- AF reference flags match retained code fields on the selected P6/P8 rows,
  but no longitudinal incident-AF evidence exists. PVC SPH endpoints are ECG
  statement comparisons, not beat detection.
- P4 reconstructed replay matched 962/962 saved panel decisions but had a
  maximum probability difference of `0.0006194115`, greater than the fixed
  `1e-5` criterion. The exact historical loader remains unavailable.
- Five physical model checkpoint hashes are measured in the separate A10
  correction evidence. The original Optuna DB and generic prediction artifact
  remain unverified; do not assign them fabricated hashes.
- Model/backbone relationships, selected cohort counts and released metrics
  are linked in the evidence map. Synthetic Grad-CAM/uncertainty smoke tests
  are not clinical explanation or reader-study evidence.

## Irreducible or unsatisfied points

1. **Historical parent population and exclusions:** no preselection V3H/V3S
   parents, authentic June full-flow denominator or complete quarantine ledger
   were recovered in the examined sources. SPH coverage is a later separate
   source, not a substitute.
2. **Historical split and exposure independence:** selected PTB-XL fold
   membership does not prove the published training/checkpoint/calibration
   isolation; full source lineage is missing.
3. **Auxiliary supervision and Optuna lineage:** output tensors and a few trial
   records do not prove per-class checkpoint-linked training or trial-to-weight
   promotion.
4. **Strict replay equivalence:** the historical loader hash is missing, and
   P4's fixed numerical tolerance fails despite exact decision agreement.
5. **Quarantine, `Other`, clinical AF and beat-level PVC:** none is validated
   by fallback counts, empty sets, code presence or ECG-level statement scores.
6. **Interpretability and readers:** no verified clinical Grad-CAM validation,
   reader experiment, human review outcome or patient benefit is available.
7. **Data rights:** additional redistribution of the mixed archive is on HOLD
   pending source-specific provenance and license-holder confirmation.

These limits may be narrowed in the future manuscript, but narrowing language
does not mean the original experiment was performed. If a claim is retained,
the matrix identifies the required evidence/experiment. If the evidence is
not obtainable, the corresponding claim must be removed or explicitly limited.

## Human approval boundary

No further human approval is needed for the bounded technical checks already
executed. Authors must approve the final scope, claims retained/withdrawn,
reference selection, rights statements, figure and supplement package, and any
new clinical or reader experiment. Only the corresponding author can approve
the actual journal response and submission on behalf of the author group. This
technical closeout must not be sent as an editor response without author review.

## Reproducibility gates

Run `python scripts/evaluation/verify_release_evidence.py`, the complete
`python -m pytest -q` suite, Ruff, the matrix integrity test, and the current
GitHub CI before treating this package as delivered. A green software check
does not establish clinical validity, complete cohort independence, author
approval or editorial acceptance. The [readiness checklist](MANUSCRIPT_READINESS_CHECKLIST.md)
contains the later manuscript-only gates.
