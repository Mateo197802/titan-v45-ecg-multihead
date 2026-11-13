# SPH V1 acquisition audit

Status: source metadata verified; no model results. The acquisition does not
authorize inference or establish independence. See the [primary paper](https://doi.org/10.1038/s41597-022-01403-5)
and the [versioned Figshare collection](https://doi.org/10.6084/m9.figshare.c.5779802.v1).

The Figshare API labels each dataset item below CC0. The paper has separate
article terms. Signals, private processing receipts and row-level predictions
are not included in this repository. The published cohort count is 25,770 ECG
from 24,666 patients, not a local integrity finding.

| Item | Version and file ID | Bytes | Figshare MD5 |
| --- | --- | ---: | --- |
| [Signals](https://doi.org/10.6084/m9.figshare.17912444.v1) | V1, 32630684 | 2281799680 | `0beef976f54cf0a95fac9f45bb157950` |
| [Metadata](https://doi.org/10.6084/m9.figshare.17912441.v1) | V1, 34793152 | 999219 | `8ef8e8789059a585c89c5302c7891909` |
| [Dictionary](https://doi.org/10.6084/m9.figshare.17912507.v1) | V1, 32630954 | 1839 | `9fafec6cc6e1ef8117e2964116654d05` |

Figshare reports the signal file as `application/x-tar` despite the
`.tar.gz` suffix. The staging job validates exact sizes and publisher MD5,
then measures SHA-256 and inventories the archive without extracting it. The
actual archive format and HDF5 structure must be checked on the bytes before
any extraction, even if the MIME and filename agree. Acquisition is separate
from any cohort-label join or model execution.

## Native acquisition receipt

CEDIA SLURM job `32615`: `COMPLETED 0:0`, elapsed 3m47s. All three exact
byte lengths and publisher MD5 digests passed. The signal archive is
**POSIX TAR (GNU), not gzip**; the native listing counted 25,771 members,
including directory entries. This is not yet an HDF5-record integrity count.

| File | SHA-256 measured on CEDIA |
| --- | --- |
| `code.csv` | `4d22759fd19d37133c78d439a5726f9e0bc412cc17483c424926ce9abb33c8fc` |
| `metadata.csv` | `c6f8dc5197758a3970aae554f8b6ee884d96656b121879bc0eb1adf367ea6d86` |
| `records.tar.gz` | `cebad89d7d25663272eeb45545712d76302d334bb107cdc23fd15390c9194e55` |

The publisher [Python example](https://doi.org/10.6084/m9.figshare.17914088.v1)
reads the HDF5 dataset named `ecg`. It does not document a conversion to mV.

The first inventory job, `32616`, failed before any HDF5/model output
because the parser rejected repeated primary codes. A separate metadata
inspection found 47 repeated-primary occurrences and no unknown primary
or modifier in the inspected fields. The reader now preserves all
occurrences (including distinct modifiers), counting primary support once
per record. This is a parser correction, not a label remapping or exclusion.

## Full source-only inventory

Job `32617` completed `0:0` in 2m51s at commit `f6e27fa`. The
[aggregate inventory](../../outputs/results/external_sph/source_inventory_32617.json)
has SHA-256 `8321abf1d91f0a97ae65b8e9d3a47ba4f5460055ac7780fd84ad2cc86efd2cf7`.
It accounts for **25,770** HDF5 records with matching metadata,
**24,666** source patient IDs, **1,066** with more than one ECG,
no unreadable arrays, no wholly flat leads, and **168 exact waveform
duplicate groups**. The decoded arrays are float16, with 5,000–28,000
samples per lead. The parser retained 47 repeated primary occurrences
across 44 ECGs and counted each code once per ECG.

Exact duplicates here are identical numerical arrays within SPH, not a
cross-source or cross-patient match finding. Check duplicate groups for
patient and label overlap before freezing the analysis unit. The aggregate
contains neither patient/record identities nor model scores. These are
inventory and annotation counts, not performance results.
