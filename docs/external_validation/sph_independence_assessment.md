# SPH source-transfer independence assessment

The [SPH dataset paper](https://doi.org/10.1038/s41597-022-01403-5) identifies
Shandong Provincial Hospital as the acquisition institution. This is not
an explicitly named institution in the known P6/P8 or P4 development cohorts.
A source-name/identifier search of the public baseline `2677a33` and retained
local historical logs and manifests found no Shandong Provincial Hospital,
Figshare collection 5779802, signal item 17912444 or dataset paper DOI.
Absence of a name is not evidence of absence of the records.

| Historical phase | Current evidence | Remaining risk |
| --- | --- | --- |
| Backbone pretraining and V3F/V3AG adjustment | Checkpoint metadata and partial runtime/recovered source. | Full record/patient manifests and source lists missing; earlier data reuse not excludable. |
| Rhythm specialist | V3P manifest reference names V3J plus INCART/SVDB virtual windows; V3H explicitly monitored. | Missing historical manifest bytes and exposure inventory. |
| Pathology specialist and P4 calibration | V3M/PTB-XL split and internal panel paths in the checkpoint/log. | Full historical manifests and cross-stage patient overlap not certified. |
| Optuna and checkpoint selection | Partial V3C summary/trials; P6/P8 development selections and logs. | Original trial database, splits and exact promotions not recovered. |
| Development evaluation | Retained P6/P8 and P4 manifests, source audits and release hashes. | Source names alone do not establish uniqueness; Chapman/Ningbo duplicates already documented. |

## Bounded Retained-Source Signature Screen

CEDIA SLURM job `32633` completed at commit `ca6df11212cc3af9d19a7361bcc43eeffd70d899`
in 4m49s. It compared all 25,770 SPH records against the 2,193 waveforms in
the retained Chapman/Shaoxing/Ningbo package and 733 PTB-XL fold-10 waveforms.
The preregistered first-10-second, 12-by-1,250, per-lead-standardized,
0.001-quantized signature screen found zero cross-source candidate groups and
zero technical failures. The aggregate SHA-256 is
`6b290dd80d9d30aa0758aa16e7ac3963b950894ad43d501236804637dd9f47d8`; the
staging receipt SHA-256 is
`a117e0ed4df666ff3267120e7beb0070dcea1b3baefad0c0f56859615d5f329f`.
The candidate-link file remains private in CEDIA and contains no rows.

This is a bounded exact-signature screen, not a patient-identity match or a
complete near-duplicate search. It does not compare the unavailable historical
V3F/V3AG pretraining and fine-tuning inputs, and it cannot certify full
historical independence. Do not infer a match or independence from patient
strings across institutions.

Permitted description with incomplete historical lineage: **evaluation of
transfer to a distinct hospital source, with historical traceability limitations**.
Do not describe it as fully certified independent, or as a prospective or
clinical assessment. Do not reselect the models or alter thresholds on SPH.
