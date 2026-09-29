# V2.1 development grid report

**Status: not_promoted**

This is adaptive development evidence, not confirmation or a publication guarantee.

Input artifacts: `C:\Users\ANHKHOI\Documents\ChatGPT\caissa-jepa\chess_data\v21-grid-02`.


Candidate: raw-jepa at learning rate 0.001, auxiliary weight 0.1.

- Aggregate improvement against the strongest tuned control is below 0.05
- Nonpositive game improvement versus decoded

| Tuned family | Global learning rate | Auxiliary weight | Equal-game exact regret |
| --- | ---: | ---: | ---: |
| direct | 0.001 | 1 | 0.220191 |
| value-dynamics | 0.001 | 1 | 0.212250 |
| decoded | 0.001 | 0.1 | 0.215900 |
| rjepa | 0.001 | 0.1 | 0.213350 |
| raw-jepa | 0.001 | 0.1 | 0.207425 |
| no-response | 0.001 | 1 | 0.201912 |

| Comparison | Improvement | Development bootstrap 95% interval | Favorable seeds |
| --- | ---: | --- | ---: |
| Candidate versus direct | 0.012766 | [-0.028656, 0.054107] | 2/3 |
| Candidate versus decoded | 0.008475 | [-0.025689, 0.046441] | 3/3 |
| Candidate versus value-dynamics | 0.004826 | [-0.039003, 0.044845] | 2/3 |

| Run | Status | Connect4 exact / hybrid regret | Reversi exact / hybrid regret |
| --- | --- | --- | --- |
| direct-lr0.001-w1-s17 | complete | 0.158879 / 0.158879 | 0.313725 / 0.313725 |
| direct-lr0.001-w1-s29 | complete | 0.168224 / 0.168224 | 0.274510 / 0.274510 |
| direct-lr0.001-w1-s43 | complete | 0.121495 / 0.121495 | 0.284314 / 0.284314 |
| direct-lr0.0003-w1-s17 | complete | 0.149533 / 0.149533 | 0.294118 / 0.294118 |
| direct-lr0.0003-w1-s29 | complete | 0.168224 / 0.168224 | 0.294118 / 0.294118 |
| direct-lr0.0003-w1-s43 | complete | 0.177570 / 0.177570 | 0.274510 / 0.274510 |
| value-dynamics-lr0.001-w1-s17 | complete | 0.149533 / 0.121495 | 0.313725 / 0.441176 |
| value-dynamics-lr0.001-w1-s29 | complete | 0.130841 / 0.102804 | 0.284314 / 0.450980 |
| value-dynamics-lr0.001-w1-s43 | complete | 0.140187 / 0.112150 | 0.254902 / 0.519608 |
| value-dynamics-lr0.0003-w1-s17 | complete | 0.140187 / 0.149533 | 0.284314 / 0.480392 |
| value-dynamics-lr0.0003-w1-s29 | complete | 0.168224 / 0.149533 | 0.411765 / 0.421569 |
| value-dynamics-lr0.0003-w1-s43 | complete | 0.177570 / 0.158879 | 0.294118 / 0.480392 |
| decoded-lr0.001-w0.1-s17 | complete | 0.140187 / 0.149533 | 0.362745 / 0.421569 |
| decoded-lr0.001-w0.1-s29 | complete | 0.112150 / 0.084112 | 0.294118 / 0.460784 |
| decoded-lr0.001-w0.1-s43 | complete | 0.121495 / 0.102804 | 0.264706 / 0.539216 |
| decoded-lr0.001-w1-s17 | complete | 0.177570 / 0.140187 | 0.313725 / 0.470588 |
| decoded-lr0.001-w1-s29 | complete | 0.130841 / 0.093458 | 0.235294 / 0.431373 |
| decoded-lr0.001-w1-s43 | complete | 0.158879 / 0.140187 | 0.303922 / 0.549020 |
| decoded-lr0.0003-w0.1-s17 | complete | 0.140187 / 0.149533 | 0.294118 / 0.500000 |
| decoded-lr0.0003-w0.1-s29 | complete | 0.186916 / 0.140187 | 0.343137 / 0.450980 |
| decoded-lr0.0003-w0.1-s43 | complete | 0.158879 / 0.140187 | 0.274510 / 0.519608 |
| decoded-lr0.0003-w1-s17 | complete | 0.140187 / 0.149533 | 0.274510 / 0.480392 |
| decoded-lr0.0003-w1-s29 | complete | 0.149533 / 0.149533 | 0.303922 / 0.450980 |
| decoded-lr0.0003-w1-s43 | complete | 0.149533 / 0.149533 | 0.303922 / 0.480392 |
| rjepa-lr0.001-w0.1-s17 | complete | 0.158879 / 0.140187 | 0.225490 / 0.450980 |
| rjepa-lr0.001-w0.1-s29 | complete | 0.177570 / 0.112150 | 0.284314 / 0.401961 |
| rjepa-lr0.001-w0.1-s43 | complete | 0.149533 / 0.093458 | 0.284314 / 0.460784 |
| rjepa-lr0.001-w1-s17 | complete | 0.140187 / 0.102804 | 0.254902 / 0.470588 |
| rjepa-lr0.001-w1-s29 | complete | 0.224299 / 0.112150 | 0.274510 / 0.450980 |
| rjepa-lr0.001-w1-s43 | complete | 0.168224 / 0.149533 | 0.284314 / 0.460784 |
| rjepa-lr0.0003-w0.1-s17 | complete | 0.140187 / 0.140187 | 0.294118 / 0.500000 |
| rjepa-lr0.0003-w0.1-s29 | complete | 0.177570 / 0.140187 | 0.303922 / 0.431373 |
| rjepa-lr0.0003-w0.1-s43 | complete | 0.149533 / 0.130841 | 0.254902 / 0.578431 |
| rjepa-lr0.0003-w1-s17 | complete | 0.140187 / 0.140187 | 0.323529 / 0.490196 |
| rjepa-lr0.0003-w1-s29 | complete | 0.177570 / 0.158879 | 0.303922 / 0.421569 |
| rjepa-lr0.0003-w1-s43 | complete | 0.158879 / 0.158879 | 0.254902 / 0.500000 |
| raw-jepa-lr0.001-w0.1-s17 | complete | 0.168224 / 0.130841 | 0.333333 / 0.490196 |
| raw-jepa-lr0.001-w0.1-s29 | complete | 0.130841 / 0.102804 | 0.254902 / 0.470588 |
| raw-jepa-lr0.001-w0.1-s43 | complete | 0.112150 / 0.130841 | 0.245098 / 0.529412 |
| raw-jepa-lr0.001-w1-s17 | complete | 0.168224 / 0.121495 | 0.274510 / 0.450980 |
| raw-jepa-lr0.001-w1-s29 | complete | 0.130841 / 0.130841 | 0.254902 / 0.372549 |
| raw-jepa-lr0.001-w1-s43 | complete | 0.130841 / 0.093458 | 0.303922 / 0.411765 |
| raw-jepa-lr0.0003-w0.1-s17 | complete | 0.140187 / 0.149533 | 0.313725 / 0.490196 |
| raw-jepa-lr0.0003-w0.1-s29 | complete | 0.168224 / 0.130841 | 0.313725 / 0.431373 |
| raw-jepa-lr0.0003-w0.1-s43 | complete | 0.186916 / 0.158879 | 0.294118 / 0.500000 |
| raw-jepa-lr0.0003-w1-s17 | complete | 0.140187 / 0.149533 | 0.284314 / 0.460784 |
| raw-jepa-lr0.0003-w1-s29 | complete | 0.177570 / 0.130841 | 0.352941 / 0.401961 |
| raw-jepa-lr0.0003-w1-s43 | complete | 0.168224 / 0.140187 | 0.313725 / 0.480392 |
| no-response-lr0.001-w0.1-s17 | complete | 0.140187 / 0.102804 | 0.205882 / 0.519608 |
| no-response-lr0.001-w0.1-s29 | complete | 0.186916 / 0.102804 | 0.235294 / 0.549020 |
| no-response-lr0.001-w0.1-s43 | complete | 0.140187 / 0.093458 | 0.343137 / 0.568627 |
| no-response-lr0.001-w1-s17 | complete | 0.130841 / 0.130841 | 0.225490 / 0.588235 |
| no-response-lr0.001-w1-s29 | complete | 0.224299 / 0.093458 | 0.254902 / 0.529412 |
| no-response-lr0.001-w1-s43 | complete | 0.130841 / 0.149533 | 0.245098 / 0.529412 |
| no-response-lr0.0003-w0.1-s17 | complete | 0.130841 / 0.130841 | 0.303922 / 0.549020 |
| no-response-lr0.0003-w0.1-s29 | complete | 0.177570 / 0.130841 | 0.294118 / 0.539216 |
| no-response-lr0.0003-w0.1-s43 | complete | 0.140187 / 0.112150 | 0.254902 / 0.588235 |
| no-response-lr0.0003-w1-s17 | complete | 0.140187 / 0.140187 | 0.333333 / 0.519608 |
| no-response-lr0.0003-w1-s29 | complete | 0.177570 / 0.140187 | 0.303922 / 0.539216 |
| no-response-lr0.0003-w1-s43 | complete | 0.158879 / 0.158879 | 0.254902 / 0.598039 |

| Fixed baseline | Connect4 exact regret | Reversi exact regret |
| --- | ---: | ---: |
| zero | 0.317757 | 0.696078 |
| untrained-17 | 0.308411 | 0.617647 |
| untrained-29 | 0.345794 | 0.764706 |
| untrained-43 | 0.233645 | 0.549020 |

## Interpretation limits

- Grid02 reuses exposed Grid01 development roots; tuning is adaptive and not confirmatory.
- Primary comparisons use augmented tuned controls; shared augmentation gains are not JEPA-specific.
- No uniqueness or publication-readiness claim follows from passing this development screen.
- Intervals condition on two fixed games and three training seeds.
- Equal-update/data comparison is not equal active compute; process-lifetime peak RSS is not a per-model peak.
- No new model fitting, decision scoring, selection-set or final-set access occurs here.

JSON retains hashes, source identity, all per-game metrics and paired-seed effects. No failed cell or censored root is deleted.
