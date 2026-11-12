# External source provenance

This study is separate from historical TITAN V4.5 and Stage A. No source below is represented as clinically adjudicated merely because it is geographically external.

| Source | Authority and status | Use boundary |
|---|---|---|
| MIMIC-IV-ECG 1.0 | [PhysioNet release](https://physionet.org/content/mimic-iv-ecg/1.0/), DOI 10.13026/4nqg-sb35, open under ODbL 1.0 | Only public ECG headers/signals, indexes, and machine measurements. No note linkage, MIMIC-IV Clinical Database, or clinical free text. No individual rows shared. |
| CODE-15% 1.0.0 | [Zenodo release](https://zenodo.org/records/4916206), DOI 10.5281/zenodo.4916206, 18 waveform ZIPs and one index | Reserve for locked cross-source evaluation. Do not use index labels to choose endpoints or candidate models beyond the publisher's stated schema. Confirm license record and capacity before waveform acquisition. |
| CODE-II-open/test | [Primary article](https://doi.org/10.1038/s41746-026-02704-4) describes the release and blind benchmark; [author repository](https://github.com/PetrusAbreu/code-ii) still does not provide functional PhysioNet download or benchmark instructions | No download or submission verified. The [separate full-data catalog](https://researchdata.se/en/catalogue/dataset/doi-10-17044-scilifelab-32859377) is restricted and is not substituted for the announced subsets. |

On CEDIA, NFS free space is shared and is not an account quota. The study uses a dedicated private directory and CPU/GPU SLURM jobs; the effective per-account storage limit was not printed by `quota`. Full MIMIC and CODE downloads were not authorized by a measured quota. The MIMIC acquisition rule is bounded, patient-first and label-blind. See [protocol](FROZEN_EXTERNAL_EVALUATION_PROTOCOL.json).
