# V2.8 data/power protocol amendment v0.3

**Status: model-blind support amendment; no training authorization.** Earlier protocol versions and failed receipts remain retained. This version changes only the prefit candidate quota after the 24-per-game/split pilots failed to provide adequate Connect4 validation support.

## Evidence

- DEV02 (schema v02, seed `28094000`, 24 candidates per game/split) formed 95 assigned components and quarantined 3 components containing uniform/tactical and positional families. Connect4 retained 21 train, 0 validation, and 10 selection trajectories. Reversi6 retained 38 train, 10 validation, and 24 selection trajectories. The split audit failed and only diagnostic trajectories were written.
- DEV03 (schema v03, seed `28094001`, 24 candidates per game/split) formed 98 assigned components and quarantined 5 mixed-family components. Connect4 retained 12 train, 5 validation, and 9 selection trajectories; Reversi6 retained 36 train, 12 validation, and 24 selection trajectories. Connect4 validation was below the predeclared floor of 8 trajectories. The split audit failed and only diagnostic trajectories were written.
- These are feasibility outcomes only. No labels were fitted, no model was trained, and no JEPA/baseline result exists.

## Frozen DEV04 change

DEV04 uses the same two games, rules, one-third phase threshold, component keys, family definitions, and support floors. It increases the candidate quota to 48 trajectories per game/split to test whether the failure is low support at the fixed 24 quota. For each game, compatible uniform/tactical components are assigned as whole units to train or validation toward a 25% validation trajectory target; components containing positional-family trajectories remain quarantined in full. Selection trajectories remain positional-family only. Component assignment is deterministic from candidate fingerprints and the declared quota; no model metric is consulted.

The DEV04 audit passes only if every admitted game has at least 8 unique trajectories, 64 model-facing records, and 16 H2 records in train, validation, and selection; both mandatory policy families occupy both seats in train/validation; every component is assigned wholly to one split; and no raw, symmetry/role-normalized, context, target, or full two-ply legal-reply key crosses split boundaries. Failed runs may write trajectories and full diagnostic receipts only, never `records.jsonl`.

## Stop rule and interpretation

If DEV04 fails, do not increase the quota again by default. Preserve its receipt, estimate the required local compute, and amend the admitted scope or split design under a separately versioned protocol before another pilot. A pass permits a separately reviewed small training pilot; it does not by itself grant permission for a large run or support a model-performance claim.
