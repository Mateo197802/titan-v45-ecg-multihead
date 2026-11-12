# Scientific closure execution register

The [protocol](PROTOCOL_FREEZE.md) was frozen on
`208f7b4abfb409d77c4a370cdb7aa768a8364b82`, before acquiring LUDB.
Protocol SHA-256:
`d4f8157e762ba411781c5a04f0b0a7a51a2ff7cd764ffe0bc2bfae1681d6ef6f`.
The [publisher archive](https://physionet.org/content/ludb/1.0.1/) was
acquired in the CEDIA private study root; its exact SHA-256 is
`d03192c7361ab5deeaba3f0d46e274b9ecb0b74c9caf8964151e20f1b5a7df06`.
The runner checks the archive and the publisher checksums independently.

| Operation | Authoritative handle | Code commit | Separation |
|---|---|---|---|
| LUDB frozen P6/P8/P4 scoring, joint routes and morphology hooks | SLURM 33697 | cb17ac132dd3242192d9996f51129a48e06b5d32 | No reference join; immutable release assets and sealed SPH policy |
| LUDB reference, support, fixed policy and previously fitted SPH head evaluation | SLURM 33699 | baceb368a08352b6ea74798f1c77159ef1ec139a | afterok:33697, native score seal verified before reading LUDB reference CSV |
| Original SPH split/cutoff read-only audit | [Native aggregate](../../outputs/results/reviewer_closure_experiments/sph_split_and_policy_audit.json) | baceb368a08352b6ea74798f1c77159ef1ec139a | Original 33362 calibration/held split and 33414 policy; no labels or new inference |
| Matched morphology statistical robustness audit | SLURM 33704 | d89dbc05c67b29d6cf7954ea2763d3b068d16775 | Sealed fit 33474 and evaluation 33596; no fit or waveform extraction |

The native reference-free SPH audit reconstructed the assignments and
cutoffs. It found zero cross-split patients, exact waveform fingerprints or
connected components. Calibration comprised 12,901 ECGs / 12,340 patients;
held comprised 12,869 ECGs / 12,326 patients. The unchanged joint cutoffs are
0.037162774801254295 for P8 and 0.014417142868041966 for P4. This proves
isolation within that SPH policy experiment, not absence of exposure
between SPH and historical model development.

The morphology robustness check repeats only the computation of the
original confusion counts and bootstrap from saved fitted arms, then adds
an explicitly post hoc clustered arm-swap test with Holm adjustment.
It must not be read as a fresh predeclared confirmatory experiment.

## Run and verify

Run launchers under SLURM on CEDIA with approved private release assets
and the dependency archive. The LUDB evaluator must use `afterok` of
its score producer and the original `joint-policy.json` from 33414.
Use the stage-A feature checkout at
`f4d6be30b0befea739cf2e35df1033230a1f5d10`, not the current experimental
branch as the scorer. Make an immutable code copy at each code commit and
seal all copied code/configuration before launch. Reuse the original 33396
private model, 33474 private features/fit, and 33596 native aggregate; do
not rerun fitting or export private rows. Each launcher writes a native
SHA-256 manifest for its outputs. Publish only validated aggregate and
receipt bytes; terminal scheduler state alone is insufficient.

The [draft PR](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/9)
targets the previous November experimental branch, not a manuscript branch.
Existing PRs are untouched. No closure decisions follow from submission alone.
