# V2.5 complete-reply robust latent consistency

Prospective specification, 2026-09-29. Frozen before implementation/fitting after
independent review; review amendments must precede source launch. This is one
finite adaptive DEVELOPMENT comparison, not confirmatory evidence. Previous
negative grids and V2.4 failed obstruction screen remain in the record.

## Question, prior art and boundaries

Hypothesis: concentrating part of latent-prediction training on the largest
error within a complete legal reply group improves hybrid minimax decisions
beyond equally strong recurrent task supervision, scalar consistency,
reconstruction and uniform latent matching. The unit is the legal replies to
one own action. This models deterministic transitions under supplied actions;
it does not predict an opponent's behavioral policy or an equilibrium strategy.

MuZero, SPR, EfficientZero, TD-JEPA, VAML/VaGraM, TEMPO, WAKER and Minimax Model
Learning rule out broad novelty claims. See V25_ROBUST_PREDICTION_RESEARCH.
The complete-reply adaptation and its controlled evidence are the contribution
under investigation; exact priority/uniqueness is unestablished. The nonlinear
predictor below is a standard common comparator, not a V2.4-proven repair.

For fixed targets t_b, predictions u_b, d-dimensional per-coordinate residual
ell_b=||u_b-t_b||²/d and J=.5 mean(ell)+.5 max(ell), a fixed L-Lipschitz head
obeys |min v(u)-min v(t)|<=L sqrt(2dJ). Target/oracle error is additional;
worst own-action error bounds selected-action regret by twice that error.
These elementary inequalities concern the same exact legal tree and terminal
overrides. They do not certify generalization, equilibrium, learned encoder
quality or improvement from minimizing average J. Head norms and encoded-target
oracle errors must be reported. Oracle-worst-reply weighting is rejected because
a different reply can become spuriously pessimistic and change the minimum.
Precisely, epsilon_a=max_b|v(t_ab)-V*(s_ab)| over nonterminal replies, zero for
an empty subset; delta_a<=L sqrt(2dJ_a)+epsilon_a. Include exact terminal values
on both sides of each minimum. Then regret<=2max_a delta_a. A mean or MSE is
not a substitute for epsilon_a; record these maxima separately in diagnostics.

## Immutable data and grouped sampler

Use only standalone FULL train `chess_data/v22-full-01` (fingerprint
`73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18`)
and standalone development `chess_data/v22-development-01` (fingerprint
`bbfc41fc34e1e346a9dc5905f9f686bb61582e4a63f363d76ea2406088235617`).
Never open parent `v2-forks-01`.
Training has509 roots,9237 nodes,6750 recorded forks; development has209 roots
(107 Connect4 4x5,102 Reversi6). All previous audits/exclusions persist. No new
labels/data/protected-state access. Training and development remain separate.

Group forks by (game,root_id,own_action), sorted lexicographically; replies in
adapter legal-action order. Verify all2056 H1 groups against exact rules, all
legal replies exactly once, same source/H1 target across replies, correct
successor-player labels and a singleton missing-H2 row only for terminal H1.
Do not group by outcomes or model errors. Terminal/pass rules stay unchanged.

Per epoch/seed, NumPy SeedSequence[seed,epoch,2501]: for each sorted game, sort
root IDs, permute their indices, then append uniformly sampled roots until261
root draws. For each root draw sample4 own-action groups uniformly with
replacement. Shuffle the resulting2088 group draws. Batch32 groups, preserving
complete groups:66 updates/epoch,10560 updates/160epochs. Repeated groups are
distinct draw instances. All families share every draw; differing reply counts
are recorded, not truncated or padded into artificial transitions.

Use SeedSequence[seed,epoch,2511] for one legal symmetry per drawn group, in
draw order, independently of sampling: gravity identity/reflection, Reversi D4.
Apply that same transform to root, own action, all replies and their labels.
Group identity is the draw instance; transformed action order may differ but
member order/aggregation is unchanged. Every full reply remains represented.

## Common model and supervision

Shared across games:198 features, encoder tanh(198→128) then tanh(128→64),
65-action linear policy head, tanh scalar value head. Same feature adapters and
legal masks as V2; no cross-game transfer claim. Value always uses the current
player-to-move, so H1 is opponent perspective and H2 restores root perspective.

Every recurrent family uses g(z,a)=tanh(tanh([z,a]W1+b1)W2+b2), hidden width50,
latent64, action65;9764 transition parameters. Same module recurrently for H1/H2.
Direct has the same encoder/heads and never uses its allocated transition.
Common initialization is seed-addressed with identical matching tensors across
variants. No warm starts. EMA coefficient.99; targets stop-gradient. Online
head is used on predicted states. Scalar consistency uses the SAME online value
head on the actual EMA-encoded target, detaching that entire target branch
(including its head). This matches the fixed-head bound; using an EMA value head
instead would confound head lag with latent error. EMA value-head tensors may
remain stored for inventory consistency but are not scalar auxiliary targets.
Allocate the same parameter inventory in all families, including dormant decoder
weights; report active versus allocated counts separately. Only decoded-tail
updates the decoder. Equal unused allocations are not equal active compute.

For G group draws, each group's K full rows receives occurrence weight1/K.
Root/H1 contributions therefore occur once per group; H2 averages its replies.
Encoded policy CE averages these weights over policy-labelled nonterminal
positions; encoded value MSE averages over all valid labelled positions.
All labels are available in this FULL artifact. Illegal logits are excluded.
Missing H2 is masked; no fabricated policy at terminal positions.
Common policy weights remain1/K for the ORIGINAL complete group even when some
terminal policy terms are excluded; auxiliary subset means instead divide by
the eligible nonterminal count. These distinct denominators require tests.

Every recurrent family additionally receives H1 and H2 value MSE and legal
policy CE, each with coefficient.25 per horizon. Within each horizon use row
weights1/K and normalize by the eligible value/policy weight sum separately.
This is a stronger MuZero-style task control, not a reproduction of MuZero.
Direct receives encoded supervision only. All recurrent variants share the
variance penalty.1*mean(max(0,.1-std(z))²), std=sqrt(weighted population variance
+1e-4), using valid encoded occurrence weights. Direct coefficient0.

## Auxiliary families and gradients

Seven families, fixed auxiliary coefficient.1 for every auxiliary family:

1. `direct`: encoded policy/value only; no recurrent/auxiliary computation.
2. `recurrent-pv`: common recurrent policy/value, no auxiliary.
3. `decoded-tail`: linear decoder64→198; target actual features. Per-coordinate
   reconstruction residual, with aggregation below.
4. `scalar-tail`: squared predicted-value minus detached same-head EMA-target-value;
   same aggregation, no hidden-label substitution (all labels already present).
5. `raw-mean`: squared predicted latent minus detached EMA latent, divided64;
   mean aggregation at H2.
6. `raw-tail`: same latent residual; half-mean/half-max H2; prespecified candidate.
7. `raw-scaled`: latent residual with uniformly allocated gradient scaled per
   group by detached J/mean(ell), or0 when mean is exactly0. Its forward group
   loss equals J, but its residual gradients are uniform times that factor.
   This is a gradient-allocation control, not an alternate research candidate.

Auxiliary H1 uses each NONTERMINAL H1 once per group, ordinary mean across
eligible groups; raw-scaled H1 equals raw-mean. Auxiliary H2 excludes terminal
successors because evaluation uses exact terminal overrides; retain the original
complete group and aggregate its nonterminal subset. For decoded-tail,
scalar-tail and raw-tail use J=.5mean(ell_b)+.5max(ell_b). raw-mean uses mean.
Groups with no eligible nonterminal H2 contribute neither loss nor denominator.
Average group losses over eligible groups, separately H1/H2; add.1 times each
horizon auxiliary. Report missing/terminal/eligible group and row counts.
Terminal states still receive common supervised value training.

For exact max ties, share the max subgradient equally among all exact maxima.
The scaled-uniform factor is detached: finite-difference checks must hold its
base-point value fixed. Its equality of forward loss is per-model/current
residual, not equality to the separate tail model's evolving loss trajectory.
Record scaled-factor minima/maxima/means and exact-max tie counts; no clipping
is applied. For nonzero errors the factor lies in[1,(1+K_nonterminal)/2]. This
control does not match gradient norms or active compute across training paths.
Max-tie subgradients are verified analytically/directionally; use ordinary finite
differences away from ties, not central coordinate differences at3+ equal maxima.
No gradient enters EMA targets or aggregation-derived detached factors. H2
backpropagates through H1 and the shared predictor to the root encoder.

Float64 NumPy, Adam(.9,.999,eps1e-8), global gradient norm clip5, seeds17/29/43.
Two rates .001/.0003,160 epochs, no warmup/decay/early stopping. Exactly42 fresh
cells (7×2×3), all completed before comparison. No auxiliary-weight search,
extra candidate seeds, later capacity extensions or dropping failed cells.
Adaptive retry requires an amended future protocol and preserves failed work.

## Evaluation and fixed decisions

Use unchanged V2 evaluator for209 roots×exact/hybrid tracks per cell:4096 exact
transition-node cap,1s/root cooperative deadline, all legal branches, exact
terminal overrides, deterministic adapter-order ties. Every learned/control
cell has the same schedule and seeds. Direct uses actual encoded leaves in both
tracks. Hybrid uses predicted H2 latents and current value head for nonterminal
leaves. These are same-tree bounds, not matched wall time or FLOPs; report all
runtime/neural counts and active parameters. No engine-strength claim.

Preserve the original primary metric: equal-game mean EXACT action regret. Tune
one global rate per family by three-seed mean exact regret, tie to smaller rate.
Use that SAME selected rate for hybrid and mechanism analysis for every family.
No separate hybrid retuning or checkpoint substitution. Hybrid regret is the
prespecified additional mechanism gate. A hybrid-only gain cannot be called a
pass of the original project screen. Preserve every cell/rate/per-game result.

Compare raw-tail to direct, recurrent-pv, decoded-tail and scalar-tail. Per track
require improvement>=.05 versus strongest control, positive both games versus
each control, and positive equal-game improvement in at least2/3 paired seeds
versus each. Report paired-root bootstrap95% intervals with10000 draws,
SeedSequence[2505,track_index], sharing each resampled root across seeds and
stratifying by game. No interval or development gate is confirmatory significance;
reused209 roots and adaptive hypothesis search preclude that interpretation.

Mechanism additionally requires raw-tail hybrid regret below both raw-mean and
raw-scaled (each tuned on exact identically), positive both games and at least2/3 seeds;
and lower hybrid own-action backed-up oracle MSE than each non-JEPA recurrent
control. MSE is mean squared error of saved `action_estimates` versus original
root-perspective oracle own-action values, first average actions/root, then
roots/game, then equally games. Compute from saved records, no extra inference.
The same-head/target conditional error is diagnostic, not an equilibrium metric.

If hybrid gates pass but exact project gate fails, report a narrow exploratory
hybrid result; no broad project promotion. Both passing merely admits independent
selection work, never a superiority/Q1/transfer conclusion. If scalar/decoded or
scaled-uniform controls explain the gain, the proposed JEPA-tail mechanism fails.
If no candidate survives, stop this specified recipe and preserve negative
evidence; no post-hoc replacement candidate from an ablation.

Record per-game standard representation/policy/value diagnostics on development
fork occurrences (label weighting explicitly differs from grouped training),
true EMA H1/H2 nonterminal mean/max residuals by complete group, online head norm,
target-value oracle error, and total valid/skipped/missing/terminal counts.
Collapse check uses all unique development nodes per game: effective rank<2 or
median coordinate std<.001 makes the cell/grid inconclusive. No policy calibration
or unseen-game claim follows from NLL/MRR alone.

## Runtime, audit and implementation gates

Fresh-only atomic checkpoints, journals and per-epoch receipts; identity includes
source/config/objective/data/group/symmetry fingerprints and environment. No
resume for this bounded grid. Save final tensor/checkpoint hashes, actual epoch
draw/group/fork-row/label counts, update count and elapsed cost of failures.
Check unchanged source and immutable input manifests throughout and at completion.
Do not read selection/final paths, and keep all exposure counters explicit0.

Serial CPU, one BLAS/OMP thread, no paid compute.600s/cell including evaluation,
25200s cumulative cell budget,3GB output and1GB lifetime peak-RSS acceptance
limits; cooperative checks around epochs/batches/evaluation/serialization.
All42 cells are intended; stop on any failure/censor/collapse/limit violation,
record inconclusive status and preserve output. These limits bound work; they
do not guarantee low peak system load or equal active computation.

Before fitting: independent method review, group legality/sampler/augmentation
tests, manual-gradient finite differences including recurrence/tail ties/scalar
targets/detached allocation, atomic checkpoint identity tests, no protected
access, pure report gates/tuning/bootstrap arithmetic, and independent source
review. Commit/push verified source on sole main, mirror documentation in Obsidian.
After fitting: independent artifact/source/schedule/decision audit, complete
negative-results ledger, updated professor brief and no overclaim.
