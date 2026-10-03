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

## Split-allocation ambiguity

V2.8 episodes all start from the standard initial position. If same-size
episodes were independently divided between train and development and every
H0–H4 state were part of the overlap audit, their common opening would join
those episode components. The V2.8 component allocator avoids some early
overlap by deriving keys only after a phase threshold; that threshold is not a
V2.12 rule and cannot be imported without changing which windows are eligible.

However, `METHOD_SPEC_V212.md` says held-out board sizes cannot appear in fit
data and defines primary development evaluation on those held-out variants. If
the split matrix is strictly train windows on Connect Four 6x7/Reversi6 and
development roots only on Connect Four 8x8/Reversi8, shared standard openings
occur only within their own partition and do not create a cross-split state
collision. The specification does not state this allocation matrix explicitly:
it also refers to train/development episode groups before windowing. That
ambiguity should be resolved before generation.

The preferred design to review is to freeze the matrix as:

- fit windows only from the two declared training variants;
- development/model-selection roots only from the two held-out-size variants,
  generated from a separately hashed reachable-situation schedule; and
- no same-size development windows unless a new method version explicitly
  defines them and their opening-overlap treatment.

Under that design, repeated openings are not a blocker. If reviewers require a
same-size development split, V2.12 must additionally choose a predeclared
reachable-root schedule or justified prefix exclusion, audit all retained
H0–H4/H1-H2-H4 keys, and quantify the effect on the training-state
distribution. These alternatives are not adopted here. Freeze the exact split
matrix, root-generation policy, symmetry handling, collision rule, and
insufficient-support disposition together before observing scores.

## Required frozen protocol fields

Before generating any candidate data, a new protocol version should bind:

- game/rules adapter fingerprints, dimensions, and policy implementation hashes;
- one immutable root/episode schedule with independent seed streams for each
  game and partition, and episode IDs derived from those inputs;
- per-seat policy-family draws from the four pinned sources, plus exact RNG
  algorithm and seeds, rather than an inferred schedule from the split name;
- an explicit variant-by-split matrix and whole-episode partition ownership
  before window materialization, with a complete raw, role-normalized, and
  symmetry-normalized H0–H4/H1-H2-H4 key
  audit and explicit quarantine counts;
- canonical window deduplication and the definition of 928 distinct eligible
  training windows, including terminal masks and whether short tail windows
  count;
- development root situations and both seat assignments, generated from a
  seed namespace disjoint from training, with reachability and cross-split key
  checks at the exact game/rules identity used by the auditor;
- selection data policy, if any, while keeping the locked-final set unopened
  until nomination and a separately reviewed confirmatory plan;
- atomic output behavior, provenance/license statement, manifest and per-file
  hashes, replay receipts, audit schema, and a `training_approved: false` guard;
- failure behavior when component quarantine leaves fewer than 928 windows or
  insufficient development roots: stop, preserve the failed audit receipt,
  and draft a new version rather than top up or alter counts silently.

The next review should assess the proposed method amendment in
`METHOD_SPEC_V212_SPLIT_AMENDMENT_DRAFT_V05.md`. Only after its matrix and the
held-out root schedule are frozen should an executable generator be implemented
and independently reviewed. A generated corpus would still need
replay, support, split, leakage, and license gates before any fit; this design
does not authorize a fit, match, or outcome inspection.

## Current disposition

The V2.12 synthetic auditor from `V212_TRAJECTORY_AUDIT_PROTOCOL_V01.md`
provides reusable in-memory checks, but the H4 overlap detector is only a
software fixture. V2.12 corpus feasibility and train/development disjointness
remain untested. No support claim, leakage-free claim, or training readiness
claim follows from the synthetic tests. Independent review found this note
accurate as a non-authorizing design document. The method amendment draft now
proposes training episodes/windows on fit variants and standalone development
roots on held-out sizes, explicitly replacing the ambiguous episode-split
wording. The companion `V212_DEV_ROOT_SCHEDULE_DESIGN_01.md` proposes a fixed
48-root bank and fail-closed candidate schedule; independent review found it
suitable for further design review, but the 64-slot yield, occupancy bands, and
symmetry uniqueness rule remain unverified and must be frozen before any root
generation.
