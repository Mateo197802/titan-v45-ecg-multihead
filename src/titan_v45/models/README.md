# Models

Contains the 58,352,219-parameter TITAN backbone, classwise specialists, factories, checkpoint inspection, and strict profile-bundle loading. The rhythm and pathology release lineages are loaded separately.

`frozen_pathology` verifies named release assets and scores the 670-input P4 specialists; `frozen_rhythm` verifies and loads the 681-input rhythm specialists and binds two hash-pinned signal-event functions from the recovered trainer. All checkpoint loads in this workflow are strict. Rhythm resolves conflicting width metadata from stored tensors; it never reshapes or initializes replacement weights. The [feature contract](../../../docs/recovered-feature-contract.md) distinguishes the backbone's feature probabilities from specialist scores.
