# Attribution: 84 Selected `data_test` Records

This notice applies only to the selected files identified in the [29 October provenance audit](../../docs/revision-evidence-20261029.md), not the complete mixed-source rhythm archive. `data_test` is a local directory label, not a dataset or an independent center.

## Upstream Resource

Perez Alday, E. A., et al. (2022). *Classification of 12-lead ECGs: The PhysioNet/Computing in Cardiology Challenge 2020*, version 1.0.2. PhysioNet. [DOI: 10.13026/dvyd-kd57](https://doi.org/10.13026/dvyd-kd57).

Original Challenge publication: Perez Alday, E. A., et al. (2020). *Classification of 12-lead ECGs: the PhysioNet/Computing in Cardiology Challenge 2020*. Physiological Measurement. [DOI: 10.1088/1361-6579/abc960](https://doi.org/10.1088/1361-6579/abc960).

The [upstream resource](https://physionet.org/content/challenge-2020/1.0.2/) identifies CPSC, Georgia and PTB-XL as contributing datasets. Its published license is [Creative Commons Attribution 4.0 International](https://physionet.org/content/challenge-2020/view-license/1.0.2/), including its disclaimer of warranties. Retain these credits, license and disclaimer when using that material. The code license does not replace the data license. No endorsement is implied.

## Measured Identity and Modifications

- Signals: 84 exact upstream SHA-256 matches: CPSC 2018 3, Georgia 5, PTB-XL 76. Existing [PTB-XL source credit](PTB-XL-CC-BY-4.0.md) also applies to its contributions.
- Headers: zero byte-identical upstream matches, but **84/84 identical after newline normalization alone**. Local CRLF replaces upstream LF; this finding is measured from exact text bytes, not guessed from parsed WFDB fields.
- All record-line tokens, signal-line tokens and normalized comment fields agree. No waveform, header values or demographic data are newly redistributed by this audit.
- The [representation report](../../outputs/results/revision_20261029/header_modification_summary.json) fingerprints its inputs. This is an observed difference notice; it does not identify who or which software changed the line endings.

## Remaining Distribution Boundary

The selected-file attribution and modification description are now documented. The existing mixed archive remains **HOLD**: the other source groups, original acquisition history and package-wide notices must be reconciled separately. This notice does not grant new rights, establish patient disjointness, clear the entire archive, or alter a published release asset.
