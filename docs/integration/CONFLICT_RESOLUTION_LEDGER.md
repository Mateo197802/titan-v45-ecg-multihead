# Conflict and compatibility ledger

| Integration | Conflict or regression | Resolution and proof |
|---|---|---|
| #10, #5 | Optional h5py minimum: 3.13 versus 3.10 | Kept the stricter 3.13 floor already introduced for SPH; no model, feature or threshold edit. |
| #5 | Shared figure audit had parallel allowlists | Combined both exact allowlists and retained every per-file, manifest and renderer check. All pre-existing figures are byte-identical. V4.6 figures remain in their own directory. |
| Combined CI | Seven reviewer scripts developed import-order diagnostics once Stage A modules were available | Ruff import reordering only. Source blobs executed historically remain available under their original commits and sealed packets. |
| #12 readback | Archived scripts and current lint-normalized scripts are intentionally different | Verify archived source bytes against the immutable packet, then independently require exact equality for all published result and report bytes. Neither packet nor any tolerance was changed. |
| CODE-15% readback | Public checkout intentionally lacks private score arrays | Verify on CEDIA, not by copying arrays into GitHub. The original private evaluator and delivery receipts remain authoritative. |

Workflow kept full Git history, Python 3.10-3.12, reviewer checks, adaptation
checks, recovery checks, package build, and aggregate figure generation.
