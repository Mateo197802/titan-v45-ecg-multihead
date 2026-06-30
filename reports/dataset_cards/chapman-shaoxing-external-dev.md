# Rhythm External-Development Subset

## Source

The principal source is the Chapman-Shaoxing-Ningbo 12-lead ECG database, PhysioNet version 1.0.0. Zheng et al., *Scientific Data* 9, 136 (2022). License: CC BY 4.0. A small number of records originate from other documented external sources and are preserved with source attribution in the manifest.

## Released Scope

The Release archive contains the ECG records referenced by the public rhythm validation manifests. The Primary8 view contains 2,193 record evaluations; the Primary6 diagnostic view contains 1,643 eligible records.

## Processing And Limitations

Signals are resampled to 125 Hz and evaluated as `12 x 1250` windows with record-level aggregation. The release report lists the exact records, labels, predictions, and source counts used by the published metrics.
