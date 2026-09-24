# Figure Evidence And Limits

## Included Evidence

`outputs/figures/` contains only the 14 PNG images referenced by the submitted manuscript. `figure_manifest.json` records their names, ZIP source paths, and SHA-256 hashes. The manuscript PDF, TeX source, and source ZIP are not committed. The verifier checks the exact image set and hashes; when given the original ZIP, it also checks the archive hash, TeX references, and byte-for-byte equality.

The figure generator still produces development figures for tests, but those are written to a temporary directory and are not the submitted manuscript assets. The committed tables and external-development evidence do not independently reproduce model training, establish that the upstream raw ECG cohort is complete, or validate a manuscript claim beyond the documented metric/profile contract.

## Attribution Illustration

The development-only `fig15_gradcam_contract` illustration is drawn from `data/fixtures/synthetic/synthetic_ecg_12x1250.csv`. Its overlay is a normalized signal-slope/amplitude heuristic, not a model activation, class-conditioned explanation, Grad-CAM result, real patient ECG, or clinical evidence. It is not one of the images published with the manuscript. Actual model Grad-CAM is generated separately by `scripts/evaluation/generate_gradcam.py` and requires the specified model and input artifacts.

## Missing Publication Material

The full manuscript, its bibliography, and the former literature-screening file `MANUSCRIPT/literature/studies.csv` are not included in this repository copy. Consequently, the context/evolution schematics are conceptual and are not a substitute for cited related-work evidence. The two dataset-descriptor citations in the README and `data/licenses/` can be checked independently; a completeness, accuracy, or recency review of the manuscript's other references is not possible from this repository.

## Reproduction Boundary

The repository supports integrity verification of the 14 committed manuscript PNGs. It does not regenerate those source images from the repository alone, rerun the full training pipeline, or recreate source-cohort assembly. Those broader claims would require the original manuscript package, exact training code/configuration, environment lock, source data access/version manifests, checkpoints, random-state records, and end-to-end run logs for the reported release.
