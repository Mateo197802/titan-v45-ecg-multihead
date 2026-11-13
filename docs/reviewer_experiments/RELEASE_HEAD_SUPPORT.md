# Released backbone supervision boundaries

This read-only audit uses the exact two released backbone assets, not
the 41M experimental weights. It does not run inference or train a model.
The [aggregate](../../outputs/results/reviewer_experiments/release_backbone_head_support.json)
is reproduced byte-for-byte from the checksum-verified checkpoints and
the retained shareable evidence package; no weights, paths from
checkpoint metadata or record identities are exported.

| Scope | Direct evidence | Boundary |
|---|---|---|
| V3F backbone rhythm | The archived 16781 patch indexes P8 in both direct rhythm losses (0.70 focal BCE, 0.30 cross-entropy). The verified checkpoint declares the same eight targets and includes internal panels for them. P6 subsequently omits NSR and PAC from its reported output. | Flutter, LBBB, 2AVB, 3AVB, LQTS and Paced have no direct rhythm term in that recovered V3F stage. Neither the absence of an internal panel nor a stored score establishes the full pretraining history. NSR is normal rhythm. |
| V3AG backbone rhythm | The archived 17285 launcher sets a distinct eight-class rhythm target set and names its own training and validation inputs. The verified checkpoint declares that set and contains internal panels for Flutter (152 positive, 355 negative) and Paced (34 positive, 473 negative), plus NSR, SB, STACH, RBBB, PVC and 1AVB. All ten embedded epoch rows match the captured job log. | These are internal observation counts, not patient counts or a published rhythm specialist result for V3AG. The compound job has a nonzero scheduler exit; the backbone artifact does not prove later commands ran. The consumed record set and loaded parent bytes are not verified. |
| Pathology | Both released backbones declare ASMI, LVH, IMI and ISC_ and contain internal validation panels for them. The recovered V3F patch restricts direct pathology loss to those four; the V3AG launcher also declares Pathology4. | ALMI, ILMI and LAE are present in the global output contract and emit scores, but neither checkpoint contains an embedded validation panel for them. This does not rule out earlier supervision, prove calibrated performance or validate a route. |

For the two released states, the last-layer weight row and bias are
numerically unchanged for LBBB, 2AVB, 3AVB, LQTS, ALMI, ILMI and LAE,
whereas Flutter and Paced both differ. Earlier shared tensors within
both heads differ. Consequently a fixed last-layer row does not imply
fixed scores, and a changed row is not proof of labeled exposure. Both
assets declare the same parent path string; parent file identity and
the optimizer trajectory remain unverified.

Primary source: `TITAN_V45_REVIEWER_PRIMARY_DELTA_SHAREABLE.zip`,
SHA-256 `2935deb7eaaa9ba6b040610cf810ddc6e1c82a212b260170ec9b6b02e3727d07`.
Its `PRIMARY_EXCERPTS/` members are captured source/log evidence, not
proof of the exact bytes loaded by the trainer:

| Member | SHA-256 |
|---|---|
| `job16781_contemporary_loss_selection.patch_excerpt.txt` | `4352b155c2078a6c37b1ca6dc372e9397ccb58c76a101aa36178a0f15ec5c330` |
| `job17285_launcher.patch_excerpt.txt` | `5068ca8a249b9b392aad21ee336b3b412373a2cd5719d940221eb48b4a884e45` |
| `job17285_epochs_and_scheduler.txt` | `b71e48e5483f753af26e1fa4ebb416e579384e90290c2a956b682dd2bf17e88b` |

Run `scripts/evaluation/audit_reviewer_release_head_support.py` with
`--v3f`, `--v3ag`, `--source-archive` and `--output`. This establishes
the asset-specific output/supervision boundary for R2-general. It does
not replace the CEDIA Other experiments or change reviewer scores.
