# PR #11 and #15 corrective experiments

- [PR #11 recovery evidence](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/4fddf0de37c0a5768dd39994cdcfdf283dfde131/docs/performance_recovery/FINAL_MODEL_TECHNICAL_ASSESSMENT.md):
  14 development fits. CODE + Chapman improved validation AUPRC but
  reduced F1 and failed four safeguards. Platt-only had the best F1 but
  failed SB. The report links negatives, curves, hashes and jobs.
- [PR #15 corrective evidence](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/732ecb1c8e697997cdedf85f67db70d38bd765ed/docs/performance_recovery/CORRECTIVE_TECHNICAL_ASSESSMENT.md):
  six development fits; +0.002792 paired validation macro-F1,
  95% CI [-0.013190, +0.021799]. Only one of three CODE-only seeds
  passed all class safeguards. A CLI failure and recovery are retained.

Both use 3,088 CODE validation ECGs, not the 4,921 reserved ECGs.
Their Chapman/CPSC evidence is diagnostic; neither authorizes promotion.
