# Independent review of v2 development grid 01

Reviewed 2026-09-29 by the independent-audit agent. This is an independent
implementation/results review within the same project, not an external laboratory
replication or third-party referee. No training or model predictions were rerun.

**Verdict: engineering verification passed; JEPA promotion screen failed.** The
best eligible JEPA configuration does not beat the strongest tuned non-JEPA
predictive control. Preserve this as a negative development result. Neither the
selection nor final set should be opened because of this result.

## Evidence identity and checks

- Frozen source commit: `325afc0502911314d585a659ce456bb150b6231e`.
- Local run directory: `chess_data/v2-grid-01/`.
- Local dataset: `chess_data/v2-forks-01/`.
- Dataset fingerprint: `3297fa10abd296299ccff6a80238a7db20b883369f0603a03b5f33983ccc57c2`.
- Final ledger SHA-256: `da670558ae479fc25af7b1b316e3b4b2078f92843a267b8b74ae9c99a162aa7d`.
- Fixed-control receipt SHA-256: `f6e80a987b9df74c6c13968fde9161a10683d37c3e2c2644575939414bedb6ba`.

The review used separate Python calculations over the original JSON/NPZ artifacts,
not the report module's aggregation or promotion functions. It checked every
source file hash, run receipt hash, checkpoint hash and embedded tensor hash;
finite tensors; checkpoint/config/data/source identities; complete epoch history;
budget identities and totals; and identical per-seed sampling schedules across
all methods and learning rates. Original development labels were loaded through
the restricted development loader. For every saved decision it checked action
legality, recomputed regret from that action's exact oracle value, checked the
optimal-action flag and first-maximum tie-break against saved action estimates,
and verified complete root/track/trajectory order and node/time caps. It did not
recompute neural action estimates or independently resolve the entire oracle bank.
The bank's independent rule/oracle and closure checks were reviewed previously.

All **36 runs** completed 40 epochs, **2,640 optimizer updates** and **334,080 sampled
forks per run**. This totals 95,040 updates and 12,026,880 sampled forks, including
repeated sampling; these are not unique states or independent observations.
Every epoch contains 8,352 fork draws and 66 minibatches. There are 509 unique
training roots: 248 connect4 and 261 Reversi6. Minority-game roots are repeated as
declared to equalize game sampling. The review verified **15,048 learned-model
decisions** (36 runs x 209 roots x 2 tracks) and **836 fixed-control decisions**.
There were zero missing, censored or failed decisions and no thresholded collapse
finding. Selection/final prediction counters remain **0/0**.

Paired training schedule hashes, covering all 40 epoch schedule receipts:

| Seed | SHA-256 |
| --- | --- |
| 17 | `3c4df4146842b35f3b28b84488c395991884083db8e4cf273acaf8804fb6d92a` |
| 29 | `62b24d49a9a0e9ca73c7676f1808318993fefecb20c84a6308bee3c2b71695a2` |
| 43 | `0e4448efa1f2d77b470a89beecc0d8a29ac08e1f75c78d10c1a3709e926f013d` |

## Independently recomputed results

Mean exact-action regret, lower is better, averaged over the three seeds. The
primary aggregate weights the two games equally. Connect4 has 107 development
roots and Reversi6 has 102; no denominator is reduced. Asterisks mark each
family's globally selected learning rate under the frozen primary metric.

| Family | Learning rate | Connect4 exact | Reversi6 exact | Equal-game exact | Connect4 hybrid | Reversi6 hybrid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| direct | .001 | .177570 | .379085 | .278328 | .177570 | .379085 |
| direct | .0003* | .152648 | .392157 | .272402 | .152648 | .392157 |
| value-dynamics | .001 | .205607 | .392157 | .298882 | .133956 | .437908 |
| value-dynamics | .0003* | .161994 | .333333 | .247664 | .146417 | .486928 |
| decoded | .001 | .196262 | .379085 | .287673 | .124611 | .460784 |
| decoded | .0003* | .174455 | .366013 | .270234 | .158879 | .506536 |
| rjepa | .001* | .168224 | .330065 | .249145 | .149533 | .450980 |
| rjepa | .0003 | .137072 | .395425 | .266248 | .149533 | .506536 |
| raw-jepa | .001* | .165109 | .346405 | .255757 | .146417 | .428105 |
| raw-jepa | .0003 | .143302 | .369281 | .256292 | .146417 | .486928 |
| no-response | .001* | .168224 | .339869 | .254047 | .146417 | .607843 |
| no-response | .0003 | .143302 | .382353 | .262828 | .149533 | .614379 |

The frozen eligible-family rule selects rjepa at .001. The strongest tuned control
is value-dynamics at .0003. Its regret minus rjepa regret is **-0.001481**, so JEPA
is slightly worse overall, far from the required +0.05 margin. The corresponding
per-game differences are **-0.006231** on connect4 and **+0.003268** on Reversi6.
The required positive effect in both games also fails. Relative to direct,
connect4 likewise worsens (-0.015576), despite a lower equal-game mean.

Independent paired bootstrap recomputation used the frozen 2,000 replicates,
seed 901, common training-seed draws across both games, and common trajectory
draws across paired methods and sampled seeds within each game. Positive values
below favor rjepa; intervals are descriptive development intervals, uncorrected
for adaptive family/rate selection.

| Tuned comparator | Improvement | Paired seed effects (17, 29, 43) | Development 95% interval |
| --- | ---: | --- | --- |
| direct | +.023258 | +.014706, +.010720, +.044347 | [-.027360, +.082801] |
| decoded | +.021089 | +.024052, +.034314, +.004902 | [-.028810, +.074407] |
| value-dynamics | -.001481 | +.009575, +.000687, -.014706 | [-.049433, +.048714] |

All intervals span zero. Two favorable paired seeds versus value-dynamics do not
override the failed aggregate and per-game criteria. No threshold or comparator
was changed after viewing these results.

The zero-leaf exact-rule baseline has regret .317757 on connect4 and .696078 on
Reversi6. Learning helps relative to that fixed baseline, but that is not evidence
of a JEPA-specific advantage. The pronounced Reversi6 hybrid penalty from removing
reply conditioning (.607843 versus .450980 at the same .001 rate) is a useful
exploratory mechanism observation; it does not establish JEPA superiority over
the non-JEPA predictive controls. Rjepa hybrid Reversi6 regret also exceeds tuned
direct exact/hybrid regret (.392157). Whole-game strength was not measured.

## Diagnostics, resources and interpretation limits

All predeclared geometry gates passed. Across the spaces eligible for those
gates, the smallest effective rank was 5.678678 (no-response .0003, seed43,
connect4 projected) and the smallest median dimension standard deviation was
.205672 (rjepa .0003, seed43, connect4 unprojected). These coarse noncollapse
checks do not establish useful latent dynamics or calibrated uncertainty.

Summed recorded training/checkpoint-verification time was 513.286501 seconds;
individual runs ranged from 11.690708 to 18.316183 seconds. These are recorded
training intervals, not total research or wall-clock end-to-end cost. The final
ledger reports 71,839,390 array bytes and 213,417,984 bytes process-lifetime peak
RSS, including preprocessing and prior cells. Run-directory artifacts occupied
36,905,709 bytes at review. No per-model memory-efficiency claim follows from
process-lifetime RSS, and equal optimizer steps do not imply equal active compute.

Earlier independent closure analysis found 209 singleton closure components
within development, as well as no canonical or encoded-feature overlap across
splits and no held-out overlap with v1 training. Nevertheless, 209 roots and three
training seeds support only an exploratory screen, not reliable confirmation of
a .05 effect. Repeated seed-root scores are not independent new trajectories.
The root distribution was deliberately admitted using oracle difficulty predicates
at 5..8 empty cells. Conclusions are restricted to these two fixed endgame game
families and this sampling design; there is no whole-game or unseen-family claim.

Recommended next step: preserve this grid and its failed screen, diagnose the
development-only representation/rollout gap, then freeze a new finite hypothesis
and equally informative controls before any further fitting. Any new development
result must be labeled adaptive. The current grid does not justify selection/final
evaluation, publication-readiness, novelty, or an established JEPA advantage.
