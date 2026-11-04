# Workflow audit of the released profiles

This is a score-only audit of **every record key in the union of the two
released, already-selected manifests**. It is not the original pre-selection
population, raw-waveform inference, or an independent external validation.

```sh
python scripts/evaluation/audit_saved_workflow.py --output saved_workflow_audit.json
```

The program takes identity from the manifests and predictions from the released
score columns. It never routes on a reference diagnosis, a true label, or a
saved correctness flag. A test removes all such fields and confirms identical
transitions. A separate comparison in that test confirms all reproduced
decisions against the saved P8/P4 outcomes. The audit does not use P6 to expand
coverage; P6 is a separate selected diagnostic profile.

## Measured scope

See the [aggregate report](../outputs/results/revision_20261029/saved_workflow_audit.json).
It enumerates 2,926 exact released record keys (2,193 P8 and 733 P4, no exact
path overlap). This is not a count of independent patients or unique waveforms.
P8 includes 476 NSR top-1 decisions and 58 empty-set fallbacks. P4 has 962
scored record-label pairs; just five keys have all four pathology scores.
An unscored pathology is not a negative finding. The released scores cannot
identify Other arrhythmia or Other pathologies; the audit does not impute either.

The pre-state records which branches have scores. The post-state can be
`retained`, `quarantined`, `quarantine_not_assessed`, or `no_scores`.
Computing a quarantine decision requires separate uncertainty inputs and an
explicit policy. No real, bound record-level uncertainty scores are available
in these released profiles. All 2,926 post-states are consequently
`quarantine_not_assessed`. The quarantine rate is **undefined**, not zero.
The optional private ledger contains record keys and is not a release artifact.

## Historical contrast

An audit of 11 CEDIA cache manifests found candidate lineage evidence, not the
V4.5 checkpoint's training manifests. Manual curation, validated P0 quarantine,
and Primary9 rare quarantine have 3, 3, and 4 rows, respectively. These are
selected curation records, not a complete, model-only V4.5 routing ledger.
No exact key or source-and-ID match was found against the released P8/P4
profiles for the 11 files; this is not a waveform or patient linkage check.

The cached PATHOLOGY_10 training manifest explicitly contains 244 ALMI,
271 ILMI, and 273 LAE label rows. The recovered multihead source independently
shows a seven-output pathology loss on rows with a valid pathology target,
including the auxiliary output dimensions. Neither result establishes that
those exact cached rows trained a released checkpoint. The recovered contract
places NSR in the default Primary8 set and in the rate-frequency axis; it is
not assigned to the default rhythm cascade. The distinct Primary4 specialist
does not establish deployment or performance of the three auxiliary labels.

Full historical closure still requires the original upstream population,
record-level scores and policy before and after quarantine, the inputs bound
to each training/calibration run, and the exact preprocessing source. The
available P4 replay matches saved binary decisions but does not meet strict
probability equivalence. The cache contrasts cannot resolve that difference or
substitute for the missing Optuna database.
