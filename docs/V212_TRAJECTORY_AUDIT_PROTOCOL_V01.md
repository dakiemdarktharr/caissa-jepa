# V2.12 trajectory audit protocol v01

**Status: frozen; synthetic implementation independently reviewed and accepted.**
This protocol authorizes only a tiny in-memory, synthetic rules/window-auditor
fixture. It does not authorize generating a dataset, reading saved outcomes,
fitting a model, running a match, or changing the candidate training method.

## Purpose

Demonstrate that a V2.12 window auditor fails closed on transition,
terminal-mask, forced-pass, duplicate, and four-ply split-overlap defects before
any model-facing window can be emitted. This is a software contract test, not a
data-feasibility or leakage-free-dataset result.

## Allowed inputs and outputs

- Construct all examples in memory from deterministic `BoardGame` rules and
  hand-authored synthetic states/actions. Do not read `chess_data/`, a saved
  trajectory, a training label, checkpoint, match, or locked-final artifact.
- Use fixed, documented fixture constants. Do not sample weights, instantiate
  an optimizer, or call training/model-selection code.
- The auditor returns a pass/fail result and expected window/mask counts only.
  It writes no files and does not set any training-approval flag.
- Pin source/rules/protocol hashes in the test result if a report is produced.

## Required fixture cases

1. **Valid ordinary path:** use a small legal Connect Four adapter path and
   verify replay, actor alternation, action legality, and windows at H0–H4.
   JEPA latent target horizons are H1/H2/H4; H3 is an intermediate context
   state, not a latent-loss target.
2. **Terminal boundary:** include a legal path that ends at a known terminal
   state before the four-ply window is complete. Verify that every later
   horizon is masked, terminal utility is taken exactly from the rules adapter,
   and no terminal latent target is exposed.
3. **Forced pass:** use a synthetic Reversi state where the side to move has
   only action 64 while the opponent has a legal placement. Verify pass
   legality, role alternation, and the next state's legal actions.
4. **Illegal replay:** inject an illegal action, an altered replay state, and
   an incorrect terminal result. Each must fail before any window list is
   returned.
5. **Duplicate window:** inject the same context/action/target window twice,
   including its role- and symmetry-canonical equivalent. The audit must report
   the duplicate and fail closed rather than silently oversample or drop it.
6. **H4-only split overlap:** pass two otherwise distinct synthetic window-key
   records whose H0–H3 keys differ but whose H4 context/target identity is the
   same across train and development. The overlap check must reject the pair.
   Keep this detector fixture separate from board-game replay because its
   purpose is to isolate the horizon-key coverage predicate.
7. **No partial output:** for every failing case, assert that the public audit
   entrypoint returns no model-facing windows and creates no files.

## Key and mask contract

For each eligible window, audit the raw and side-to-move-normalized key for
every state at offsets H0 through H4, together with all legal symmetry
transforms supported by that game. Check the materialized JEPA targets at
offsets H1, H2, and H4. State identity keys include game/rules identity and the
raw or canonical state only; store episode lineage, source split, and window
start as separate owner metadata so they cannot hide cross-split collisions.
A repeated key crossing train/development/selection/locked assignments fails
the fixture. The exact treatment of shared initial states and overlapping
prefixes in a *real* generated corpus remains open and must be frozen in a
separate V2.12 generation protocol before data are produced.

For horizons 1, 2, and 4, a latent target is valid only when every transition is
legal and the target state is nonterminal. A terminal target instead carries
the exact player-perspective payoff and is excluded from latent matching. All
masked, valid, and terminal-exact cases must be counted explicitly; a missing
target must never be substituted with an all-zero state or latent.

## Pass criteria and limits

All seven fault/positive cases above must produce the declared result. Test
runtime is not a production budget measurement. Passing this protocol closes
only the auditor's synthetic software-contract check; it does not certify
V2.8/V2.12 data splits, support, a generator, a 5-second planner deadline,
6-second response handling, model feasibility, novelty, or training readiness.
The request-to-response runtime audit remains a separate no-training gate.

The implementation is in `two_player/v212_trajectory_audit.py`, with synthetic
contract tests in `tests/test_v212_trajectory_audit.py`. The focused auditor
and V2.12 pilot regression set passes 16 tests. Independent review accepted the
implementation for this synthetic-only contract. This does not close any
data-generation, training, or runtime gate.
