# V2 development grid report

**Status: not_promoted**

This is adaptive development evidence, not confirmation or a publication guarantee.

Input artifacts: `C:\Users\ANHKHOI\Documents\ChatGPT\caissa-jepa\chess_data\v2-grid-01`.


Candidate: rjepa at learning rate 0.001.

- Aggregate improvement against the strongest tuned control is below 0.05
- Nonpositive game improvement versus direct
- Nonpositive game improvement versus value-dynamics

| Tuned family | Global learning rate | Equal-game exact regret |
| --- | ---: | ---: |
| direct | 0.0003 | 0.272402 |
| value-dynamics | 0.0003 | 0.247664 |
| decoded | 0.0003 | 0.270234 |
| rjepa | 0.001 | 0.249145 |
| raw-jepa | 0.001 | 0.255757 |
| no-response | 0.001 | 0.254047 |

| Comparison | Improvement | Development bootstrap 95% interval | Favorable seeds |
| --- | ---: | --- | ---: |
| Candidate versus direct | 0.023258 | [-0.027360, 0.082801] | 3/3 |
| Candidate versus decoded | 0.021089 | [-0.028810, 0.074407] | 3/3 |
| Candidate versus value-dynamics | -0.001481 | [-0.049433, 0.048714] | 2/3 |

| Run | Status | Connect4 exact / hybrid regret | Reversi exact / hybrid regret |
| --- | --- | --- | --- |
| direct-lr0.001-s17 | complete | 0.168224 / 0.168224 | 0.362745 / 0.362745 |
| direct-lr0.001-s29 | complete | 0.205607 / 0.205607 | 0.352941 / 0.352941 |
| direct-lr0.001-s43 | complete | 0.158879 / 0.158879 | 0.421569 / 0.421569 |
| direct-lr0.0003-s17 | complete | 0.158879 / 0.158879 | 0.352941 / 0.352941 |
| direct-lr0.0003-s29 | complete | 0.149533 / 0.149533 | 0.372549 / 0.372549 |
| direct-lr0.0003-s43 | complete | 0.149533 / 0.149533 | 0.450980 / 0.450980 |
| value-dynamics-lr0.001-s17 | complete | 0.214953 / 0.130841 | 0.382353 / 0.470588 |
| value-dynamics-lr0.001-s29 | complete | 0.224299 / 0.102804 | 0.372549 / 0.431373 |
| value-dynamics-lr0.001-s43 | complete | 0.177570 / 0.168224 | 0.421569 / 0.411765 |
| value-dynamics-lr0.0003-s17 | complete | 0.168224 / 0.158879 | 0.333333 / 0.450980 |
| value-dynamics-lr0.0003-s29 | complete | 0.158879 / 0.149533 | 0.343137 / 0.519608 |
| value-dynamics-lr0.0003-s43 | complete | 0.158879 / 0.130841 | 0.323529 / 0.490196 |
| decoded-lr0.001-s17 | complete | 0.186916 / 0.112150 | 0.382353 / 0.490196 |
| decoded-lr0.001-s29 | complete | 0.252336 / 0.140187 | 0.333333 / 0.411765 |
| decoded-lr0.001-s43 | complete | 0.149533 / 0.121495 | 0.421569 / 0.480392 |
| decoded-lr0.0003-s17 | complete | 0.177570 / 0.158879 | 0.352941 / 0.500000 |
| decoded-lr0.0003-s29 | complete | 0.186916 / 0.158879 | 0.382353 / 0.480392 |
| decoded-lr0.0003-s43 | complete | 0.158879 / 0.158879 | 0.362745 / 0.539216 |
| rjepa-lr0.001-s17 | complete | 0.158879 / 0.149533 | 0.323529 / 0.411765 |
| rjepa-lr0.001-s29 | complete | 0.186916 / 0.158879 | 0.313725 / 0.519608 |
| rjepa-lr0.001-s43 | complete | 0.158879 / 0.140187 | 0.352941 / 0.421569 |
| rjepa-lr0.0003-s17 | complete | 0.112150 / 0.158879 | 0.431373 / 0.539216 |
| rjepa-lr0.0003-s29 | complete | 0.140187 / 0.140187 | 0.362745 / 0.470588 |
| rjepa-lr0.0003-s43 | complete | 0.158879 / 0.149533 | 0.392157 / 0.509804 |
| raw-jepa-lr0.001-s17 | complete | 0.158879 / 0.168224 | 0.313725 / 0.450980 |
| raw-jepa-lr0.001-s29 | complete | 0.186916 / 0.130841 | 0.362745 / 0.392157 |
| raw-jepa-lr0.001-s43 | complete | 0.149533 / 0.140187 | 0.362745 / 0.441176 |
| raw-jepa-lr0.0003-s17 | complete | 0.149533 / 0.140187 | 0.362745 / 0.480392 |
| raw-jepa-lr0.0003-s29 | complete | 0.140187 / 0.149533 | 0.362745 / 0.500000 |
| raw-jepa-lr0.0003-s43 | complete | 0.140187 / 0.149533 | 0.382353 / 0.480392 |
| no-response-lr0.001-s17 | complete | 0.140187 / 0.149533 | 0.362745 / 0.617647 |
| no-response-lr0.001-s29 | complete | 0.205607 / 0.158879 | 0.323529 / 0.637255 |
| no-response-lr0.001-s43 | complete | 0.158879 / 0.130841 | 0.333333 / 0.568627 |
| no-response-lr0.0003-s17 | complete | 0.121495 / 0.158879 | 0.382353 / 0.598039 |
| no-response-lr0.0003-s29 | complete | 0.149533 / 0.149533 | 0.352941 / 0.617647 |
| no-response-lr0.0003-s43 | complete | 0.158879 / 0.140187 | 0.411765 / 0.627451 |

| Fixed baseline | Connect4 exact regret | Reversi exact regret |
| --- | ---: | ---: |
| zero | 0.317757 | 0.696078 |
| untrained-17 | 0.308411 | 0.617647 |
| untrained-29 | 0.345794 | 0.764706 |
| untrained-43 | 0.233645 | 0.549020 |

## Interpretation limits

- Development tuning and selection are adaptive; no confirmatory inference.
- Intervals condition on two fixed games and three training seeds.
- Equal-update/data comparison is not equal active compute; process-lifetime peak RSS is not a per-model peak.
- No new model fitting, decision scoring, selection-set or final-set access occurs here.

JSON retains hashes, source identity, all per-game metrics and paired-seed effects. No failed cell or censored root is deleted.
