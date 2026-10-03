# V2.12 random-weight inference compute pilot v01

Status: frozen no-training instrumentation protocol. This pilot measures
inference compute only. It does not authorize trajectory generation from
training episodes, fitting, match play, outcome recording, model selection, or
changing the research claim. The V2.12 v04 method review cleared this narrowly
scoped random-initialized pilot; the disposition is recorded in
`GROUND_TRUTH.md`.

## Question

Can all four declared board variants and all six v04 inference arms be
measured under one conservative node, wall-time, and memory ceiling, with a
last-completed-depth fallback? Measurements may inform a later versioned
common-budget proposal. They cannot establish playing strength, superiority,
scientific novelty, or feasibility of training.

## Frozen inputs

- Variants, in order: Connect Four 6x7/k4, Connect Four 8x8/k4, Reversi6, and
  Reversi8. Use the project-owned `BoardGame` rules implementation and its
  fixed legal-action order.
- Roots: for each variant and target ply in `{0, 8, 16, 24}`, scan uniform-
  random legal episodes in ascending seed order beginning at
  `66271 + 1000*variant_index + 100*target_ply`; take the first reachable,
  nonterminal state at that ply. Try at most 64 consecutive seeds per target
  ply, then fail before model inference if the root is unavailable. Record
  only seed, ply, and a SHA-256 state fingerprint. These are synthetic legal
  states, not training or evaluation examples.
- Arms, in the v04 order: multi-step JEPA, single-pair JEPA, recursive
  raw-state dynamics, value-only latent rollout, direct-leaf value, and the
  single-horizon JEPA ablation. Each uses freshly initialized random weights;
  named seed streams pair shared encoder, predictor, and value weights across
  compatible arms. No checkpoint or dataset is opened.
- Run one deterministic warm-up inference per arm on the first root, then the
  complete root schedule once for each arm. Warm-up is reported separately.
- Search: iterative-deepening alpha-beta through four individual plies. Root
  actions and replies retain adapter order, and all arms receive identical
  roots and budgets. Return internally the last fully completed root
  iteration if a ceiling interrupts a deeper iteration; if depth one does not
  complete, use the first legal action. Do not record or report selected
  actions, action values, game scores, or outcomes.
- Count a search-node visit on entry, including root and terminal leaves;
  count every exact rules transition call separately, including a generated
  child not subsequently entered. Count encoder, predictor, decoder, and value
  head calls separately, and report their sum as model calls.

## Safety ceilings and measurements

Per root-arm run, stop at the first of:

- 500,000 entered search-node visits;
- 8.0 seconds wall time;
- 1.5 GiB sampled resident memory, sampled before search and every 256 node
  entries.

These are pilot safety ceilings, not proposed production move budgets. The
previous 2.0-second provisional cap is known to fail the rule-only Reversi8
diagnostic. A later cap proposal must use only these no-outcome measurements,
retain one common budget for every arm/variant, and specify fallback and
timeout handling in a new reviewed protocol.

For each root-arm run record only the root id/fingerprint, variant, arm,
completed depth, stop reason, node visits, exact transition calls, per-module
and total model calls, wall time, and sampled resident-memory peak. Keep raw
receipts under ignored `chess_data/`; publish an aggregate compute-only report
with code, source, schedule, protocol, and runtime fingerprints. No run may
read labels or training histories, update parameters, save a fitted
checkpoint, score a game, or select an arm.

## Exit gate

Verify all 96 root-arm cells, deterministic schedule reconstruction, source
and receipt hashes, finite measurements, and the absence of outcome fields.
An independent reviewer must inspect the harness and no-outcome report before
any cap revision or later pilot. Regardless of the compute result, training
and matches remain closed pending the V2.12 novelty comparison, fresh
trajectory/replay and leakage audits, and a separate pre-fit review.
