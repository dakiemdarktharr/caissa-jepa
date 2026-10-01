# V2.8 data/power protocol amendment v0.7

**Status: active strict software-gate rerun; no training authorization.** Earlier protocol versions and all diagnostic receipts remain retained.

## DEV07 execution failure

The strict-tuple DEV07 job stopped during self-play generation before creating its output directory or writing a manifest. Reversi6 can produce more than two forced passes over a game; the generator's finite-action guard incorrectly used `board cells + 2`. No DEV07 artifact or result exists. The guard now allows a conservative finite bound of `2 * board cells + 2`; seeded Reversi regression tests replay 12 deterministic games.

## Further protocol gate correction

Independent review found public `audit()` and `build_records()` still accepted caller-selected phase thresholds. That could return a passing data audit for a different sampling scope. Both now reject any threshold other than the frozen `1/3` fraction, with regression coverage. The public record builder and `audit()` return no records on any failed gate. Generation additionally requires the exact ordered split tuple and exact named quota/seed.

## Frozen DEV09 and result

DEV09 used schema `v28-procedural-trajectories-v09`, protocol ID `dev09-v1`, Connect4 gravity 6x7 plus Reversi6, 48 candidate trajectories per game/split, seed `28094007`, exact ordered splits `("train", "validation", "selection")`, and phase threshold `1/3`. Component assignment, policy families, source/seed regeneration checks, and support floors remain as in v0.5. No threshold, quota, game, split, policy, or seed variation was changed.

DEV09 passed: 3,531 audited model-facing records across 284 unique trajectories, zero quarantined components and zero cross-split keys. Connect4 support was train 72/307 records/264 H2, validation 24/128/109, selection 44/139/127. Reversi6 was train 72/1,490/1,418, validation 24/491/467, selection 48/976/928. All support, seat and provenance checks passed. The full receipt with source, dataset and artifact hashes is `validation/V28_DATA_SPLIT_DEV09.json`; raw artifacts remain in ignored `chess_data/v28_data_dev09/`.

This establishes prefit data feasibility for this synthetic two-game protocol only. `training_approved` remains false; no model was fit. Exact 6x7 root-label feasibility, power analysis, independent method review and a bounded training/selection/locked-final plan remain mandatory. A data-audit pass is not authorization to train or a performance result.
