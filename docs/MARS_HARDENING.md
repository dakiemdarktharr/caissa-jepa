# MARS-JEPA Chess hardening handoff

This change is engineering validation, not evidence that the research hypothesis
is true. The production dataset was intentionally removed. No production
training or valid model-v-model result was created in this task.

## Implemented and tested

- Seven real shared registry entries, compatibility aliases, CLI/GUI selection,
  configuration/parameter/feature declarations and serialization fingerprints.
- Full supported FEN transition checks, including en-passant and both clocks;
  corrected fullmove export, apply/undo and snapshot serialization.
- Version-2 audit with actual shard checksums/counts, normalized game/provenance
  identity, duplicate detection, quarantine reasons, deterministic event groups,
  disjoint context/target positions and locked final test. The trainer re-audits
  the plan before cache preparation and rejects stale/missing data.
- Explicit fresh/resume, dataset-change override rejection, per-attempt failure
  diagnostics and traceback, per-model active-time reservations, checksum-bound
  generation recovery and full decoded ready-cache record verification.
- Finite-difference directional and largest-gradient-coordinate checks across
  every parameter tensor of all seven registered models. These are numerical
  regression checks, not an exhaustive proof for every possible input.
- All-legal policy metrics, value error, tactical/endgame strata, latent
  diagnostics and explicitly labelled scalar-to-WDL surrogate Brier/ECE.
- Behavioral response expectation replaces minimum-over-all-replies inference.
  The distribution is uncalibrated; no worst-case or counterfactual-outcome claim.
- Versioned confirmatory gate and fixed paired execution coordinator, live pinned
  UCI version/hash/options/time checks, three-seed checkpoint requirements,
  common budgeted negamax adapter, cluster-paired intervals and Holm adjustment.
- SQLite connections close before iterator yields; early termination, idempotent
  import, concurrency and Windows rename/cleanup have regression coverage.
- Source release self-test: seven fixture train/resume paths, Windows junction
  cache, corruption recovery, Qt monitor, SVG assets, ZIP staging and censored
  exploratory arena persistence. No new installer binary was built in this task.

## Scientific and operational blockers

A new licensed, fully audited dataset and fresh multi-seed checkpoints are still
required. No independent production UCI referee binary has been installed or
validated here. Tests use explicitly labelled temporary fixtures and a UCI stub.

The 120 frozen legal opening fixtures vary six opening families. Final
confirmation requires independent diversity review; the default protocol keeps
that gate closed. All required model/seed/data/referee identities and complete
uncensored pairs must pass before `ranking_ready` can become true.

The common-search adapter counts explicit tree nodes. Neural forward work is
charged to wall time, with a predeclared overrun tolerance; a late return is a
censored timeout. This is cooperative local execution, not an OS-enforced hard
real-time guarantee. The GUI's original continuous arena stays exploratory.

Allocated parameter matching does not imply matched active FLOPs. The direct
policy/value and local NNUE-style controls require an explicit capacity/compute
matching design before causal same-search comparison. Repetition history and
clock features are not learned; full-history exact rules own draw outcomes.
H4 currently supplies an auxiliary representation loss rather than H4 planning.

The audit streams source games but retains identity/position indexes and the
quarantine report in memory. Large-corpus audit capacity and runtime have not
been benchmarked against a production dataset. Do not extrapolate pilot cache
or ETA measurements to full-run performance.

Negative results must remain visible. If `full` does not outperform `h1`,
`h1-h2`, and `no-response` under matched conditions with uncertainty intervals,
narrow or pivot the contribution. A lower latent loss is not stronger chess.

## Compatibility and publication

CAISSA-JEPA package/import/executable/installer/storage identifiers are retained.
The two user-supplied prompt files are preserved and excluded from this commit.
Generated datasets, JSONL, NPZ, SQLite/DB, caches, checkpoints, builds and logs
remain excluded from Git. Historical recovery receipts are marked as such.
