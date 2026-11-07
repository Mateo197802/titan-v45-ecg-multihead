# Evaluation Scripts

Entry points for internal, external-development, primary, head, cascade, uncertainty, Optuna-audit, and Grad-CAM outputs. Every result records its evaluation scope.

`evaluate_cascade.py` defaults to a contract-only inspection. Its `pathology_primary4` and `rhythm` modes require a verified release root and scratch directory and execute frozen inference. `compare_waveform_references.py` consumes the two private ledgers and writes a separate, aggregate-only matched comparison. Outputs are not replacements for canonical evidence. See the [commands and boundaries](../../docs/frozen-waveform-audit.md).
