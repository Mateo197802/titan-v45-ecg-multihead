# Mixed-Source Rhythm External-Development Subset

## Source

The 2,193 Primary8 rows are mixed-source, not a Chapman-only cohort. The public row manifest reports 1,879 `chapman_shaoxing`, 167 `codetest_zenodo_3765780`, 63 across PhysioNet Challenge training folders, and 84 `data_test` rows. The latter have no identified upstream dataset, version, citation, checksum, or license in this repository. The archive filename `external-dev-rhythm-chapman-shaoxing.tar.zst` is therefore incomplete and must not be read as a complete provenance statement. See the [source-level license audit](../../data/licenses/README.md) and [machine-readable source counts](../../data/licenses/rhythm-source-attribution-v0.1.0.json).

For Chapman-Shaoxing-Ningbo, cite Zheng et al., *Scientific Data* 7, article 48 (2020; DOI `10.1038/s41597-020-0386-x`) and PhysioNet version 1.0.0 (DOI `10.13026/wgex-er52`), CC BY 4.0. For CODE-test, cite Ribeiro et al., *Nature Communications* 11, 1760 (2020; DOI `10.1038/s41467-020-15432-4`) and Zenodo v1.0.3 (DOI `10.5281/zenodo.3765780`), CC BY 4.0. Challenge-folder labels match the PhysioNet/CinC Challenge 2021 training layout (Reyna et al., DOI `10.23919/CinC53138.2021.9662687`; PhysioNet v1.0.3 DOI `10.13026/34va-7q14`, CC BY 4.0); this mapping is inferred from path labels and was not independently confirmed from upstream waveform hashes.

## Released Scope

The Release archive contains the ECG records referenced by the public rhythm validation manifests. The Primary8 view contains 2,193 record evaluations; the Primary6 diagnostic view contains 1,643 eligible records. Source counts by profile are in `data/licenses/rhythm-source-attribution-v0.1.0.json`.

## Processing And Limitations

Signals are resampled to 125 Hz and evaluated as `12 x 1250` windows with record-level aggregation. The release report lists records, labels, predictions, and source labels used by the published metrics. Its source labels are not a full upstream identity/hash map. **Distribution status: HOLD** until the 84 `data_test` records are traced and their rights established.
