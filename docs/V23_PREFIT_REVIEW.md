# Independent V2.3 prefit review

Reviewed 2026-09-29 before research fitting. Scope: `METHOD_V23_DIAGNOSTIC.md`,
the epoch-40 hash references, `two_player_v23_diagnostic/runtime.py`,
`metrics.py`, and their engineering tests. This is an internal independent
reviewer agent, not an external replication or third-party scientific endorsement.

## Conclusion and scope

No blocking scientific or implementation defect remains in this reviewed scope.
The 18-cell design can diagnose training value fit under a fixed optimizer and
compare two total-model capacities. It cannot establish generalization, playing
strength, a JEPA advantage, policy convergence, or irreducible prediction error.
The negative development grids and their promotion requirements remain intact.
The report implementation receives a separate review; no research run is claimed
complete by this document.

## Access, identity and fairness

- The runner accepts one standalone training artifact and a fresh output path.
  Its manifest fingerprint and train split are rejected before calling the label
  loader when mismatched. Full labels, label seed, audit status, exposure counts
  and record splits are checked. No development or parent-bank path is accepted.
- Metrics call only the source-pinned pure alignment helper with `saved=None`.
  They do not invoke its inventory loader or CLI. They reject incorrect splits
  and missing label masks before model encoding.
- All three families receive both capacities, the same fixed learning rate,
  160 epochs, and matched seed-addressed fork/symmetry schedules. Larger capacity
  changes encoder, heads and predictor together. Its negative results remain
  conditional on the chosen learning rate and optimizer.
- S uses equal roots with nonterminal targets within each game/horizon, then
  equal weights for all four supported components. Terminal/missing-horizon
  counts and transition-weighted summaries remain available. Raw-node geometry
  weights each node once; direct's untrained dynamics are unscored.
- Initial snapshots are engineering references. Effective-rank, standard-deviation
  and nonfinite gates apply at every snapshot, including initialization. Training
  fit does not justify inferential confidence intervals over repeated forks.

## Replay and checkpoint review

The nine required Grid03 FULL reference checkpoints were independently read
without loading their evaluation outputs or any parent dataset. All nine file
SHA-256 values and all 531 online/EMA/Adam tensor hashes matched their references.
The reference JSON SHA-256 is
`8311c459634a4b183b03e920834bcc6d00c8766c2589f4b4d9a4fbee02702f74`.

New runs initialize from seed. At small-model epoch 40 they compare configuration,
59 tensor hashes and epoch/update counters; a mismatch prevents interpretation.
Whole NPZ file equality is correctly not required because run identity metadata
can differ. Four separate checkpoint files per cell preserve the prescribed
0/0, 40/2640, 80/5280 and 160/10560 snapshots. Save/load verification includes
online tensors, EMA tensors, both Adam moments and counters. Diagnostic mutation
of that state is rejected.

## Resource and failure review

Deadlines are cooperative acceptance limits, not OS-level preemption. They are
checked around updates, diagnostics and checkpoint I/O; measured overruns fail.
An active journal precedes fitting. Failure records retain elapsed work, the
outer ledger includes failed-cell time, and subsequent planned cells stop.
Existing output/cell paths cannot silently resume an interrupted run.

Review found a final-write boundary: ledger growth could cross the aggregate
artifact limit after the preceding size check. The implementation now checks
again after the final ledger write and records `inconclusive` on overflow. An
independent regression exercises that boundary. File-size scans after writes
preserve the gate without scanning the entire output tree after every optimizer
batch. Process peak RSS is explicitly a process-lifetime measurement.

## Engineering verification

`test_v23_runtime.py`: **14 passed**. Tests use synthetic arrays and mocked
optimizer updates, never research fitting. Coverage includes historical schedule
replay at epochs 0/39/79/159, complete fixed-grid construction, source pinning,
training-only loader routing, rejected foreign artifact identity, atomic receipt
preservation, checkpoint/diagnostic state tampering, both accepted and rejected
epoch-40 replay, separate snapshots, fresh-only behavior, failed-work accounting,
cooperative overrun, output cap and final-ledger growth.

`test_v23_metrics.py`: **5 passed**. Independent arithmetic checks verify S with
unequal root/transition weighting, H1 deduplication, missing H2 and terminal
counts, raw-node geometry, read-only model/data state, and access/support guards.

Combined command: `python -B -m unittest test_v23_runtime test_v23_metrics -q`,
with one BLAS/OMP thread: **19 passed in 2.607 seconds**. These are engineering
results, not research evidence. `git diff --stat -- two_player two_player_v2
two_player_v21 two_player_v22` produced no output: the historical packages had no
tracked diff at review time. Source freeze, full regression and the separate
report review still belong to the launch checklist.
