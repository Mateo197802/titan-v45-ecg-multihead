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

The SPH source audit measures repeated patients and identical waveforms within
SPH; it does not compare SPH patients against unlinked identifiers from
other sources. Before interpreting results, compare waveforms against the
authorized retained releases where sample rates, lead order and units can be
harmonized, and report separately exact matches, near-duplicate candidates,
comparisons that could not be made, and historical artifacts unavailable.
Do not infer a match or independence from patient strings across institutions.

Permitted description with incomplete historical lineage: **evaluation of
transfer to a distinct hospital source, with historical traceability limitations**.
Do not describe it as fully certified independent, or as a prospective or
clinical assessment. Do not reselect the models or alter thresholds on SPH.
