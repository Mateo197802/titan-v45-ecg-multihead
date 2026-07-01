# Manuscript figures

This folder contains the regenerated manuscript figure assets exported from `MANUSCRIPT/figures`.

Included assets:

- `fig*.png`: raster figures used for manuscript insertion and visual review.
- `fig*.pdf`: PDF versions of the same figures.
- `fig*.svg`: editable vector-style exports where available.
- `figure_manifest.json`: figure ids, captions, source files, and evidence flags.
- `optional_visual_prompts.md`: prompts used for optional regenerated visual assets.

Verification:

```powershell
python TEST\figure_evaluation\scripts\verify_figure_assets.py --manifest OUTPUTS\FIGURES\figure_manifest.json --figures OUTPUTS\FIGURES
```
