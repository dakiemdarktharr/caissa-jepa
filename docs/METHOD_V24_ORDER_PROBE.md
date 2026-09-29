# V2.4 fixed-target additive-order probe

Frozen design, 2026-09-29, after the complete verified V2.3 diagnostic and before
implementation or new checkpoint measurements. This is a training-only
architecture-feasibility diagnostic, not a JEPA candidate or a development grid.
Generic random minimum-probe fitting is deferred; read V24_MECHANISM_CRITIQUE.

## Common budget decision

V2.3 found material80→160 progress in every family/capacity group and a capacity
response in all families/seeds. It did not establish convergence or a JEPA win.
For a future development comparison, adopt hidden/latent128/64 and exactly160
epochs as a bounded operating point for every relevant family, not a claimed
converged optimum. Do not extend only JEPA to320/640 epochs. Preserve decoded
and appropriate value/EMA controls; if tuning is included, offer the same
predeclared learning-rate opportunities to all families. The final architecture,
objective, primary planner metric and finite development grid are not frozen
by this diagnostic and require a separate method document before fitting.

## Scope and artifact identity

Use only the completed `chess_data/v23-fit-01` grid at source
`20f457c63bf07b2dd7f1a9eb9d5528d5d93cbc37`, its18 epoch160 checkpoints, and
standalone FULL training artifact `chess_data/v22-full-01`, fingerprint
`73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18`.
Require strict diagnostic-report verification and the independently audited
18-cell/509-root/9237-node/6750-fork inventory before measurements. All families,
seeds and capacities remain included; do not choose a favorable checkpoint.
Pin the prerequisite compact independent audit to file SHA-256
`e5f7d6df255699ea0f5684f215546f72dd48368f70e6c4c2ad1c478199ce8ced`,
and require its ledger/data/source identities to match these inputs. A status
string alone is insufficient.

No optimizer updates, new labels, development or protected-set input, planner,
action selection or match occurs. This first probe concerns H1 only: each
unique (root, own action) edge appears once, irrespective of reply count.
It does not quantify the H2 recurrent bottleneck or opponent response behavior.

## Outcome-blind block packing

Build each game's complete H1 edge table from the recorded legal training
closures, deduplicating replies and checking that repeated H1 targets agree.
Within each game enumerate root pairs with identical player-to-move and at
least two common action IDs. For each unordered pair of common actions a<b,
form the four distinct edges (s1,a),(s2,a),(s1,b),(s2,b). Root IDs are sorted.
Sort all eligible blocks by SHA-256 of canonical JSON
`[2401,game,root_id1,root_id2,a,b]`, with that identity as deterministic tie-break.
Greedily retain a block only if none of its four (root,action) edges was already
used in that game. Never reorder or repack using embeddings, errors or values.
Compute and save block/edge hashes and counts before loading any model.
The strict V2.3 report verifier itself loads checkpoints: invoke it only after
packing is saved, and require its success before any probe encoding.
Retain all packed blocks, including nonreversing and terminal-containing ones.

Report eligible root pairs, candidate blocks, selected blocks, total unique H1
edges, used edge count/fraction, and counts of blocks with0/1/2/3/4 terminal
targets. Freeze the sensitivity subset of all-four-nonterminal blocks from
rule metadata alone, without repacking. A game with no blocks is unsupported,
not a zero-error success. Insufficient coverage does not authorize new packing.

## Conditional bound and fixed measurements

For coordinate j, `g_j(z,a)=tanh(w_j^T z+beta_aj)` preserves the ordering of
two fixed input latents across every action. For fixed target encoder E,
let `d_a=E(T(s1,a))_j-E(T(s2,a))_j` and similarly d_b. A strict reversal
`d_a*d_b<0` forces four-edge squared error at least
`min(d_a^2,d_b^2)/2`. Set its bound contribution to0 otherwise. Sum over
coordinates and disjoint blocks. This is an SSE lower bound; do not sum
overlapping blocks or substitute an action-ordering formula mid-experiment.
The proof and coordinate-system limitations are in V24_ADDITIVE_DYNAMICS_LIMIT.

For every final checkpoint, evaluate both online and actual EMA encoder
targets separately. The online input latent always comes from the current
online encoder. Raw-JEPA/EMA targets are the primary architectural diagnostic;
other families and online targets are contextual/sensitivity measurements.
No projection or post-hoc latent rotation is introduced.

For each game/target space report all-H1 and packed-subset latent SSE and
dimension-averaged MSE, conditional bound SSE, bound MSE using both
`4*blocks*latent_dim` and `total_H1_edges*latent_dim`, and bound/full observed SSE
when defined. These uniform-edge quantities differ from the fork-sampled
training objective and from equal-root value error; label them explicitly.
Repeat packed quantities on the preselected all-four-nonterminal subset, with
its own denominator. Report strict reversals, reversals with both absolute
gaps>1e-6, ties with either absolute gap<=1e-6, and gap quantiles
0/0.25/0.5/0.75/1 of pooled absolute d_a,d_b (2*blocks*latent_dim observations)
and separately of min(abs(d_a),abs(d_b)) (blocks*latent_dim observations), using
linear interpolation. Strict reversal and near-tie counts can overlap; do not
present them as exclusive categories. Tiny gaps remain visible.
For the nonterminal sensitivity report both bound_NT/SSE on retained packed
nonterminal edges and bound_NT/SSE on all nonterminal H1 edges, with their
distinct counts/coverage. Neither replaces the primary all-H1 ratio.

Use the online value head for both target spaces when measuring target-value
oracle MSE, predicted-value oracle MSE and predicted/target value discrepancy.
Record its Euclidean weight norm and target-value gaps on the same blocks,
including all/nonterminal strata. These are descriptive task-relevance checks,
not evidence that the bound causes a wrong decision. Direct models contribute
target geometry, bounds and target-value quality only; never call their unused
random transition or score its predicted errors/ratios.
All H1 oracle labels and head values use the successor player-to-move
perspective. Never compare an unnegated H1 head to the root's outcome label.

Check the observed prediction's coordinate ordering and verify the conditional
bound does not exceed observed packed SSE with tolerance
`1e-10*max(1,observed_SSE,bound_SSE)`; exact/near floating-point ties do not
constitute a strict architectural violation. Any failed inequality, inconsistent
edge identity, nonfinite output or changed model tensor is a correctness failure
and makes the entire probe inconclusive, not a discarded row.
For the predicted-order assertion require opposite signs with both absolute
state-pair gaps>1e-12 to call a violation; these tanh coordinates lie in[-1,1].

## Prespecified descriptive materiality screen

Separately for each game/capacity, require at least25% coverage of its unique H1
edges and a median (over the three raw-JEPA seeds, EMA targets) conditional
bound/full observed SSE ratio>=0.10, with at least two seeds>=0.10. This is a
heuristic screen for a material obstruction in these frozen representations,
not a significance test or universal necessary condition. Zero observed SSE
makes the ratio unavailable; it cannot pass the screen. Report all individual
seeds and all-four-nonterminal sensitivity without replacing the primary screen.
Also show whether the sensitivity reaches25% of all nonterminal H1 edges and
the same10% median/two-seed criterion using bound_NT/all-nonterminal observed
SSE. A primary pass without that nonterminal support must be explicitly labelled
terminal-sensitive or unsupported for nonterminal planning. It does not prove
terminal states caused the difference; exact terminal overrides limit relevance.

A pass only motivates a separately frozen comparison that strengthens gated
and nonlinear-MLP transitions in non-JEPA controls as well. A low bound or low
coverage means this particular material-obstruction explanation is not
established; it does not prove additive adequacy because greedy packing and
the bound are conservative. No result here establishes a JEPA advantage,
irreducible joint encoder/model error, action-ranking failure or a new theorem.

## Integrity and resources

One fresh output directory, one serial CPU/BLAS thread,600s total acceptance
limit including verification/encoding/reporting,200MB local-output limit and
1GB process-lifetime peak-RSS acceptance limit. Cooperative deadline checks
between batches/after I/O; measured overshoots remain recorded failures. Preserve
an active journal and any failed outputs; no silent restart or adaptive retries.
Use batches128, float64, fixed tensor hashes before/after every checkpoint's
measurements. Save all counts, summaries, source/spec/block/checkpoint/data
identities and an immutable attempt receipt. Do not copy model/data artifacts
to Git or Obsidian. Freeze source with tests and independent review, commit/push
on main, and update Ground Truth/Obsidian before executing this probe once.
Check deadlines and peak RSS during block enumeration and before/after sorting
as well as during checkpoint measurements. Sorting/NumPy calls are cooperative,
not OS-preempted. Include packing and prerequisite verification in the600s cap.
