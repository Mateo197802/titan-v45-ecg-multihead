# Dataset License And Attribution Audit

This inventory separates verified upstream terms from source identity inferred from the row manifests. It is not a legal opinion. The repository's source-code license and model-weight license do not apply to ECG data.

## Historical Rhythm Asset `v0.1.0`

The public asset `external-dev-rhythm-chapman-shaoxing.tar.zst` contains 2,193 Primary8 record rows and is not a Chapman-only cohort. Counts below are copied from `data/external_dev/rhythm/release_cohort_report.json` and the two public record manifests. They do not prove that every waveform was matched against an upstream checksum.

| Manifest source label | Primary8 | Primary6 diagnostic | Attribution and rights status |
|---|---:|---:|---|
| `chapman_shaoxing` | 1,879 | 1,514 | Chapman-Shaoxing-Ningbo, PhysioNet 1.0.0; CC BY 4.0; see the dataset card and source citation below. Exact record-to-source checksum mapping is not present. |
| `codetest_zenodo_3765780` | 167 | 19 | CODE-test, Zenodo v1.0.3, CC BY 4.0; cite Ribeiro et al. (2020) and the Zenodo record. |
| `training/cpsc_2018` | 10 | 5 | Path matches the PhysioNet/CinC Challenge 2021 training layout; CC BY 4.0 at that release; exact source checksum mapping is absent. |
| `training/cpsc_2018_extra` | 8 | 8 | Same Challenge 2021 release and limitation. |
| `training/georgia` | 9 | 6 | Same Challenge 2021 release and limitation. |
| `training/ningbo` | 13 | 10 | Same Challenge 2021 release and limitation. |
| `training/ptb-xl` | 23 | 18 | Same Challenge 2021 release and limitation; also retain PTB-XL's own citation. |
| `data_test` | 84 | 63 | **Unresolved.** No upstream dataset, version, citation, source hash, or license is identified in this repository. |

The 2021 Challenge release identifies the CPSC/CPSC-Extra, Georgia, PTB-XL, and Ningbo training directories and is distributed under CC BY 4.0. The row paths make this a plausible source attribution, but the repository does not carry upstream record checksums proving the exact mapping. Cite Reyna et al., *Computing in Cardiology* 48 (2021), DOI `10.23919/CinC53138.2021.9662687`, and the PhysioNet v1.0.3 release, DOI `10.13026/34va-7q14`.

The CODE-test Zenodo record identifies the dataset and gives CC BY 4.0 in its record metadata (DOI `10.5281/zenodo.3765780`). Cite Ribeiro et al., *Nature Communications* 11, 1760 (2020), DOI `10.1038/s41467-020-15432-4`.

**Distribution status: HOLD.** The `data_test` rows prevent this mixed-source archive from being treated as license-cleared. Resolve and document their upstream identity and rights before creating or distributing a replacement cohort. This repository update does not remove or alter the already-published GitHub Release asset.

Machine-readable counts and source status are in [`rhythm-source-attribution-v0.1.0.json`](rhythm-source-attribution-v0.1.0.json). The Chapman-Shaoxing-Ningbo and PTB-XL source terms/citations are recorded in their dedicated files. The PTB-XL Primary4 subset contains 962 panel rows and uses PTB-XL version 1.0.3, CC BY 4.0; see [PTB-XL](PTB-XL-CC-BY-4.0.md).
