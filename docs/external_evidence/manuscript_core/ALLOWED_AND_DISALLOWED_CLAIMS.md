# Claim boundaries

| Supported | Not supported |
|---|---|
| Patient-disjoint held-out evaluation within CODE-15% following supervised domain adaptation | Independent institutional or adjudicated clinical validation |
| Paired comparison of three operating systems over 4,921 ECGs and five compatible reference endpoints | Pairing PR #6 with PR #10; attributing the whole gain to weight changes |
| Mean binary accuracy 0.983052, dominated by negative observations | Multiclass accuracy, global diagnostic accuracy per ECG or PPV |
| Macro-AUROC and macro-AUPRC on the five CODE endpoints | Claiming the same discrimination for P4, incident AF or all rhythm/pathology classes |
| Genuine PR points on a published 0.01 threshold grid | Creating ROC curves from AUROC or treating sampled PR area as original AP |
| Reproduction of aggregate arithmetic and verification of the historical private-score readback receipt | Fresh replay, new inference, reconstruction of all historical training or proof of independent validation |
| Higher adapted macro-F1 with AFIB/1AVB safeguards failing | Clinical deployment, promotion or replacement of the published profiles |

The later PR #11, #15 and #16 results are development-only; the #12 work
has a separate morphology/cascade scope. None replaces PR #10 or modifies
the preserved historical P6/P8/P4 figures.
