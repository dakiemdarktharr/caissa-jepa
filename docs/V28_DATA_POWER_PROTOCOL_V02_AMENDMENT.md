# V2.8 data/power protocol amendment v0.2

**Status: model-blind correction after DEV01; no training authorization.** V0.1 and all failed receipts remain retained. This amendment responds only to pretraining trajectory/split feasibility, not to learned outcomes.

## Evidence prompting the amendment

`validation/V28_DATA_SPLIT_DEV01.json` records 144 project-generated trajectories (24 per game/split) from fixed seed 28094000, with a one-third phase threshold. After exact replay, symmetry/role normalization, context/target comparison, and complete legal two-ply counterfactual closure:

- 112 unique trajectories remained; 32 were duplicate symmetry/role-normalized paths.
- Connect4 4x5 had 83 train/validation overlaps, 33 train/selection overlaps, and 12 validation/selection overlaps. Five connected overlap components crossed split assignments; the largest component contained 15 trajectories and mixed all three splits.
- Positional-policy duplication left only 7 unique Connect4 selection trajectories, below the development support floor. Reversi6 retained 9 selection trajectories and showed no overlap in this small pilot, which does not establish full support or power.
- Reusing the exact same trajectories at phase thresholds 0.5 and 0.6 lowered the observed Connect4 overlap count but also reduced selection support; Connect4 still failed both thresholds, and Reversi6 selection fell below the record support floor at 0.6.

This is a prefit split failure, not a model result. The complete generated data and manifest stay ignored under `chess_data/v28_data_dev01/`; tracked receipt pins artifact hashes and counts. No learned model, checkpoint, power estimate, or JEPA/baseline comparison exists.

## Required v0.2 corrections

1. Make the trajectory-to-split rule component-first. Build the transitive graph over exact raw, role/symmetry-normalized, context/target, and full legal reply-closure keys before assigning any trajectory component to a split. A component may not be divided across train, validation, selection, or locked-final.
2. Preserve family holdouts at component level. If a component contains trajectories from a policy family that must be held out, quarantine the whole component from training, or fail the family-holdout gate. Never split or filter individual roots after model outcomes.
3. Increase positional-family behavioral diversity with a versioned stochastic policy definition and test its seat-symmetric behavior. Do not count seed changes alone as independent opponent families. Pin implementation hashes and randomization before the next run.
4. Run a new model-blind DEV02 support/overlap pilot at a fixed scope and episode quota. Report every component's source-family/split memberships, not just the largest sizes. Require enough independent components and positions in every game/split after component assignment.
5. Retain the one-third phase threshold for this next pilot. The 0.5/0.6 sensitivity results are failed exploratory attempts and do not authorize choosing a new threshold by whichever happens to pass. A later scope change requires a scientific rationale and a fresh version before generating or inspecting its outcomes.

## Stop rule

Do not train if component-first splitting leaves fewer than the predeclared trajectory/root/H2 support, if the held-out policy families connect to training components, if either game has persistent cross-split keys, or if the model-blind power estimate exceeds available local compute. In that case, change the admitted game/scope or pivot the claim before training, then create another versioned protocol and fresh receipts. A split audit that fails may not be repaired by removing only inconvenient positions or trajectories.

## Interpretation boundary

DEV01 and its phase sensitivities are development feasibility evidence only. They do not measure JEPA representation quality, planning performance, opponent response prediction, game strength, exploitability, transfer, novelty, or publication readiness. Passing a future data gate still would not prove superiority; it only permits the separately reviewed training experiment.
