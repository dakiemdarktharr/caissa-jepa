# V2.1 prospective symmetry and auxiliary-weight development amendment

Frozen2026-09-29 after grid01 and before this implementation/fitting. V2 grid01
remains unchanged and failed promotion. This is a new adaptive development cycle,
not a fresh independent validation set or a unique new JEPA objective.

## Evidence and hypothesis

The strongest non-JEPA value-dynamics control matched/exceeded JEPA. There was
no collapse, and JEPA's training/development gap was substantial. The flattened
encoder has no built-in spatial parameter sharing. Across three checkpoint seeds,
a bounded training-only gradient probe found no consistent game/auxiliary
gradient conflict; this does not motivate gradient surgery or separate encoders.

Hypothesis: coherent legal-symmetry augmentation improves generalization, and
a smaller latent auxiliary weight preserves useful prediction while reducing
unhelpful regularization. Controls receive the same augmentation and weight
opportunity where the auxiliary exists. Any shared augmentation gain must not
be attributed to JEPA. SPR is direct prior art; novelty remains unestablished.

## Frozen changes

Keep dataset01, split/labels, architecture, initialization, optimizer, horizons,
EMA,40epochs,16forkdraws/root, game balance and exact/hybrid evaluator unchanged.
Only training inputs are augmented. On each sampled complete fork draw choose
one uniform valid board symmetry and apply it coherently to all three state
features, both actions, legal masks and policy targets. Terminal/missing slots,
value perspective and metadata remain unchanged. Connect4 permits identity and
horizontal reflection; Reversi6 permits its eight dihedral symmetries. Pass
action64 remains64. Do not rotate gravity or reflect only one transition endpoint.

The existing canonical-closure audit already quotients these symmetries, so
augmentation does not create a new held-out overlap. Test transformed features,
actions, legal/policy masks against direct adapter transforms and transition
commutation, including missing-H2 and forced pass. No new oracle query/label.

Sampling indices use the frozen v2 seed/epoch scheduler. Symmetry choices use a
separate RNG SeedSequence([seed,epoch,2211]); iterate sampled fork draws in order,
uniform integer from that draw's game transform count. Save both schedule and
augmentation-plan hashes per epoch. Identical across all configurations sharing
a training seed; no augmentation during evaluation.

Finite grid: direct/value-dynamics at both learning rates0.001/0.0003; decoded,
rjepa,raw-jepa,no-response at both rates and auxiliary weights0.1/1.0. Seeds
17/29/43:60 cells. Weight only changes existing latent or reconstruction term;
encoded supervision, predicted-value0.25 and variance weights stay fixed. All
families retain equal40epoch updates/data coverage, with different active compute.
No capacity increase, best-epoch selection or post-hoc run replacement.

One CPU BLAS/OMP thread, serial runs,180s per cell,3GB new-artifact cap. Retain
atomic checkpoint/EMA/Adam state and strict source/data/config/method identities.
Unaccounted interrupted compute blocks silent grid resume. Record process peak
RSS with lifetime scope and all failures. Every60 cells and decision must finish;
otherwise the screen is inconclusive.

## Selection and interpretation

Development roots remain the same209 exposed roots. Select one GLOBAL(rate,
weight) configuration per family on equal-game exact mean regret across all
three seeds. Ties within1e-12 choose smaller rate, then smaller weight. Direct
and value-dynamics have no auxiliary and use the canonical stored weight1.
Select best eligible rjepa/raw-jepa, preferring rjepa on an exact tie. Keep the
same collapse gates,0.05 strongest-control margin, positive each-game gain
versus all three tuned control families, and at least2/3 favorable paired seeds.
Any selected control collapse makes the screen inconclusive. No-response is
attribution only. All candidates are compared with the augmented tuned controls;
grid01 numbers are historical comparisons, not the primary comparator.

Retain the2000-replicate seed901 paired hierarchical development bootstrap and
all exact/hybrid, policy/value, geometry, counts, runtime/hash metrics. Intervals
do not correct repeated development use. No selection/final predictions. A pass
would nominate a candidate for a separate frozen selection/replication protocol,
not prove JEPA superiority or Q1 readiness. Failure motivates a separately
declared decision-aligned/root-grouped hypothesis, not threshold weakening.
