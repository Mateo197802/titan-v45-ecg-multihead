# Optional Visual Prompts

These are reference-only design prompts. The figure generator does not read them, and generated artwork based on them is not part of the verified evidence package. Any adopted artwork must be reviewed, added as a versioned source, and recorded in the figure manifest; it must not alter metrics, class contracts, source counts, or evidence hashes.

## Graphical Abstract

Create a clean biomedical graphical abstract for a modular 12-lead ECG deep-learning system. Show a 12-lead ECG input block, a harmonization/preprocessing block, a shared ResNet-1D plus Transformer encoder, then two independent specialist routes: rhythm Primary6 and pathology Primary4. Add cascade/quarantine routes for rhythm and pathology as secondary lanes. Use a white background, thin technical lines, restrained red/blue/orange accents, no patient photos, no device hardware, no legacy model names, and include only these metrics: Rhythm Primary6 diagnostic-only 95.19% accuracy and 80.09% macro-F1; Pathology Primary4 80.23% mean binary accuracy and 79.35% macro-F1.

## Specialist Cascade Figure

Create a journal-style methods diagram explaining primary, cascade, and auxiliary class contracts for ECG classification. Left side: global 12-lead ECG representation. Middle: routing logic. Right side: Primary rhythm classes AFIB, SB, STACH, RBBB, 1AVB, PVC; rhythm cascade classes NSR, PAC, Flutter, Paced; Primary pathology classes ASMI, LVH, IMI, ISC_; pathology cascade classes ALMI, ILMI; auxiliary outputs LBBB, 2AVB, 3AVB, LQTS, LAE. Use clear boxes and arrows, no decorative gradients, no hardware imagery, no old model names.

## Reproducibility Map

Create a clean reproducibility workflow diagram for the public research package. Blocks: frozen evidence artifacts, class contracts, generated tables, generated figures, manuscript outputs (not included in this repository copy), and public repository. Include SHA-256 evidence checks as a small note. Use minimal scientific design and high contrast; do not imply that the manuscript is present or that the prompt itself proves reproducibility.
