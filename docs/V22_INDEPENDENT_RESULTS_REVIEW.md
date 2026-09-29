# Independent review of v2.2 development grid 03

Reviewed 2026-09-29 after completion, by the independent-audit agent. This is an
independent implementation/results check within the project, not a third-party
replication. **Engineering verification passed; the restricted-label JEPA
promotion screen failed.** No training or neural predictions were rerun.

## Identities and access boundary

- Frozen source: `9e3d10bb3d01f4761db552ec6b2d7241957cf2e0`.
- Run directory: `chess_data/v22-grid-03/`.
- Ledger SHA-256: `660fe61f7612ed3ca69ff7b9dcb5bb91a3c4cf4c656c05c6332df412f29c1f26`.
- Control receipt SHA-256: `d968602ee5ff3bd163cbffb13021072e41dc029a622ff5ed43a31ea5600a4f4d`.
- Scarce artifact fingerprint: `dc81db9ab2d67d2905156fb328fe80369eb76bb4d5b140ebe041e68a578ebfab`.
- Full artifact fingerprint: `73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18`.
- Standalone development fingerprint: `bbfc41fc34e1e346a9dc5905f9f686bb61582e4a63f363d76ea2406088235617`.

Only the standalone scarce/full training and development artifacts were loaded.
The parent dataset file, selection split and final split were not opened. The
existing parent identity and readiness evidence are documented in
[V22_PREFIT_REVIEW](V22_PREFIT_REVIEW.md). Both training arms retain the same
509 roots and legal-fork exposure; the evaluation schedule has 209 development
roots. Scarce nonterminal states remain 75.5479% unknown in connect4 and 74.5408%
unknown in Reversi6 under the fixed, previously audited mask.

## Complete verification and replay

All **72 declared cells** completed. Each has 40 epochs, 2,640 optimizer updates
and 334,080 sampled fork draws: **190,080 total updates** and **24,053,760 repeated
fork draws**. These are exposure counts, not independent samples. The review
verified **30,096 learned decisions** and **836 fixed-control decisions**.
All are complete, with zero failed, missing or censored decisions. No model
crossed the declared unprojected collapse thresholds. Selection/final prediction
counters remain **0/0**.

Separate Python calculations over original JSON/NPZ artifacts verified every
source, receipt, checkpoint and embedded tensor hash; finite tensors; source,
dataset and config identities; bounded budget totals; epoch/step consistency;
and complete configuration inventory. Saved actions were checked against the
standalone development legal-action list and exact oracle labels. Regret and
optimal-action flags were independently recomputed; first-maximum tie-breaking
was checked against saved action estimates; ordered root/trajectory/track
schedules and node/time limits were verified. This does not recompute neural
estimates or independently resolve the oracle again.

The sampler and augmentation algorithms were independently replayed from the
frozen specification without calling production scheduling helpers. All
**120 seed-epoch plans** matched their index hashes, transform hashes and counts.
For both label fractions, masks were gathered from the standalone node records
at those exact sampled indices. The review then independently reconstructed and
matched **all 2,880 run-epoch label/target count dictionaries**, including encoded,
policy/value available/unavailable, terminal, missing-horizon, latent-target and
EMA-pseudo-value counts. Direct-model disabled horizon counts and full-arm zero
pseudo-target counts were checked explicitly. No model fitting was involved.

| Seed | Sampling schedule SHA-256 | Augmentation schedule SHA-256 |
| --- | --- | --- |
| 17 | `4063a7a551000796b89f21984af41600c09ec900f868dacc131960c943a06365` | `6a6bbbab8976453f5e5e0dce3f81a70f96b19749a57446fa142b44b20209472d` |
| 29 | `e4669b6c56c99f66a1580e23e94ea8f82dcd8724a8d0974cdc81a9b7c4584958` | `a78355bd8f9ae6cfc6eee95026095a6485c047f3421ad77a97c16bce75ed8804` |
| 43 | `2eccaf965ce78dda55d2d59cd74f515100a3cc8d633a6beab230cf1b4afac89c` | `8a445778e738dfdbc5b340cd8eed322fed35b54dcd04e25ca9930935ba77593c` |

These schedule identities match across all families and both fractions within
each seed. They differ from grid02, as expected after state-only root re-keying.

The strongest control's full-label equivalence was checked on real checkpoints:
for **all six matched learning-rate/seed pairs**, EMA-value and value-dynamics
have **all 59 stored tensors bitwise identical**, covering online parameters,
EMA state and Adam moments. Each pair also has **418 identical saved actions,
regrets and action-estimate vectors**. Variant/config metadata and runtime
measurements naturally differ. This verifies the promised equality when no
unlabeled successor requires a pseudo-value target.

## Independently recomputed complete results

Mean exact-action regret, lower is better, across seeds 17/29/43. The primary
metric gives each game equal weight; connect4 has 107 roots and Reversi6 102.
Hybrid columns use the same configuration, without separate selection.
Weights are fixed at .1 for decoded/raw-jepa/raw-no-response and canonical1
for direct/value-dynamics/ema-value.

| Root-label fraction | Family | Learning rate | Connect4 exact | Reversi6 exact | Equal-game exact | Connect4 hybrid | Reversi6 hybrid |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.25 | direct | 0.001 | 0.196262 | 0.415033 | 0.305647 | 0.196262 | 0.415033 |
| 0.25 | direct | 0.0003 | 0.149533 | 0.418301 | 0.283917 | 0.149533 | 0.418301 |
| 0.25 | value-dynamics | 0.001 | 0.196262 | 0.444444 | 0.320353 | 0.196262 | 0.496732 |
| 0.25 | value-dynamics | 0.0003 | 0.165109 | 0.450980 | 0.308045 | 0.168224 | 0.522876 |
| 0.25 | decoded | 0.001 | 0.180685 | 0.434641 | 0.307663 | 0.227414 | 0.486928 |
| 0.25 | decoded | 0.0003 | 0.168224 | 0.428105 | 0.298164 | 0.152648 | 0.500000 |
| 0.25 | raw-jepa | 0.001 | 0.165109 | 0.421569 | 0.293339 | 0.218069 | 0.506536 |
| 0.25 | raw-jepa | 0.0003 | 0.165109 | 0.428105 | 0.296607 | 0.165109 | 0.516340 |
| 0.25 | ema-value | 0.001 | 0.186916 | 0.444444 | 0.315680 | 0.202492 | 0.490196 |
| 0.25 | ema-value | 0.0003 | 0.158879 | 0.437908 | 0.298394 | 0.199377 | 0.568627 |
| 0.25 | raw-no-response | 0.001 | 0.155763 | 0.411765 | 0.283764 | 0.186916 | 0.594771 |
| 0.25 | raw-no-response | 0.0003 | 0.165109 | 0.444444 | 0.304777 | 0.152648 | 0.591503 |
| 1 | direct | 0.001 | 0.112150 | 0.281046 | 0.196598 | 0.112150 | 0.281046 |
| 1 | direct | 0.0003 | 0.161994 | 0.287582 | 0.224788 | 0.161994 | 0.287582 |
| 1 | value-dynamics | 0.001 | 0.124611 | 0.297386 | 0.210998 | 0.124611 | 0.470588 |
| 1 | value-dynamics | 0.0003 | 0.168224 | 0.330065 | 0.249145 | 0.146417 | 0.450980 |
| 1 | decoded | 0.001 | 0.121495 | 0.300654 | 0.211074 | 0.133956 | 0.470588 |
| 1 | decoded | 0.0003 | 0.165109 | 0.346405 | 0.255757 | 0.152648 | 0.473856 |
| 1 | raw-jepa | 0.001 | 0.133956 | 0.277778 | 0.205867 | 0.127726 | 0.457516 |
| 1 | raw-jepa | 0.0003 | 0.168224 | 0.330065 | 0.249145 | 0.140187 | 0.450980 |
| 1 | ema-value | 0.001 | 0.124611 | 0.297386 | 0.210998 | 0.124611 | 0.470588 |
| 1 | ema-value | 0.0003 | 0.168224 | 0.330065 | 0.249145 | 0.146417 | 0.450980 |
| 1 | raw-no-response | 0.001 | 0.137072 | 0.284314 | 0.210693 | 0.124611 | 0.545752 |
| 1 | raw-no-response | 0.0003 | 0.171340 | 0.330065 | 0.250702 | 0.133956 | 0.539216 |

Primary scarce-arm tuning selects .0003 for direct, value-dynamics, decoded and
EMA-value; .001 for raw-jepa and raw-no-response. Raw-jepa is the only eligible
candidate. Its exact regret is **0.293338830859**, versus the strongest control,
direct, at **0.283916681938**. The difference favoring JEPA is **-0.009422148922**:
the candidate is worse, not close to the frozen +0.05 improvement gate.

Positive differences below favor raw-jepa. All were recomputed independently
from saved decisions. The 2,000-replicate bootstrap uses seed901, paired root
draws and common model-seed draws across both games. It conditions on the one
fixed label mask and does not correct adaptive development.

| Tuned scarce control | Aggregate improvement | Connect4 improvement | Reversi6 improvement | Paired seed effects (17,29,43) | Descriptive development 95% interval |
| --- | ---: | ---: | ---: | --- | --- |
| direct | -0.009422 | -0.015576 | -0.003268 | 0.000458, 0.020295, -0.049020 | [-0.075730, 0.047922] |
| value-dynamics | 0.014706 | 0.000000 | 0.029412 | 0.043889, 0.029870, -0.029641 | [-0.051831, 0.081014] |
| decoded | 0.004826 | 0.003115 | 0.006536 | 0.024281, 0.015164, -0.024968 | [-0.055340, 0.063496] |
| ema-value | 0.005055 | -0.006231 | 0.016340 | 0.029641, 0.020066, -0.034543 | [-0.059770, 0.069122] |

Every interval spans zero. The candidate loses to direct in both games; ties
value-dynamics on connect4; and loses to EMA-value on connect4. These outcomes
violate the positive each-game requirement in addition to the failed aggregate
margin. Two favorable paired seeds cannot override those failures. The strict
production report also returns `not_promoted` with zero verification errors;
the independent numbers agree.

## Full-label sensitivity cannot rescue the primary result

The prospectively specified sensitivity analysis carries scarce-selected learning
rates into the full arm. At those rates, raw-jepa scores .205867 and direct
.224788, but that is a **secondary comparison with different learning rates
chosen in the scarce regime**, not full-label superiority. The complete table
shows full-label direct at .001 scores **.196598**, better than raw-jepa at .001.
The full arm cannot replace the failed primary scarce arm or be selectively
retuned afterward to promote a candidate.

The scarce candidate's hybrid regret also worsens relative to its own exact
track in both games (.218069 versus .165109 on connect4; .506536 versus .421569
on Reversi6). Raw-no-response can have competitive exact-state scores while its
Reversi6 hybrid track remains weak. These observations reinforce the need to
separate representation regularization from useful latent-dynamics planning.

## Resources and interpretation

Recorded training/checkpoint-verification intervals sum to **1102.611040 seconds**,
with **11.929624–23.861409 seconds** per cell, all below180 seconds. The ledger
reports **123,061,300 array bytes** and **251,486,208 bytes process-lifetime peak
RSS**, including preprocessing and previous cells. Run artifacts occupied
**78,628,950 bytes** at review. These are not total research cost, per-model peak
memory, equal active compute, or a hardware-normalized efficiency comparison.

This third development cycle supplies a reproducible negative result for the
specific restricted-label hypothesis/configurations. It does not disprove all
JEPA approaches. The fixed bank was already fully solved and admitted using
oracle difficulty predicates, so redaction establishes simulated label access,
not real oracle-compute savings. The two fixed endgame families, exposed
development roots and three model seeds do not establish whole-game strength,
unseen-game transfer, independent confirmation, novelty or Q1 readiness.

Preserve all three failed development screens. A further design needs a new
bounded hypothesis and equally informative controls; the selection/final sets
remain protected. No gate, baseline, label fraction or primary metric was
changed after seeing this grid.
