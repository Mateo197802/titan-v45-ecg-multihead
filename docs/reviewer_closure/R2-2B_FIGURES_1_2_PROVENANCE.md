# Reviewer 2.2b: Figures 1 and 2 provenance record

## Source archive

The author-supplied `life-4620846 (1).zip` was byte-identical to the previously audited `life-4620846.zip` and to the archive hash recorded by `outputs/figures/figure_manifest.json`:

```text
SHA-256 36c1c6db30a759ef9d349ae2e545577cfd7ce3af91a3b97fb459380113f294a8
```

The archived TeX file is `mdpi_Articulo/manuscrito.tex`. Its Figure 1 callout and float are at lines 148-154; Figure 2 is called out and captioned at lines 156-162. The image bytes in the archive match the hashes recorded by the repository manifest and the corresponding repository assets.

| Figure | Archive path | Repository path | SHA-256 | Bytes | Dimensions |
| --- | --- | --- | --- | ---: | ---: |
| 1 | `mdpi_Articulo/figures/fig01_graphical_abstract.png` | `outputs/figures/fig01_graphical_abstract.png` | `52401fa880a6f521490297b01d535c49e9e7e6f957ef3dea62c7d685012ef665` | 3,151,996 | 3708 x 2092 |
| 2 | `mdpi_Articulo/figures/fig02_data_processing_bias_workflow.png` | `outputs/figures/fig02_data_processing_bias_workflow.png` | `b045537dfeb3ffd0f4392f6817fd9448099b75b6119e08fc7fc58e8b492c6066` | 4,560,222 | 3708 x 2092 |

## Purpose stated in the archived manuscript

- **Figure 1** is presented as a proposed modular architecture: a 12-lead ECG enters a shared CNN-transformer backbone and branches to separate Primary6 rhythm and Primary4 pathology specialists, with uncertainty margins.
- **Figure 2** is presented as a data-curation and harmonization workflow: source aggregation, 125 Hz standardization, diagnostic-ontology mapping, and patient-level partitioning for the external-development cohort.

These are descriptions of what the archived callouts and captions say. The figure files and captions do not independently establish that every depicted operation was executed, that the historical partitions were patient-disjoint, or that the images are empirical outputs. In particular, the split and cohort claims must be evaluated against the surviving run-level evidence, not accepted from the diagram.

## Provenance boundary and disposition

This check establishes that the two PNGs are present in the supplied submitted-source archive, are byte-identical to the repository's manifested copies, and have the purposes stated in the archived TeX. It does **not** establish who created or edited them, whether any third-party assets were used, the applicable reuse permissions, or whether Figure 2 faithfully represents the executed historical pipeline. No native editable figure source or figure-specific license record was located in the checked archive/repository material.

Accordingly, R2-2b remains `ACTIVE_RECOVERY_REQUIRED` and `PARTIALLY_ADDRESSED`. Author/source-record confirmation of authorship, third-party material and permissions is still needed. Before manuscript editing, the authors must also confirm or narrow Figure 2's claims against the verified pipeline. If provenance or permission cannot be established, use an authorized replacement or remove the affected illustration rather than infer its origin from appearance.

## Reproduction

The verifier checks the archive SHA-256, TeX image references, each image's archive path and bytes, the repository manifest hashes, PNG dimensions, and the exact top-level manuscript image inventory:

```powershell
python tests/figure_evaluation/scripts/verify_figure_assets.py --manifest outputs/figures/figure_manifest.json --figures outputs/figures --root . --source-archive "<path-to-life-4620846-source.zip>"
```

The archive itself is not copied into this repository. The hash and per-image checksums allow a future holder of the same archive to verify identity without publishing the manuscript package again.
