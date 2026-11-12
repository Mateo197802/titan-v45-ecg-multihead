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
| PTB Diagnostic clinical territory vs healthy control transport | SLURM 33718 | 1ca453f0d4ba1a4438a3c6e8873242444c6bb755 | Protocol f37f6ca; score all source ECGs before reference join; original P4 and separately trained 33390 heads, no refit |

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

The LUDB score job completed `0:0` in 6:39 and [sealed 200/200 ECGs
in every profile](../../outputs/results/reviewer_closure_experiments/ludb_scoring_receipt.json).
The label-blind policy produced 152 acceptances, 48 abstentions and
zero technical failures. These are route counts, not reference-based
performance or independent historical validation. The measured tensor
flow is in [the morphology audit](MORPHOLOGY_REPRODUCIBILITY_AND_ABLATION.md).

The completed LUDB evaluator 33699 used a parser that did not split
newline-delimited annotations within a CSV cell. It undercounted several
explicit diagnoses compared with the publisher's data description, so
its aggregate is superseded (native SHA-256
`12ad265b5e9bd4a455c20aa2f46362a9beeface1831d1ffd731cb9fbf09bc47a`).
The correction is limited to source grammar: splitting lines, retaining
AFIB when explicitly qualified by aberrant conduction, and naming
compatible rhythm negatives accurately. A wandering atrial pacemaker
annotation is not electronic pacing and can leave the principal rhythm
ambiguous. No mapping from LAO to LAE, incomplete to complete block,
or unknown to negative is introduced. No score, threshold, route,
enrollment or endpoint support rule changes.

The complete PTB Diagnostic [source audit](../../outputs/results/reviewer_closure_experiments/ptb_diagnostic_eligibility_verified_v2.json)
verified all 549 publisher-checksummed headers from 290 subjects. The
[original grammar attempt](../../outputs/results/reviewer_closure_experiments/ptb_diagnostic_eligibility_superseded_v1.json)
missed the literal token `no` in the acute infarction localization field
of explicit healthy controls. The versioned correction preceded all model
scoring, rechecked the same publisher bytes, and did not recode any
unmentioned disease as negative. The 80 explicit control ECGs came from
52 subjects; positive patient supports were 27 ASMI, 30 IMI, 16 ALMI,
22 ILMI. This allowed an enriched territory/control test, not a natural
prevalence or historically independent claim.

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
