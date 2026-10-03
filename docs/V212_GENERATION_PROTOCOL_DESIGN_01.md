# V2.12 data-generation protocol design note 01

**Status: design note only; not frozen and does not authorize data generation.**
No trajectory, training label, checkpoint, match, or saved outcome was read or
created for this note.

## Why a generation protocol is needed

`METHOD_SPEC_V212.md` fixes the candidate training objective, four policy
families, and a requirement for 928 valid train windows per game. It does not
yet freeze a V2.12 episode/seed manifest, split assignment rule, or a root
situation schedule for the independent development evaluation. V2.8 supports
the same Connect Four 6x7 and Reversi6 training sizes, but cannot silently
supply V2.12's protocol, split, policy schedule, or H1/H2-only record schema;
it also does not generate V2.12's held-out-size evaluation variants.

## Critical split-design issue

All episodes produced by the current V2.8 generator start from the same
standard initial position for a game. A strict component assignment over every
H0–H4 state would therefore connect episodes that share that initial position.
If episodes were assigned independently to train and development before
windows are formed, the shared state would violate the split boundary. The
existing component allocator avoids some early overlap by deriving keys only
after a phase threshold, but that is not a V2.12 rule and cannot be imported
without changing the method's declared window population.

V2.12 needs a preregistered root-situation design before generation. Candidate
options to evaluate in a versioned protocol are:

1. assign training trajectories and development roots from separately seeded
   reachable-state schedules, then quarantine any collision across complete
   H0–H4 context and H1/H2/H4 target keys; or
2. declare and justify a fixed opening-prefix exclusion, then audit every
   retained window and evaluation root beyond that prefix.

These choices affect which states the model sees and the evaluation target.
Neither is adopted by this note. The root schedule, derivation policy, minimum
ply, symmetry handling, collision rule, and insufficient-support disposition
must be reviewed and frozen together. A post-generation choice based on observed
scores is disallowed.

## Required frozen protocol fields

Before generating any candidate data, a new protocol version should bind:

- game/rules adapter fingerprints, dimensions, and policy implementation hashes;
- one immutable root/episode schedule with independent seed streams for each
  game and partition, and episode IDs derived from those inputs;
- per-seat policy-family draws from the four pinned sources, plus exact RNG
  algorithm and seeds, rather than an inferred schedule from the split name;
- whole-episode partition ownership before window materialization, with a
  complete raw, role-normalized, and symmetry-normalized H0–H4/H1-H2-H4 key
  audit and explicit quarantine counts;
- canonical window deduplication and the definition of 928 distinct eligible
  training windows, including terminal masks and whether short tail windows
  count;
- development root situations and both seat assignments, generated from a
  seed namespace disjoint from training and checked against all training keys;
- selection data policy, if any, while keeping the locked-final set unopened
  until nomination and a separately reviewed confirmatory plan;
- atomic output behavior, provenance/license statement, manifest and per-file
  hashes, replay receipts, audit schema, and a `training_approved: false` guard;
- failure behavior when component quarantine leaves fewer than 928 windows or
  insufficient development roots: stop, preserve the failed audit receipt,
  and draft a new version rather than top up or alter counts silently.

The next review should decide the root-situation strategy and align the method
spec's split language with it. Only then should an executable generator be
implemented and independently reviewed. A generated corpus would still need
replay, support, split, leakage, and license gates before any fit; this design
does not authorize a fit, match, or outcome inspection.

## Current disposition

The V2.12 synthetic auditor from `V212_TRAJECTORY_AUDIT_PROTOCOL_V01.md`
provides reusable in-memory checks, but the H4 overlap detector is only a
software fixture. V2.12 corpus feasibility and train/development disjointness
remain untested. No support claim, leakage-free claim, or training readiness
claim follows from the synthetic tests.
