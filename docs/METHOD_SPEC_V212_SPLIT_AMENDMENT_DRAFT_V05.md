# V2.12 split and root-schedule amendment — draft v05

**Status: review draft only.** This amendment is not frozen, does not replace
`METHOD_SPEC_V212.md`, and authorizes no data generation, model fitting, match,
or outcome access. It resolves the allocation wording before implementation.

## Proposed allocation matrix

| Use | Variant | Materialized trajectory windows? | Model-facing role |
| --- | --- | --- | --- |
| Fit | Connect Four 6x7/k4; Reversi 6x6 | Yes, training episodes only, rooted at `game.initial()` | Select 928 distinct eligible source windows per game before fitting |
| Development/model selection | Connect Four 8x8/k4; Reversi 8x8 | No labeled development episodes or training windows; only a frozen root-situation schedule | Compare the candidate with all five controls on zero-shot held-out sizes |
| Locked confirmation | Fresh situations after nomination, on the predeclared variants | No fit windows | Confirmatory evaluation only under a separate reviewed protocol |

No same-size development or validation windows are included. If the project
later decides it needs them, this amendment is insufficient: a new method
version must define their use and split/leakage treatment before any scores are
observed.

## Proposed replacement for the split language in method sections 3 and 6

Create project-owned training episodes rooted at `game.initial()` only for the
two fit variants. Before generation, freeze an immutable manifest that assigns
each complete episode to `train`, enumerates its game/rules fingerprint,
episode id, seed, ordered policy pair, and policy/source hashes, and fixes the
candidate episode quota.
The two policy seats are sampled independently and uniformly from the four
pinned families, preserving the existing 16-pair distribution. Pin the exact
RNG and episode-to-seed mapping; hash the realized ordered pairs and counts in
the manifest before generation. Every episode is replayed from its declared
root through its terminal state before windows are materialized.

After whole-episode ownership is fixed, enumerate eligible windows and their
raw, side-to-move-normalized, and symmetry-normalized identities over H0–H4;
track the H1/H2/H4 targets and terminal masks separately. Canonical-equivalent
window content is reported as a diagnostic but is not silently dropped.
Define a source-window id as `(game/rules fingerprint, episode id, start ply)`;
this is the unit meant by “distinct” for the 928-window bank. An eligible start
is a nonterminal state with a recorded legal action. Available terminal targets
retain exact utility and are masked from latent matching; unavailable tail
horizons remain masked, so a start need not have a nonterminal target at all
three horizons. A terminal-only window with no nonterminal H1/H2/H4 target
still counts toward 928 because it supplies root policy/value supervision and
exact terminal utility; it contributes no latent-match term. Before fitting,
verify every frozen minibatch has at least one valid latent target, and fail the
data gate if any batch is empty under the existing loss rule. Preserve
episode-first/start-ply-uniform sampling without
replacement using a pinned RNG stream: choose uniformly among eligible episodes
with remaining unselected starts, then uniformly among that episode's remaining
eligible starts. Continue until exactly 928 source-window ids are selected per
fit variant. Count canonical-equivalent or repeated trajectory content as a
data-quality diagnostic, but do not silently drop or upweight it; any content
deduplication would require an explicit revised sampling estimand. If support
leaves fewer than 928 windows, fail the data gate and create a new reviewed
protocol version rather than repeating or silently replacing windows. The role,
action, exact-target, and terminal-mask semantics in METHOD_SPEC v04 remain
unchanged.

Development/model-selection inputs are standalone reachable root situations,
not labeled development episodes and not materialized training windows. This
explicitly replaces the current train/development episode split language in
both §§3 and 6: training trajectories belong to `train` before windows are
formed, and held-out development roots are a separate evaluation unit, not a
development episode/window split. There is no within-size development episode
split.
Generate root situations only on the two held-out-size variants, from a seed
namespace disjoint from the training manifest. Each root must have a replayable
legal prefix from `game.initial()`; reject terminal roots, preserve forced pass
action 64 in source replay, and record the exact side-to-move. Before any model
is scored, freeze and hash every root situation id, rules/game identity, exact
state, generating policy pair, root-generation seed, source rollout length,
side to move, symmetry key, and paired seat-assignment schedule. Require at
least 40 unique reachable situations per held-out variant as already stated
in method §7. The companion `V212_DEV_ROOT_SCHEDULE_DESIGN_01.md` proposes an
exact 48-root bank with 16 per occupancy band from a fixed 64-slot candidate
schedule. This exceeds §7's minimum 40 but remains under review; its yield and
phase/uniqueness choices are unverified. If adopted, freeze its schedule and
failure rule before generation. Do not top up a failed schedule after scores.

The split audit uses the exact game/rules identity in every key. Because fit
windows and development roots use different board dimensions, cross-partition
state equality is not expected; the schedule still checks and reports all
same-identity overlaps, canonical duplicates, and root provenance. A future
same-size evaluation partition would need a fresh explicit overlap design.
Locked-confirmatory roots and seeds are not created or inspected during this
development phase. After nomination, they require a separate preregistered
schedule, independent review, and seeds/situations disjoint from both fit and
development.

## Acceptance and stop conditions

Before an executable generator is implemented, independent review must accept
the revised method text and the exact train/development allocation matrix. The
later data gate must demonstrate, from immutable receipts, full legal replay,
role/value perspective, forced-pass behavior, terminal masks, window identity,
all required split keys, per-policy/seat support, hashes/versions, exactly 928
distinct eligible fit windows per game, at least 40 development roots per
held-out variant, and zero prohibited overlap. A failure leaves
`training_approved` false. No fit begins until the separate compute, data-audit,
and pre-fit review gates also pass.

## Questions for review

1. Does this matrix correctly interpret the existing method's board-size
   holdout and development evaluation, or is a same-size model-selection set
   scientifically required?
2. Is source-window identity the correct meaning of a distinct eligible
   window, and is episode-uniform sampling among episodes with remaining starts
   the right no-replacement interpretation of method §6?
3. Is the companion 48-root/three-band/64-slot proposal suitable for held-out
   development, or should its schedule and phase coverage change before freeze?
4. How should repeated canonical window content be reported and monitored
   without changing the source-window sampling unit?
5. Can the state/key audit reuse the synthetic auditor after adding a corpus
   receipt adapter, while keeping synthetic and real-data approvals separate?
   How should production handling replace or scope its unconditional duplicate
   rejection so canonical-equivalent content is reported diagnostically as
   specified above, while cross-split overlap still fails closed?

This draft's preferred allocation is not a scientific result. It is a proposal
to make the current holdout and fit boundaries executable and auditable before
any dataset exists.

Independent review found the proposed split interpretation, source-window unit,
terminal-only eligibility, and no-replacement rule explicit and coherent as a
method amendment draft. Review does not freeze it or authorize generation.
Held-out root-generation policy/phase coverage, duplicate reporting, and the
insufficient-support rule still require a separate schedule decision.
