# V2.2 prospective label-access development study

Frozen2026-09-29 after grid02 and before implementation/fitting. Grid02 had a
small raw-JEPA advantage over the strongest control(+0.004826) but failed the
0.05/per-game gates and all intervals included zero. Its primary gain was
exact-state representation, not successful latent planning. Original v2/v2.1
sources/results remain immutable. Read V22_LABEL_BUDGET_OPTION for prior-art
and scope limits; sibling residual reweighting is NOT part of this study.

## Changed scientific question and data-readiness gate

Hypothesis: recurrent latent prediction improves planning when nonterminal
oracle-label access is restricted and the same legally observed transitions
are available to all methods. This narrows the question to label efficiency;
it does not establish fully supervised superiority, new data acquisition
efficiency, novelty or a generally superior two-player model.

Use dataset01's existing509 training roots and209 development roots. Choose
25% or100% of training roots per game by sorting the SHA256 JSON digest of
`[271828, game, trajectory, state]` and taking ceil(fraction * root_count).
Selection uses no oracle values/errors. Seed271828 is fixed once for this
development study; optimizer seeds stay17/29/43. The full-label arm is a planned
sensitivity comparison, not an alternative primary regime.

Reveal each selected root's complete legal depth2 closure. Label availability
is global by game-specific canonical symmetry/role state key, so a known state
is known at every occurrence. Terminal utility is free from the rules and
available everywhere; terminal policy is absent. Report selected-root counts,
unique canonical nonterminal value/policy counts, free terminal labels and
unlabeled state counts by game and horizon. Root25% is not state-label25%.
Require at least50% of unique nonterminal training states remain unlabeled in
each game of the scarce arm; otherwise stop this design before fitting.

This is simulated restricted label access on an already oracle-admitted and
fully solved bank. All original solver costs remain reported. Claim no actual
oracle-compute saving or oracle-free acquisition. No new external data/license.

## Redacted artifacts and model interface

Create fresh immutable training-only artifacts for scarce/full arms. Each has
roots,nodes,forks and a manifest with parent fingerprint, mask seed/fraction,
selected independent root identifiers, canonical label-mask hash, source/parser
version, byte hashes, counts and passing audit. Root identifiers are regenerated
from game/trajectory/state only: do not retain hashes containing hidden oracle
labels. Remove root oracle_values, beyond_depth and other label-derived metadata.
Remove all node action_values. A hidden nonterminal value is stored0 with
value_labelled=false; hidden policy has optimal=[] and policy_labelled=false.
Known labels are copied exactly. No hidden label survives in caches/metrics.

Preserve legal actions, state/player, transitions and valid horizon masks.
Data preparation also materializes an immutable development-only export. The
trainer receives only the redacted training artifacts and that separate export,
never the full parent path/file (even a loader that filters it after parsing is
insufficient). It cannot use the parent training oracle fields for metrics,
sampling or auxiliary targets. Loaders reject selection/final and reconstruct
rules, transitions and hashes. Parent split audit remains binding. Frozen
augmentation is coherent on all states/actions/policies; label masks are not
features and are unchanged by symmetry.

Batch extends the existing six arrays with boolean value_labelled[N,3] and
policy_labelled[N,3]. Both imply valid; policy_labelled also implies nonterminal.
Missing labels do not remove real future latent targets. Encoded value MSE and
policy CE divide by their available-label counts, respectively; zero labels
gives exactly zero supervised loss/gradient. Predicted successor-value MSE uses
the respective horizon's available oracle labels, coefficient0.25. Count all
denominators explicitly. Hidden placeholders must have zero targets/mass.

## Model and controls

Keep shared198->64->32 encoder, recurrent H1/H2 dynamics, heads, initialization,
Adam, gradient cap, EMA0.99 and variance rule from METHOD_V2. Use a new objective
version and atomic checkpoint format. Every model stores EMA encoder/projector
and an EMA value head; update after the online step, no target gradients.

Six families:

- direct: available encoded policy/value labels, no dynamics auxiliary.
- value-dynamics: add available successor-value labels, unchanged recurrence.
- decoded: same supervision plus feature reconstruction on ALL real successors,
  coefficient0.1 (its best grid02 auxiliary weight).
- raw-jepa: same supervision plus raw EMA latent MSE on ALL real successors,
  coefficient0.1 (best eligible JEPA family/weight in grid02).
- ema-value: same supervision plus0.25 MSE to detached EMA encoder/value-head
  estimates on genuinely UNLABELED successors. Known successors use only their
  oracle value term. At100% labels this equals value-dynamics online updates.
  For each horizon normalize oracle and pseudo-value sums separately by their
  respective available-label/unlabeled counts; an empty subset contributes0.
  Thus the mixed case adds0.25 mean oracle error plus0.25 mean pseudo error,
  rather than pooling their denominators.
- raw-no-response: raw-jepa with ONLY second/opponent action zeroed; actual
  successor features and first own action remain. Attribution-only candidate.

The stronger EMA-value control uses the same unlabeled transitions, EMA rate,
augmentation and labeled anchors. Its pseudo-values come from its own teacher,
not a full-label checkpoint or oracle. Teacher self-confirmation/collapse are
risks measured against development. No projected-JEPA head or capacity change
is included; choosing raw JEPA is an adaptive decision from completed grid02.

## Frozen finite grid and reporting

Two fractions x six families x two learning rates(0.001,0.0003) x three seeds
=72 cells. Fixed auxiliary weights above; no selective expansion.40epochs,
16forkdraws/root, balanced games, batch128, identical epoch sampling/augmentation
across all families AND fractions for each seed. Regenerated root IDs change
ordering relative to grid02; historical comparisons are not a paired causal
estimate. Preserve all schedule/mask/source/config/checkpoint hashes. One CPU
BLAS/OMP thread, serial runs,180s/cell,3GB aggregate output cap. Failures or
missing decisions make the screen inconclusive; no early-epoch/seed selection.

Choose one global learning rate per family from the PRIMARY scarce arm using
equal-game exact regret across three seeds, tie within1e-12 prefers0.0003. Apply
those same selected rates to the full-label sensitivity arm. Also show all
full-label cells transparently, without choosing the better fraction as primary.
Eligible candidate is raw-jepa only. It must improve by at least0.05 against
the strongest of direct,value-dynamics,decoded,ema-value, improve in both games
versus each, and have favorable paired aggregate effects in at least2/3 seeds
against each. The existing unprojected collapse thresholds apply. A failed
selected control cannot be bypassed. Raw-no-response remains attribution only.

Keep both exact/hybrid depth2 tracks, all209 roots, fixed ordering, node4096/
time1s caps and all fixed zero/untrained controls. Report every per-game/seed
value/policy/geometry/horizon metric, counts and resource scope.2000-replicate
paired hierarchical development bootstrap seed901 resamples seeds and roots,
not label masks. State that intervals condition on one fixed label mask and
do not correct adaptive research. No selection/final predictions.

A pass nominates a candidate for independent mask/seed replication and separately
frozen selection/confirmation; it is not proof or Q1 readiness. If useful gains
vanish against EMA-value/decoded, reject a JEPA-specific explanation. If all
auxiliaries benefit similarly, attribute the result to unlabeled transition
learning. Any next design requires a new hypothesis; do not weaken these gates.
