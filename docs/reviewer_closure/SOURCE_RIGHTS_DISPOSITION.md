# A-02 and A-10: source identity and distribution boundary

This is a technical provenance and permissions disposition, not a legal
opinion or editorial decision. The mixed rhythm asset's name is not a source
inventory, and an accessible download does not itself establish redistribution
rights. Do not infer historical patient isolation from source identification.

## Source labels and measured identity

The P8 release manifest contains 2,193 selected record rows from multiple
manifest labels, not 2,193 records from a single Chapman institution. P6 is a
subset of those selected rhythm keys, so its 1,643 rows must not be added as an
independent cohort. [Attribution counts](../../data/licenses/README.md) and the
[machine-readable source audit](../../data/licenses/rhythm-source-attribution-v0.1.0.json)
record the literal labels; the latter is a dated snapshot whose unresolved
`data_test` field is superseded for the 84 selected files by the later audit.

The [package checksum summary](../../outputs/results/revision_20261029/packaged_checksum_summary.json)
reports exact signal-file matches to the official Challenge 2021 checksum index
for **2,026/2,193** packaged records. The remaining **167** CODE-test rows did
not match that index; this is not evidence that their signals are invalid or
that their upstream identity was checksum-verified elsewhere. Their recorded
package path prefix differs from the manifest prefix, and an identifier lookup
is not equivalent to an independent waveform checksum comparison.

For the **84** selected `data_test` signals, the
[source audit](../revision-evidence-20261029.md) reports exact matches against
the official Challenge 2020 release: three CPSC 2018, five Georgia and 76
PTB-XL. Their headers are not raw-byte matches but all 84 match after newline
normalization alone. This establishes the identified upstream bytes and the
measured representation change, not the historical download route or patient
separation. The [selected-file notice](../../data/licenses/PhysioNet-Challenge-2020-selected-data-test.md)
documents attribution, license and observed header modification for that subset.

Ten packaged signals have identical checksums in both official Chapman-Shaoxing
and Ningbo folders. Their institutional origin cannot be uniquely resolved by
that checksum. More broadly, eight literal manifest source labels do not
establish eight independent institutions or independent study populations.
The recorded exact and signature comparisons are bounded by available source
files and do not exclude overlap with missing historical training, validation,
calibration or other unexamined data.

## Access and distribution are separate

Upstream terms and citations are recorded by source in the
[data license inventory](../../data/licenses/README.md); source-code and model
licenses do not automatically license the signals. Selected-file identity and
an upstream license are not, by themselves, a package-wide review of required
notices, provenance, modifications and any other applicable conditions.

The project's existing **HOLD** on additional redistribution or replacement of
the mixed archive remains in force pending author/custodian review. The
historical v0.1.0 release already has an **already-public** asset; this HOLD
does not mean that it was withdrawn, made private, or altered by this audit.
Whether to change existing release availability is a separate author decision.
No new signal archive or record-level private inventory is published here.

## Information needed to revisit the HOLD

An author should ask the authorized project custodian for: acquisition source
and version for each archive component; upstream checksums or a documented
mapping for the 167 CODE-test signals; source-specific attribution and license
texts as received; a list of actual transformations; and written confirmation
of authority and applicable conditions for repackaging and redistribution.
If a third-party permission or correction is required after review, request it
from the identified rights holder without implying that it was granted. Ask for
inventories, hashes and conditions first, not unrestricted transfer of ECGs.

The evidence supports correcting source counts and citing the identified
selected sources. It does not support claiming an independently sourced cohort,
complete package-wide redistribution clearance or a patient-disjoint training
history. The later manuscript should state these limitations until evidence
and author review support a narrower or different disposition.
