# Optional Visual Prompts

These prompts are optional design prompts for replacing selected schematic figures with polished editorial artwork. They must not alter metrics, class contracts, source counts, or evidence hashes.

## Graphical Abstract

Create a clean biomedical graphical abstract for a modular 12-lead ECG deep-learning system. Show a 12-lead ECG input block, a harmonization/preprocessing block, a shared ResNet-1D plus Transformer encoder, then two independent specialist routes: rhythm Primary6 and pathology Primary4. Add cascade/quarantine routes for rhythm and pathology as secondary lanes. Use a white background, thin technical lines, restrained red/blue/orange accents, no patient photos, no device hardware, no legacy model names, and include only these metrics: Rhythm Primary6 95.19% accuracy and 80.09% macro-F1; Pathology Primary4 80.23% mean binary accuracy and 79.35% macro-F1.

## Specialist Cascade Figure

Create a journal-style methods diagram explaining primary, cascade, and auxiliary class contracts for ECG classification. Left side: global 12-lead ECG representation. Middle: routing logic. Right side: Primary rhythm classes AFIB, SB, STACH, RBBB, 1AVB, PVC; rhythm cascade classes NSR, PAC, Flutter, Paced; Primary pathology classes ASMI, LVH, IMI, ISC_; pathology cascade classes ALMI, ILMI; auxiliary outputs LBBB, 2AVB, 3AVB, LQTS, LAE. Use clear boxes and arrows, no decorative gradients, no hardware imagery, no old model names.

## Reproducibility Map

Create a clean reproducibility workflow diagram for a manuscript package. Blocks: frozen evidence artifacts, class contracts, generated tables, generated figures, manuscript outputs, public repository in preparation. Include SHA-256 evidence locking as a small note. Use minimal MDPI-style scientific design, high contrast, no marketing style, no claims that the repository is already released.
