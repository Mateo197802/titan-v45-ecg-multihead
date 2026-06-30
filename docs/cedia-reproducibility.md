# CEDIA Reproducibility

Set `TITAN_V45_DATA_ROOT` to the dataset cache outside the repository and `TITAN_V45_RELEASE_ROOT` to verified Release assets. Load the cluster CUDA/PyTorch module before installing `requirements/requirements-cedia-cuda.txt`.

The complete CEDIA run must:

1. verify every Release SHA-256;
2. verify profile and specialist contracts;
3. prove zero internal/external manifest overlap;
4. run full Primary8, Primary6, and Primary4 evaluations;
5. run Grad-CAM and MC-Dropout smoke tests;
6. write `reproducibility_report.json` with Git commit, asset hashes, environment, metrics, and verification results.

Cleanup is a separate guarded operation. It must stop while SLURM jobs are active, when a required asset is absent, when a hash differs, or when verification returns an error.
