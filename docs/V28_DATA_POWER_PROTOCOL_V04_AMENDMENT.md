# V2.8 data/power protocol amendment v0.4

**Status: model-blind support amendment; no training authorization.** DEV01–DEV04 receipts remain unchanged. This version responds to a support shortfall at the fixed DEV04 candidate quota.

## DEV04 result

DEV04 used schema v04, seed `28094002`, and 48 candidate episodes per game/split. It quarantined one mixed-family component. Connect4 retained 15 train trajectories/64 records, 6 validation/45 records, and 10 selection/33 records. Reversi6 retained 72/1,469, 24/488, and 48/960, respectively. Cross-split overlap was zero among retained data, but Connect4 validation and selection both failed the predeclared 8-trajectory, 64-record, 16-H2 support floor. Only diagnostic trajectories were published. This is not evidence about learned performance.

## Frozen DEV05 change

DEV05 increases the candidate quota to 96 per game/split. Rules, two games, policy family definitions, one-third phase threshold, full two-ply reply closure, component-first assignment, 25% validation trajectory target, and support floors remain unchanged. The larger quota tests whether the observed Connect4 deficiency is simply insufficient eligible state support. The 48-episode pilot took under two minutes on the local CPU, so the 96-episode run remains within a bounded local pilot; this estimate does not authorize cloud or paid compute.

DEV05 passes only if every admitted game has at least 8 unique trajectories, 64 model-facing records, and 16 H2 records in train, validation, and selection; both train/validation families occupy both seats; every overlap component stays within one split; and no raw, symmetry/role-normalized, context, target, or full legal two-ply reply key crosses splits. A failed run publishes trajectories and diagnostics only. No further quota increase is preauthorized by this amendment.

## Stop rule

If DEV05 fails, stop this split/quota line. Preserve the receipt and either reduce the admitted game claim with a written rationale or redesign the split unit under a new protocol version before generating another pilot. No model may be fitted from an audit failure. A pass is only prefit data feasibility and still requires power analysis, objective review, and a separately frozen training plan.
