# Synthetic ECG Fixtures

Small deterministic signals for preprocessing, model-shape, Grad-CAM, and uncertainty tests.

- `synthetic_ecg_12x1250.csv`: one 12-lead, 1,250-sample signal with lead rows and time-sample columns.
- `lead_mask.csv`: canonical 12-lead availability mask for the synthetic record.
- `synthetic_labels.json`: non-performance labels used only for test plumbing.
- `synthetic_manifest.csv`: release-relative fixture manifest for unit and integration tests.
