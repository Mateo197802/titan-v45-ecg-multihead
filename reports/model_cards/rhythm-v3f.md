# Rhythm V3F Branch Model Card

## Purpose

Research evaluation of rhythm classification from ten-second, 12-lead ECG windows. The branch exposes the original Primary8 contract and a separate Primary6 diagnostic view.

## Artifacts

- V3F backbone SHA-256: `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8`
- Primary8 candidate specialist SHA-256: `b30cb2bbb45f1231c93ff1c196aa966b57b49831cadb296131c0283e7b0ceb02`
- Primary6 diagnostic specialist SHA-256: `9c5a9265a7155e1206c551cc4e6d645b86363ba3dbdeb7baf7b9f173c314be3d`

## Results

Primary8 reached 90.6065% top-1 accuracy and 76.1425% macro-F1 on the released validation cohort. The six-class diagnostic profile reached 95.1917% top-1 accuracy and 80.0938% macro-F1 on its eligible records.

## Limitations

`PAC`, `1AVB`, and `PVC` have lower classwise F1 than the strongest rhythm classes.
