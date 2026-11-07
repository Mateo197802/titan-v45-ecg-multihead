# ECG-Associated AF Reference Contract

This audit concerns the AF flag stored with an ECG, not incident AF, first diagnosis, disease onset or a longitudinal event. The retained tables contain no evidence establishing those temporal endpoints. The [official Challenge resource](https://physionet.org/content/challenge-2020/1.0.2/) describes record-associated diagnosis codes and uses164889003for AF;426783006is the normal-rhythm code in the retained source contract.

Across1,643P6rows and2,193P8rows, there are390AF-reference-positive rows in each profile. Every AF flag agrees with the presence of164889003in the same row's saved `dx_codes`. There are no missing/non-numeric code rows or AF-flag disagreements in these retained fields. P6 is a conditional subset, so these counts must not be added as780independent observations.

| Literal source group | P6 rows | P6 AF references | P8 rows | P8 AF references |
|---|---:|---:|---:|---:|
| chapman_shaoxing | 1514 | 373 | 1879 | 373 |
| codetest_zenodo_3765780 | 19 | 0 | 167 | 0 |
| data_test | 63 | 13 | 84 | 13 |
| training/cpsc_2018 | 5 | 0 | 10 | 0 |
| training/cpsc_2018_extra | 8 | 0 | 8 | 0 |
| training/georgia | 6 | 0 | 9 | 0 |
| training/ningbo | 10 | 0 | 13 | 0 |
| training/ptb-xl | 18 | 4 | 23 | 4 |

One retained `data_test` record has both AF and normal-rhythm codes. P8 retains both accepted references. P6's declared class set excludes NSR; that does not resolve the underlying co-occurrence clinically. No record is silently removed, relabeled or adjudicated by this audit. Source strings are not proof of independent institutions; `data_test` is a mixed local directory label.

This is agreement between retained code and reference fields, not proof that every original source diagnosis is correct or independently re-read. The separate84-record upstream-header audit checks those records' diagnosis-code sets; it must not be expanded into a claim that all2,193reference diagnoses were clinically verified. Previous AF diagnosis, anticoagulation, symptoms and timing are not established here.

Reproduce the complete aggregate audit without exporting record identifiers:

```bash
python scripts/evaluation/audit_af_reference_contract.py \
  --output /tmp/af-reference-consistency.json
```

The [machine-readable result](../outputs/results/revision_20261029/af_reference_consistency.json) contains per-source counts, input fingerprints, overlap counts and explicit false flags for clinical readjudication, incidence, first diagnosis and independent validation. New temporal or clinical claims would need a different reference contract and study; bibliography alone cannot supply the missing measurements.
