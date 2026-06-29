# Rhythm External-Development Subset

## Source

The principal source is the Chapman-Shaoxing-Ningbo 12-lead ECG database, PhysioNet version 1.0.0. Zheng et al., *Scientific Data* 9, 136 (2022). License: CC BY 4.0. A small number of records originate from other documented external sources and are preserved with source attribution in the manifest.

## Released Scope

The Release archive contains every ECG record referenced by the promoted external-development rhythm manifest, not the complete upstream database. The full Primary8 view contains 2,193 record evaluations; the Primary6 diagnostic view contains 1,643 eligible records.

## Processing And Limitations

Signals are resampled to 125 Hz and evaluated as `12 x 1250` windows with record-level aggregation. Repeated checkpoint evaluation means this cohort is not untouched external-final evidence.
