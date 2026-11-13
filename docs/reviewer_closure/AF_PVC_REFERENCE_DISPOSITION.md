# R1-3 and R2-5: AF and PVC reference units

This is an evidence disposition, not an editorial response or a clinical
diagnosis. A record-associated ECG statement is distinct from a longitudinal
event or a per-beat annotation.

## AF: recorded code, not incident disease

The [retained reference audit](../af-reference-contract.md) checks the AF flag
against code `164889003` in the same saved record. On this audit the published
script was rerun against the archived prediction CSVs: all 1,643 P6 and 2,193
P8 rows matched their retained code fields, with 390 positive reference rows
in each profile and no unresolved code rows or flag mismatches. P6 is a subset
of P8; those 390 counts must not be added as independent cases. One source row
contains both AF and normal-rhythm codes; the audit retains the co-occurrence
rather than adjudicating it.

This confirms agreement between two retained fields, not that every diagnosis
was independently adjudicated. The 84-record upstream-header comparison has
its own limited scope and does not validate all 2,193 clinical references.
The available data do not establish previous diagnosis, onset or timing of a
first event. Thus incident AF, first diagnosis and prognostic claims require a
longitudinal reference, patient timeline and a separately defined study; they
cannot be obtained by wording or bibliography alone.

## PVC: ECG-level statement, not beat detection

The frozen SPH [protocol](../../configs/external_validation/sph_frozen.json)
maps code 60 to a ventricular premature-complex statement for both P6 and P8.
The [aggregate](../../outputs/results/external_sph/sph_aggregate_32669.json)
contains 1,067 positive and 24,703 negative *recorded-statement* comparisons
for each profile. The absent-statement category is not adjudicated disease
absence. These are ECG-level endpoints after the declared window aggregation;
they do not measure the detection, localization or count of individual beats.

The [SPH results](../external_validation/sph_results.md) report P6 PVC F1
54.08% and P8 PVC F1 66.16% with patient-component intervals and the full
denominator. Their profiles and thresholds differ, and those numbers are not
beat-detection sensitivity. A per-beat claim requires an independently
annotated beat-level reference, timing/matching rule, explicit denominator and
an appropriately designed evaluation, none of which is established by these
record-level results.

The manuscript can later describe these bounded endpoints and limitations;
retiring incident-AF or beat-level claims does not itself perform the missing
studies. Clinical interpretation and final wording require author review.
