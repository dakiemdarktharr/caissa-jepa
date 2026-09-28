# Grid01 negative result and training-only mechanism probes

Date: 2026-09-29. Status: exploratory diagnosis after development evaluation,
before the v2.1 amendment. No causal explanation or improvement is established.
No weights were updated and no source/data files were changed by these probes.
Neither selection nor final examples were loaded or scored.

## Artifacts and observed results

The verified development report is locally retained at
`chess_data/v2-grid-01-report/report.json` and `report.md`. It points to every
checkpoint/receipt/hash in `chess_data/v2-grid-01/`. Dataset:
`chess_data/v2-forks-01/`. Seeds:17,29,43. Frozen method: `METHOD_V2.md`.

| Globally tuned family | Rate | Equal-game exact regret |
| --- | ---: | ---: |
| Direct | 0.0003 | 0.272402 |
| Value dynamics | 0.0003 | 0.247664 |
| Decoded dynamics | 0.0003 | 0.270234 |
| Projected recurrent JEPA | 0.001 | 0.249145 |
| Raw JEPA | 0.001 | 0.255757 |
| No-response attribution | 0.001 | 0.254047 |

JEPA did not pass the frozen promotion screen. Its improvement versus tuned
value dynamics was -0.001481 with descriptive paired development bootstrap
interval[-0.049433,0.048714]. Per-game mean regrets for projected JEPA are
0.168224 Connect4 and0.330065 Reversi; value dynamics gives0.161994 and0.333333.
The small Reversi improvement does not compensate for Connect4 or establish a
reliable effect. All36 cells completed, and this study did not open final data.

Training histories show a substantial encoded-value generalization gap. At
epoch40, projected JEPA(rate0.001) training value MSE across seeds is
0.34175,0.33301,0.33567; its development Connect4/Reversi MSE pairs are
(0.50486,0.58429), (0.51753,0.59098), (0.48186,0.58914). Raw JEPA training MSE is
0.31361,0.31678,0.31611, with development pairs
(0.52428,0.57339), (0.52746,0.61954), (0.52013,0.61757).
Training and development state distributions/weights differ, so these gaps are
diagnostic rather than an unbiased estimate of an overfitting parameter.

Raw-JEPA H2 development online-latent MSE is0.02425,0.02734,0.02589 for Connect4
and0.08215,0.08492,0.08320 for Reversi. Corresponding projected-JEPA unprojected
H2 errors are0.22498,0.27253,0.26648 and0.26823,0.30777,0.31672. The lower raw
error does not produce better planning. These are different learned coordinate
spaces and different objectives, so their numeric errors are not directly
commensurate; the observation rejects using latent MSE alone as promotion proof.

## Probe A: encoder gradient directions

Protocol: load the saved `rjepa-lr0.001-s{17,29,43}` checkpoints through strict
identity loading. Use only audited training forks. For each game, select256
forks without replacement once with NumPy RNG seed20260929, iterating games in
sorted order. Reuse the same sampled forks for all checkpoint seeds. Compute
gradients without an optimizer step; EMA stays fixed. Concatenate the four
encoder parameter tensors. A comparison model has identical parameters/EMA and
`jepa_weight=0`; the difference of gradients isolates the existing JEPA term.
"Supervised" below includes shared encoded policy/value, predicted value and
the shared variance term. Cosines are ordinary vector inner products divided
by the two norms; norm ratio is auxiliary norm / supervised norm.

| Checkpoint seed | Connect4 aux/supervised cosine | Connect4 norm ratio | Reversi cosine | Reversi norm ratio | Cross-game full cosine | Cross-game supervised cosine |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 17 | -0.071003 | 0.601868 | 0.251295 | 0.856680 | 0.184177 | 0.175452 |
| 29 | 0.232160 | 0.162328 | 0.026907 | 0.693702 | -0.283694 | -0.366293 |
| 43 | 0.293241 | 0.303332 | -0.018756 | 0.488948 | 0.320766 | 0.368008 |

There is no consistent sign of cross-game gradient conflict or of JEPA opposing
shared supervision in this probe. This does not justify gradient surgery or
separate game encoders. Auxiliary gradients are substantial, especially for
Reversi, making an auxiliary-weight study reasonable. These are local gradients
on one bounded training sample at the final checkpoints, not estimates over
all minibatches or a causal account of training behavior.

## Probe B: complete sibling-group residual decomposition

Protocol: restart RNG at seed20260929. Group audited training forks by
`(game, root_id, own_action)`; require an existing H2 target and at least two
replies. Sort group keys, choose128 groups without replacement per game,
and reuse them for all three saved projected-JEPA checkpoints. Use the full
legal reply group, not independently sampled reply fragments.

For reply b, compute recurrent H2 prediction, online affine projection and
prediction head, and normalize with the frozen epsilon1e-6. The target uses
the frozen EMA encoder/projector and the same normalization. Define residual
`e_b = normalized_prediction_b - normalized_EMA_target_b`.

For each group compute `mean_b ||e_b||^2`,
`mean_b ||e_b-mean(e)||^2`, and `||mean(e)||^2`.
The first is exactly the sum of the other two. Table errors average groups
equally. Mean-residual fraction is the sum of group-mean squared norms divided
by the sum of group total errors. This measures objective allocation, not
whether the group mean contains decision-relevant information.

| Seed | Game | Groups | Unequal-value groups | Total squared error | Centered squared error | Mean-residual fraction |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 17 | Connect4 | 128 | 77 | 0.040072897 | 0.009515382 | 0.762548 |
| 29 | Connect4 | 128 | 77 | 0.036143916 | 0.008578259 | 0.762664 |
| 43 | Connect4 | 128 | 77 | 0.042691815 | 0.009644189 | 0.774097 |
| 17 | Reversi | 128 | 56 | 0.199091348 | 0.082232223 | 0.586962 |
| 29 | Reversi | 128 | 56 | 0.164228998 | 0.063306907 | 0.614521 |
| 43 | Reversi | 128 | 56 | 0.190524820 | 0.075178445 | 0.605414 |

Most residual energy lies in a common sibling-group offset. A later candidate
could change the relative weights on the centered and mean-residual terms,
while preserving absolute value supervision. This is a hypothesis only:
discarding common offsets might hurt comparisons between own actions. Uniform
all-pair difference matching is algebraically centered residual MSE up to scale;
it must not be presented as an independent new source of relational information.

## Next decision and prospective safeguards

The chosen next finite cycle is **v2.1 symmetry augmentation plus auxiliary-weight
tuning**, frozen in `METHOD_V21.md`. It addresses the observed generalization
gap with coherent valid game symmetries and offers all controls the same
augmentation. SPR is direct prior art; neither this workflow nor a potential
gain establishes uniqueness. Capacity, architecture and dataset remain fixed.

The sibling-weighting idea is reserved for a separately declared future cycle.
It requires complete-group sampling shared by every comparator, ordinary and
scaled pointwise-JEPA controls, random grouping with matched sizes, and strong
value-dynamics/decoded/direct controls. Any supervised reply-ranking term must
be available to the corresponding baselines. The old best value-dynamics result
must remain visible. No development outcome authorizes weakening promotion
criteria, removing failures or treating the exposed development set as final.
