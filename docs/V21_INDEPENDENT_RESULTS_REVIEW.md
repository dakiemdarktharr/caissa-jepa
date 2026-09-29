# Independent review of v2.1 development grid 02

Reviewed 2026-09-29 by the independent-audit agent. This is a separate
implementation/results review inside the same project, not a third-party
replication. All checks began after the grid's ledger reported complete. No
training, neural predictions, or selection/final scoring was performed.

**Verdict: engineering verification passed; the frozen JEPA promotion screen
failed again.** Symmetry augmentation improves historical development scores
for several families, including controls. The best eligible JEPA improvement
over the strongest augmented control is only +0.004826, below the frozen +0.05
margin, and a required per-game comparison also fails.

## Artifact identity and verification

- Source commit: `086e839d5f9ed1559cce16a9f8ff9fdd6b843191`.
- Run directory: `chess_data/v21-grid-02/`.
- Dataset: `chess_data/v2-forks-01/`, fingerprint
  `3297fa10abd296299ccff6a80238a7db20b883369f0603a03b5f33983ccc57c2`.
- Final ledger SHA-256:
  `f372497b8de7e25cca3dd53c8db4d355987eddfda02071049274bb3db5bd7777`.
- Control receipt SHA-256:
  `b7fe320991c5e3276c212da46f0180a235ce07e7c2f96e393c3afd82c1d7d235`.

A separate Python calculation over original JSON/NPZ artifacts verified all
source, receipt, checkpoint and embedded tensor hashes; finite tensors;
source/config/data identities; budget totals; epoch/step consistency; paired
sampling/augmentation schedule hashes; and the complete declared inventory.
Aggregation, configuration selection and bootstrap were recomputed without
using the production report functions.

For each saved decision, the review checked the original development root,
trajectory and track order; action legality; regret independently recomputed
from the chosen action's oracle label; optimal-action indicator; first-maximum
tie-breaking against saved estimates; complete status; and node/time limits.
It did not recompute neural estimates or resolve the full oracle bank again.

All **60 cells** completed, each with 40 epochs, 2,640 updates and 334,080
sampled fork draws. Totals: **158,400 updates** and **20,044,800 fork draws**,
including repeated sampling. These are not unique-state or independent-sample
counts. The 509 training roots and 209 exposed development roots are unchanged.
All **25,080 learned decisions** and **836 fixed-control decisions** were
verified. There were **zero failed, missing or censored decisions**, zero
thresholded collapse findings, and **0 selection / 0 final predictions**.

## Independent sampling and augmentation replay

The review independently implemented the frozen seed/epoch algorithms from
the method, without importing the runtime scheduler or augmentation-plan helper.
It replayed **all 120 seed-epochs**, covering 1,002,240 sampled draw/transform
choices: root coverage, minority-game repetitions, uniform complete-fork draws,
shuffle, namespace 2201 sample RNG, and namespace 2211 transformation RNG.
Every sample-index hash, transformation hash, transformation count and epoch
binding matched. Each seed's plans were identical across its 20 configurations.
This verifies recorded plans and the reviewed runtime binding; it is not a
second optimization run.

The ordinary sampling schedule hashes are identical to grid01's hashes recorded
in [the v2 review](V2_INDEPENDENT_RESULTS_REVIEW.md). The new augmentation schedule
hashes, covering all 40 epoch receipts, are:

| Seed | SHA-256 |
| --- | --- |
| 17 | `631a3f1a9e79c391d82f8cce564715d31e31fb50be5ac48b03a68fa6bf230c7a` |
| 29 | `05063cca6835a14fd317a2c4b8e8058f4b6ddf84920b37e2c19b61444b832a4e` |
| 43 | `23b10ac9960004bbfde878a0dd0c60296acea3956e60f6107b73a922362f5c27` |

## Recomputed complete configuration table

Mean exact-action regret, lower is better, averaged over seeds 17/29/43.
The primary aggregate weights the games equally; connect4 has 107 roots and
Reversi6 has 102. All denominators are complete. Hybrid uses the same configuration;
it was not separately tuned or used to replace the primary metric.

| Family | Learning rate | Auxiliary weight | Connect4 exact | Reversi6 exact | Equal-game exact | Connect4 hybrid | Reversi6 hybrid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| direct | 0.001 | 1 | 0.149533 | 0.290850 | 0.220191 | 0.149533 | 0.290850 |
| direct | 0.0003 | 1 | 0.165109 | 0.287582 | 0.226345 | 0.165109 | 0.287582 |
| value-dynamics | 0.001 | 1 | 0.140187 | 0.284314 | 0.212250 | 0.112150 | 0.470588 |
| value-dynamics | 0.0003 | 1 | 0.161994 | 0.330065 | 0.246030 | 0.152648 | 0.460784 |
| decoded | 0.001 | 0.1 | 0.124611 | 0.307190 | 0.215900 | 0.112150 | 0.473856 |
| decoded | 0.001 | 1 | 0.155763 | 0.284314 | 0.220038 | 0.124611 | 0.483660 |
| decoded | 0.0003 | 0.1 | 0.161994 | 0.303922 | 0.232958 | 0.143302 | 0.490196 |
| decoded | 0.0003 | 1 | 0.146417 | 0.294118 | 0.220268 | 0.149533 | 0.470588 |
| rjepa | 0.001 | 0.1 | 0.161994 | 0.264706 | 0.213350 | 0.115265 | 0.437908 |
| rjepa | 0.001 | 1 | 0.177570 | 0.271242 | 0.224406 | 0.121495 | 0.460784 |
| rjepa | 0.0003 | 0.1 | 0.155763 | 0.284314 | 0.220038 | 0.137072 | 0.503268 |
| rjepa | 0.0003 | 1 | 0.158879 | 0.294118 | 0.226498 | 0.152648 | 0.470588 |
| raw-jepa | 0.001 | 0.1 | 0.137072 | 0.277778 | 0.207425 | 0.121495 | 0.496732 |
| raw-jepa | 0.001 | 1 | 0.143302 | 0.277778 | 0.210540 | 0.115265 | 0.411765 |
| raw-jepa | 0.0003 | 0.1 | 0.165109 | 0.307190 | 0.236149 | 0.146417 | 0.473856 |
| raw-jepa | 0.0003 | 1 | 0.161994 | 0.316993 | 0.239494 | 0.140187 | 0.447712 |
| no-response | 0.001 | 0.1 | 0.155763 | 0.261438 | 0.208601 | 0.099688 | 0.545752 |
| no-response | 0.001 | 1 | 0.161994 | 0.241830 | 0.201912 | 0.124611 | 0.549020 |
| no-response | 0.0003 | 0.1 | 0.149533 | 0.284314 | 0.216923 | 0.124611 | 0.558824 |
| no-response | 0.0003 | 1 | 0.158879 | 0.297386 | 0.228132 | 0.146417 | 0.552288 |

Frozen global tuning selects: direct (.001, 1), value-dynamics (.001, 1),
decoded (.001, .1), rjepa (.001, .1), raw-jepa (.001, .1), and no-response
(.001, 1). The eligible candidate is **raw-jepa (.001, .1)**, exact mean
**0.207424714434**. The strongest control is **value-dynamics (.001, 1)**,
exact mean **0.212250320689**. No-response is an attribution ablation and remains
ineligible under the frozen rule, despite its lower exact mean **0.201911917415**.

Positive differences below favor the selected raw-jepa candidate. Independent
paired bootstrap used 2,000 replicates, seed 901, common training-seed draws
across games, and common root draws across paired methods and sampled seeds.

| Tuned control | Equal-game improvement | Connect4 improvement | Reversi6 improvement | Paired seed effects (17,29,43) | Descriptive development 95% interval |
| --- | ---: | ---: | ---: | --- | --- |
| direct | 0.012766 | 0.012461 | 0.013072 | -0.014477, 0.028496, 0.024281 | [-0.028656, 0.054107] |
| decoded | 0.008475 | -0.012461 | 0.029412 | 0.000687, 0.010262, 0.014477 | [-0.025689, 0.046441] |
| value-dynamics | 0.004826 | 0.003115 | 0.006536 | -0.019150, 0.014706, 0.018921 | [-0.039003, 0.044845] |

All intervals span zero and do not correct adaptive selection or repeated
development-set use. Although the candidate has two favorable seeds against
direct and value-dynamics, its +0.004826 strongest-control margin fails +0.05.
Connect4 is also worse than decoded by 0.012461, violating the positive
each-game effect requirement. These are explicit failed criteria; no threshold,
baseline or eligible-family rule was changed after inspection.

## Scientific interpretation and resources

Historical best direct exact regret improves from grid01's .272402 to .220191;
value-dynamics improves from .247664 to .212250. These historical comparisons
reuse development roots and globally tuned rates, so they are exploratory
evidence of shared augmentation benefit, not isolated JEPA benefit.

The best eligible exact candidate has hybrid Reversi6 regret .496732, worse than
direct (.290850) and value-dynamics (.470588). Removing response conditioning
can yield competitive exact-state representation scores while substantially
harming recurrent Reversi6 planning: at rjepa/no-response rate .001 and weight1,
exact regrets are .271242/.241830 but hybrid regrets are .460784/.549020.
This pattern warns against inferring useful action-conditioned latent planning
from exact-state value improvements alone. It neither demonstrates JEPA
superiority nor disproves every possible JEPA design.

Recorded training/checkpoint-verification intervals sum to **916.426969 seconds**,
with individual runs **12.138252–24.120961 seconds**, all below 180 seconds.
This excludes portions of preprocessing, evaluation and the wider research
workflow. The ledger reports **71,839,390 array bytes** and **215,351,296 bytes
process-lifetime peak RSS**, including preprocessing and earlier cells. The run
directory occupied **63,086,469 bytes** at review. Equal optimizer updates are
not equal active compute; these measurements do not support a per-model
memory-efficiency or hardware-normalized speed claim.

The 209 development roots remain singleton closure components, with the prior
strict cross-split and old-training exclusions intact. They describe only two
fixed oracle-admitted endgame families at 5..8 empty cells. Three seeds and
repeated tuning on these roots do not establish independent confirmation,
whole-game strength, held-out-family transfer, novelty or publication readiness.

Keep grid01 and grid02 intact as negative development outcomes. A further cycle
needs a separately frozen decision-relevant hypothesis and equally informative
controls; selection/final prediction access remains unjustified by this screen.
