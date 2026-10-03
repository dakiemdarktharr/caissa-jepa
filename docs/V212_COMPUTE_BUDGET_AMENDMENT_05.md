# V2.12 compute-budget amendment v05 — proposal

Status: frozen as an independently reviewed budget proposal. It is a candidate
protocol amendment, not an operational cap or fit authorization. It does not
authorize data access, fitting, match play, or a scientific claim. The
implementation, request-to-search headroom, and full pre-fit gates require
separate verification before this budget can be used.

## Evidence basis

The independently accepted V2.12 random-weight compute pilot v02 measured
1,152 root/arm/initialization cells across four board variants, 64 unique roots,
six arms, and three paired initializations. All completed four plies under the
8-second/500,000-node/1.5-GiB safety ceilings. Maximum observed wall time was
3.741895 seconds and maximum node visits were 7,224. Twelve cells exceeded the
old 2.0-second proposal; zero exceeded 5 seconds or 10,000 nodes. Maximum
sampled RSS was 50,212,864 bytes. The receipt SHA-256 is
`f16cdb8f624e79b32bbef7499a2b772b7bdd3a64097a60cc3b9dbbe631f1df13`; details
and limitations are in
`docs/validation/V212_RANDOM_WEIGHT_COMPUTE_PILOT_02.md`.

## Proposed common per-move budget

Use the same limits for every arm and variant:

- 10,000 entered search-node visits;
- 5.0 seconds wall time;
- 1.5 GiB sampled RSS as a hard process safety stop.

The node limit is the measured maximum (7,224) multiplied by 1.25 and rounded
up to the next 1,000. The wall limit is the measured maximum (3.741895 s)
multiplied by 1.25 and rounded up to the next whole second. This 25% margin is
a pragmatic engineering reserve, not a confidence bound or tail guarantee.
The 1,152 rows reuse 64 roots across six arms and three initializations on one
host, so they are clustered measurements, not 1,152 independent positions.
The memory ceiling retains the v02 pilot's safety limit; it is not presented
as an empirical working-set estimate. Applying the proposed node limit and
5-second wall limit to the *measured search-call durations* in the v02 receipt
would stop zero of the 1,152 cells. Pilot wall time begins inside
`run_root_arm`; it excludes request-to-search setup and dispatch. The maximum
observed search duration leaves approximately 1.258 seconds before the
request-anchored 5-second planner deadline. The required implementation and
pre-fit gate must verify that setup/dispatch fits this headroom. This finite
synthetic, random-weight sample does not guarantee that fitted models or
unseen states will fit the budget.

Stop search on the first reached node, planner-wall, or sampled-memory limit.
Start one monotonic per-move clock when the move request arrives. The planner
deadline is request time plus 5.0 seconds; setup and dispatch time consume this
budget, and search must use the remaining time. Return the action from the last
fully completed iterative-deepening root pass;
if depth one did not finish, return the first legal action in the frozen
adapter order. Such a controlled, legal fallback is recorded as a budget
fallback with its completed depth and is not a timeout or forfeit.

Superseding only the old 2-second planner cap and its timeout handling in
`METHOD_SPEC_V212.md` §5, set a separate 6.0-second end-to-end response
deadline on the same move-request clock. This leaves one second after the
planner deadline for controlled fallback and response handling. If the process is
killed, emits no legal response by 6.0 seconds, or returns an invalid action,
the game is a forfeit to the other player. The one-second response reserve is
an operational proposal, not measured by the compute pilot; the reviewed
implementation and pre-fit evaluator must verify fallback/response behavior
within it before any match. Report controlled budget fallbacks separately
from process timeouts and forfeits. Never grant extra time or nodes to an arm,
variant, seed, seat, or observed result.

## Reporting and gates

Any later development evaluation must report per-cell nodes, transitions,
model calls, CPU/wall time, sampled memory, completed depth, controlled
fallback counts, process timeouts, and forfeits. Keep all paired blocks,
including fallback games, in the declared primary analysis; do not censor or
replace a game based on which arm hit the budget.

The implementation must make node and planner-deadline checks effective
inside search, retain only fully completed root iterations, preserve a legal
fallback under every controlled stop, and enforce the separate end-to-end
deadline. Independent review must accept this amendment and its implementation
before a pre-fit grant is considered. The
V2.12 novelty comparison, fresh trajectory/replay and leakage audits, exact
data/config/schedule/source hashes, and separate pre-fit review remain open
gates. Until each passes, no fitting, matches, or outcome-data access is
permitted.
