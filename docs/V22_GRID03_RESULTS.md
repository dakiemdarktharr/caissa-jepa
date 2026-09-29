# V2.2 restricted-label development grid report

**Status: not_promoted**

This is adaptive development evidence, not confirmation or a publication guarantee.

Input artifacts: `C:\Users\ANHKHOI\Documents\ChatGPT\caissa-jepa\chess_data\v22-grid-03`.


Candidate: raw-jepa at learning rate 0.001, auxiliary weight 0.1.

- Aggregate improvement against the strongest tuned control is below 0.05
- Nonpositive game improvement versus direct
- Nonpositive game improvement versus value-dynamics
- Nonpositive game improvement versus ema-value

| Tuned family | Global learning rate | Auxiliary weight | Equal-game exact regret |
| --- | ---: | ---: | ---: |
| direct | 0.0003 | 1 | 0.283917 |
| value-dynamics | 0.0003 | 1 | 0.308045 |
| decoded | 0.0003 | 0.1 | 0.298164 |
| raw-jepa | 0.001 | 0.1 | 0.293339 |
| ema-value | 0.0003 | 1 | 0.298394 |
| raw-no-response | 0.001 | 0.1 | 0.283764 |

Primary scarce arm (25% selected roots; actual state-label counts are in JSON).

| Comparison | Improvement | Development bootstrap 95% interval | Favorable seeds |
| --- | ---: | --- | ---: |
| Candidate versus direct | -0.009422 | [-0.075730, 0.047922] | 2/3 |
| Candidate versus value-dynamics | 0.014706 | [-0.051831, 0.081014] | 2/3 |
| Candidate versus decoded | 0.004826 | [-0.055340, 0.063496] | 2/3 |
| Candidate versus ema-value | 0.005055 | [-0.059770, 0.069122] | 2/3 |

Full-label sensitivity uses exactly the scarce-selected rate for each family.

| Family | Reused rate | Full-label exact regret | Collapse findings |
| --- | ---: | ---: | ---: |
| direct | 0.0003 | 0.224788 | 0 |
| value-dynamics | 0.0003 | 0.249145 | 0 |
| decoded | 0.0003 | 0.255757 | 0 |
| raw-jepa | 0.001 | 0.205867 | 0 |
| ema-value | 0.0003 | 0.249145 | 0 |
| raw-no-response | 0.001 | 0.210693 | 0 |

| Run | Status | Connect4 exact / hybrid regret | Reversi exact / hybrid regret |
| --- | --- | --- | --- |
| f0.25-direct-lr0.001-w1-s17 | complete | 0.158879 / 0.158879 | 0.421569 / 0.421569 |
| f0.25-direct-lr0.001-w1-s29 | complete | 0.224299 / 0.224299 | 0.352941 / 0.352941 |
| f0.25-direct-lr0.001-w1-s43 | complete | 0.205607 / 0.205607 | 0.470588 / 0.470588 |
| f0.25-direct-lr0.0003-w1-s17 | complete | 0.130841 / 0.130841 | 0.401961 / 0.401961 |
| f0.25-direct-lr0.0003-w1-s29 | complete | 0.158879 / 0.158879 | 0.441176 / 0.441176 |
| f0.25-direct-lr0.0003-w1-s43 | complete | 0.158879 / 0.158879 | 0.411765 / 0.411765 |
| f0.25-value-dynamics-lr0.001-w1-s17 | complete | 0.186916 / 0.177570 | 0.401961 / 0.500000 |
| f0.25-value-dynamics-lr0.001-w1-s29 | complete | 0.186916 / 0.186916 | 0.460784 / 0.500000 |
| f0.25-value-dynamics-lr0.001-w1-s43 | complete | 0.214953 / 0.224299 | 0.470588 / 0.490196 |
| f0.25-value-dynamics-lr0.0003-w1-s17 | complete | 0.158879 / 0.177570 | 0.460784 / 0.519608 |
| f0.25-value-dynamics-lr0.0003-w1-s29 | complete | 0.168224 / 0.168224 | 0.450980 / 0.500000 |
| f0.25-value-dynamics-lr0.0003-w1-s43 | complete | 0.168224 / 0.158879 | 0.441176 / 0.549020 |
| f0.25-decoded-lr0.001-w0.1-s17 | complete | 0.168224 / 0.242991 | 0.392157 / 0.460784 |
| f0.25-decoded-lr0.001-w0.1-s29 | complete | 0.168224 / 0.233645 | 0.460784 / 0.480392 |
| f0.25-decoded-lr0.001-w0.1-s43 | complete | 0.205607 / 0.205607 | 0.450980 / 0.519608 |
| f0.25-decoded-lr0.0003-w0.1-s17 | complete | 0.158879 / 0.158879 | 0.421569 / 0.470588 |
| f0.25-decoded-lr0.0003-w0.1-s29 | complete | 0.168224 / 0.158879 | 0.421569 / 0.500000 |
| f0.25-decoded-lr0.0003-w0.1-s43 | complete | 0.177570 / 0.140187 | 0.441176 / 0.529412 |
| f0.25-raw-jepa-lr0.001-w0.1-s17 | complete | 0.149533 / 0.177570 | 0.382353 / 0.529412 |
| f0.25-raw-jepa-lr0.001-w0.1-s29 | complete | 0.186916 / 0.224299 | 0.372549 / 0.480392 |
| f0.25-raw-jepa-lr0.001-w0.1-s43 | complete | 0.158879 / 0.252336 | 0.509804 / 0.509804 |
| f0.25-raw-jepa-lr0.0003-w0.1-s17 | complete | 0.149533 / 0.168224 | 0.411765 / 0.529412 |
| f0.25-raw-jepa-lr0.0003-w0.1-s29 | complete | 0.177570 / 0.149533 | 0.441176 / 0.490196 |
| f0.25-raw-jepa-lr0.0003-w0.1-s43 | complete | 0.168224 / 0.177570 | 0.431373 / 0.529412 |
| f0.25-ema-value-lr0.001-w1-s17 | complete | 0.186916 / 0.224299 | 0.441176 / 0.509804 |
| f0.25-ema-value-lr0.001-w1-s29 | complete | 0.196262 / 0.196262 | 0.450980 / 0.460784 |
| f0.25-ema-value-lr0.001-w1-s43 | complete | 0.177570 / 0.186916 | 0.441176 / 0.500000 |
| f0.25-ema-value-lr0.0003-w1-s17 | complete | 0.140187 / 0.177570 | 0.450980 / 0.558824 |
| f0.25-ema-value-lr0.0003-w1-s29 | complete | 0.168224 / 0.205607 | 0.431373 / 0.549020 |
| f0.25-ema-value-lr0.0003-w1-s43 | complete | 0.168224 / 0.214953 | 0.431373 / 0.598039 |
| f0.25-raw-no-response-lr0.001-w0.1-s17 | complete | 0.140187 / 0.186916 | 0.352941 / 0.617647 |
| f0.25-raw-no-response-lr0.001-w0.1-s29 | complete | 0.177570 / 0.186916 | 0.392157 / 0.607843 |
| f0.25-raw-no-response-lr0.001-w0.1-s43 | complete | 0.149533 / 0.186916 | 0.490196 / 0.558824 |
| f0.25-raw-no-response-lr0.0003-w0.1-s17 | complete | 0.149533 / 0.168224 | 0.411765 / 0.558824 |
| f0.25-raw-no-response-lr0.0003-w0.1-s29 | complete | 0.177570 / 0.149533 | 0.460784 / 0.637255 |
| f0.25-raw-no-response-lr0.0003-w0.1-s43 | complete | 0.168224 / 0.140187 | 0.460784 / 0.578431 |
| f1-direct-lr0.001-w1-s17 | complete | 0.130841 / 0.130841 | 0.303922 / 0.303922 |
| f1-direct-lr0.001-w1-s29 | complete | 0.074766 / 0.074766 | 0.284314 / 0.284314 |
| f1-direct-lr0.001-w1-s43 | complete | 0.130841 / 0.130841 | 0.254902 / 0.254902 |
| f1-direct-lr0.0003-w1-s17 | complete | 0.140187 / 0.140187 | 0.303922 / 0.303922 |
| f1-direct-lr0.0003-w1-s29 | complete | 0.158879 / 0.158879 | 0.245098 / 0.245098 |
| f1-direct-lr0.0003-w1-s43 | complete | 0.186916 / 0.186916 | 0.313725 / 0.313725 |
| f1-value-dynamics-lr0.001-w1-s17 | complete | 0.158879 / 0.130841 | 0.284314 / 0.460784 |
| f1-value-dynamics-lr0.001-w1-s29 | complete | 0.093458 / 0.112150 | 0.343137 / 0.480392 |
| f1-value-dynamics-lr0.001-w1-s43 | complete | 0.121495 / 0.130841 | 0.264706 / 0.470588 |
| f1-value-dynamics-lr0.0003-w1-s17 | complete | 0.130841 / 0.140187 | 0.323529 / 0.441176 |
| f1-value-dynamics-lr0.0003-w1-s29 | complete | 0.177570 / 0.149533 | 0.382353 / 0.431373 |
| f1-value-dynamics-lr0.0003-w1-s43 | complete | 0.196262 / 0.149533 | 0.284314 / 0.480392 |
| f1-decoded-lr0.001-w0.1-s17 | complete | 0.149533 / 0.140187 | 0.313725 / 0.421569 |
| f1-decoded-lr0.001-w0.1-s29 | complete | 0.102804 / 0.140187 | 0.323529 / 0.480392 |
| f1-decoded-lr0.001-w0.1-s43 | complete | 0.112150 / 0.121495 | 0.264706 / 0.509804 |
| f1-decoded-lr0.0003-w0.1-s17 | complete | 0.140187 / 0.149533 | 0.343137 / 0.470588 |
| f1-decoded-lr0.0003-w0.1-s29 | complete | 0.168224 / 0.158879 | 0.401961 / 0.450980 |
| f1-decoded-lr0.0003-w0.1-s43 | complete | 0.186916 / 0.149533 | 0.294118 / 0.500000 |
| f1-raw-jepa-lr0.001-w0.1-s17 | complete | 0.168224 / 0.149533 | 0.323529 / 0.470588 |
| f1-raw-jepa-lr0.001-w0.1-s29 | complete | 0.112150 / 0.084112 | 0.294118 / 0.431373 |
| f1-raw-jepa-lr0.001-w0.1-s43 | complete | 0.121495 / 0.149533 | 0.215686 / 0.470588 |
| f1-raw-jepa-lr0.0003-w0.1-s17 | complete | 0.140187 / 0.149533 | 0.343137 / 0.460784 |
| f1-raw-jepa-lr0.0003-w0.1-s29 | complete | 0.177570 / 0.140187 | 0.352941 / 0.411765 |
| f1-raw-jepa-lr0.0003-w0.1-s43 | complete | 0.186916 / 0.130841 | 0.294118 / 0.480392 |
| f1-ema-value-lr0.001-w1-s17 | complete | 0.158879 / 0.130841 | 0.284314 / 0.460784 |
| f1-ema-value-lr0.001-w1-s29 | complete | 0.093458 / 0.112150 | 0.343137 / 0.480392 |
| f1-ema-value-lr0.001-w1-s43 | complete | 0.121495 / 0.130841 | 0.264706 / 0.470588 |
| f1-ema-value-lr0.0003-w1-s17 | complete | 0.130841 / 0.140187 | 0.323529 / 0.441176 |
| f1-ema-value-lr0.0003-w1-s29 | complete | 0.177570 / 0.149533 | 0.382353 / 0.431373 |
| f1-ema-value-lr0.0003-w1-s43 | complete | 0.196262 / 0.149533 | 0.284314 / 0.480392 |
| f1-raw-no-response-lr0.001-w0.1-s17 | complete | 0.168224 / 0.112150 | 0.313725 / 0.578431 |
| f1-raw-no-response-lr0.001-w0.1-s29 | complete | 0.093458 / 0.112150 | 0.313725 / 0.480392 |
| f1-raw-no-response-lr0.001-w0.1-s43 | complete | 0.149533 / 0.149533 | 0.225490 / 0.578431 |
| f1-raw-no-response-lr0.0003-w0.1-s17 | complete | 0.149533 / 0.130841 | 0.352941 / 0.617647 |
| f1-raw-no-response-lr0.0003-w0.1-s29 | complete | 0.177570 / 0.158879 | 0.343137 / 0.460784 |
| f1-raw-no-response-lr0.0003-w0.1-s43 | complete | 0.186916 / 0.112150 | 0.294118 / 0.539216 |

| Fixed baseline | Connect4 exact regret | Reversi exact regret |
| --- | ---: | ---: |
| zero | 0.317757 | 0.696078 |
| untrained-17 | 0.308411 | 0.617647 |
| untrained-29 | 0.345794 | 0.764706 |
| untrained-43 | 0.233645 | 0.549020 |

## Interpretation limits

- Grid03 reuses exposed development roots; tuning is adaptive and not confirmatory.
- Intervals condition on one fixed label mask; optimizer seeds do not measure label-selection uncertainty.
- Scarce-arm selected rates are reused unchanged for the full-label sensitivity arm.
- This simulates label access on an already solved bank; no oracle-compute saving is demonstrated.
- Primary comparisons use augmented tuned controls; shared augmentation gains are not JEPA-specific.
- No uniqueness or publication-readiness claim follows from passing this development screen.
- Intervals condition on two fixed games and three training seeds.
- Equal-update/data comparison is not equal active compute; process-lifetime peak RSS is not a per-model peak.
- No new model fitting, decision scoring, selection-set or final-set access occurs here.

JSON retains hashes, source identity, all per-game metrics and paired-seed effects. No failed cell or censored root is deleted.


## Verified execution and label-access scope

The strict aggregate verifier returned zero errors over all 72 frozen cells.
There were 30,096 learned decisions (72 x 209 roots x two tracks) and 836 fixed
zero/untrained control decisions, with zero failures, censored decisions or
collapse alerts. No selection/final predictions were made. Absence of collapse
is a diagnostic result, not evidence of useful representations.

The scarce mask exposes 62/248 Connect4 training roots and 66/261 Reversi roots.
After canonical closure, 848/3,468 and 1,386/5,444 unique nonterminal states have
value/policy labels; 2,620 and 4,058 remain unlabeled (75.55% and 74.54%). There
are respectively 321 and one unique free terminal states. Counts by horizon,
label type and occurrence remain in the exact aggregate JSON below. This is
simulated restricted access on an already solved bank, not measured savings
in oracle computation.

Primary raw JEPA is worse than the tuned direct control in both games:
Connect4 regret 0.165109 versus 0.149533, Reversi 0.421569 versus 0.418301.
It ties value-dynamics on Connect4 and loses there to EMA-value. All four
primary bootstrap intervals include zero. The original 0.05/per-game gates
failed; the primary label-efficiency hypothesis is not supported by this study.

Full-label raw JEPA has lower descriptive regret at the scarce-selected rates.
These controls are NOT independently tuned on the full-label arm, so that
sensitivity cannot establish superiority over fully tuned full-label baselines,
replace the failed primary arm or rescue promotion. Its fixed-mask intervals
remain descriptive after adaptive development. Online, EMA and Adam tensors
of full-label EMA-value and value-dynamics match in all six rate/seed pairs.

Total recorded training time: 1,102.6110401 seconds; per-cell range 11.9296 to
23.8614 seconds. Process-lifetime peak RSS: 251,486,208 bytes, including
preprocessing and earlier cells; it is not per-model peak memory. Run artifacts:
78,628,950 bytes. Training time excludes evaluation and earlier data generation.
Equal updates/data are not equal active compute. Local artifacts stay excluded
from Git/Obsidian; only documentation and aggregate receipts are published.

Training source commit: `9e3d10bb3d01f4761db552ec6b2d7241957cf2e0`.
Ledger SHA-256: `660fe61f7612ed3ca69ff7b9dcb5bb91a3c4cf4c656c05c6332df412f29c1f26`.
The [exact aggregate JSON](validation/V22_GRID03_RESULTS.json) is a byte-for-byte
copy of the verified report and retains all 72 rows, primary/full comparisons,
label manifests, hashes, geometry and per-game metrics. See the
[frozen method](METHOD_V22.md) and [pre-fitting review](V22_PREFIT_REVIEW.md).
Independent post-result review verified decision counts, tensor equivalence
and paired schedules. A descriptive check of the complete full-label table
gives direct at learning rate 0.001 regret 0.196598, lower than the candidate's
0.205867. This is not a new primary selection; it illustrates why scarce-rate
sensitivity cannot be described as full-label superiority.

![V2.2 primary restricted-label development results](figures/v22-grid03.png)
