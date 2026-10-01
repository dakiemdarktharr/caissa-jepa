# V2.8 model-blind root/oracle gate, development receipt 06

**Result: gate passed for two fixed development schedules under the stated common budget. This is not a dataset-split, power, training, strength, or JEPA comparison result.**

Both games used project-owned uniform-legal trajectories, predeclared seed schedules, 100% symmetry-unique root quotas, and a common exact solver cap of 200,000 nodes, 2 seconds, and 500,000 cache entries per root. The corrected runner checks requested quota, support floors, all exact action values, legal actions, state transitions, and terminal status after each move against a separate project-owned bitboard implementation. It is independent code, not an external referee.

| Game | Fixed unique roots | Exact root maps | Variable exact action labels | Beyond-depth roots | Rule transition comparisons | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Gravity Connect4 4×5 | 100 | 100/100 | 72 | 53 | 2,509 | Pass |
| Reversi6 | 150 | 150/150 | 54 | 54 | 2,651 | Pass |

“Beyond-depth” means all legal action scores tie under a terminal-aware depth-two minimax calculation with zero value at every nonterminal cutoff, while the exact root action values are not all tied. This is a support diagnostic for positions whose action ordering depends on information beyond that shallow cutoff; it is not a model prediction result.

The tracked aggregate is [`validation/V28_MODEL_BLIND_GATE_DEV06.json`](validation/V28_MODEL_BLIND_GATE_DEV06.json). Raw root states, exact action labels, and branch fingerprints remain ignored under `chess_data/v28_gate/` and are pinned by SHA-256 in that JSON. The root schedules are exposed development evidence and are excluded from training and locked-final evaluation.

The retained earlier runs show why the cap and support rules matter: DEV02 solved only 99/100 Connect4 roots at 100k nodes/0.5s, and a 100-root Reversi6 schedule had only 40 beyond-depth roots. DEV04 at 200k nodes/1s/200k cache solved 96/100 Connect4 roots and yielded 49 beyond-depth roots; DEV05 at 200k nodes/1s/500k cache solved 98/100. Those gates failed and no roots were removed. DEV06 used a uniformly increased two-second budget on the same predeclared per-game seed schedules and resolved all roots; no solver-success subset was formed.

The next research gate is still required before fitting: fresh self-play trajectories with complete provenance; opponent-family design; train/development/model-selection/locked-final grouping by trajectory and opponent; zero raw, role-normalized, symmetry-normalized, and counterfactual branch overlap; and a predeclared clustered power/sample-size analysis. The public prior-art and novelty review also remains open. Passing this gate authorizes only continued development and does not support a claim that JEPA outperforms a baseline.
