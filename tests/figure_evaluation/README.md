# Manuscript figure evaluation package

This folder mirrors the figure-generation and validation contract used for the manuscript.

Contents:

- `scripts/generate_manuscript_figures.py`: manuscript figure generator copied from `MANUSCRIPT/scripts/figures.py`.
- `scripts/test_figures.py`: pytest checks for generated figures.
- `scripts/test_manuscript_outputs.py`: pytest checks for manuscript output claims and figure inclusion.
- `scripts/verify_figure_assets.py`: lightweight manifest verifier for PNG/PDF/SVG outputs.
- `tables_snapshot/`: CSV inputs used by the result figures.
- `figures_png/`: PNG snapshot of the generated manuscript figures.

Typical verification:

```powershell
python TEST\figure_evaluation\scripts\verify_figure_assets.py --manifest MANUSCRIPT\figures\figure_manifest.json --figures MANUSCRIPT\figures
python -m pytest MANUSCRIPT\tests
```

The public-repository copy follows the same structure under `tests/figure_evaluation`.
