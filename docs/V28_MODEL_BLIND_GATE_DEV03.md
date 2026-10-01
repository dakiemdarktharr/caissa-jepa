# V2.8 model-blind feasibility gate, development receipt 03

**Status: historical exploratory receipt, superseded by DEV06. This receipt is not the gate record to cite.**

Both candidate games used project-owned uniform-legal self-play and the same exact solver cap for every root: 200,000 nodes, 1.0 second, and 500,000 transposition entries. The earlier tracked summary mistakenly stated a 200,000-entry cache, and the original gate did not require requested root quota/support floors in its `gate_pass` condition. Counts in the raw receipt are accurate, but cite corrected [DEV06](V28_MODEL_BLIND_GATE_DEV06.md) for the reviewed gate. Each root's legal actions and two-ply transitions were compared against a separate project-owned bitboard rules implementation; it is not a third-party referee.

| Game | Fixed unique roots | Rule transition comparisons | Exact root maps | Variable exact action labels | Beyond-depth roots |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gravity Connect4 4×5 | 100 | 2,509 | 100/100 | 72 | 53 |
| Reversi6 | 150 | 2,651 | 150/150 | 54 | 54 |

Both schedules clear the current support floors of 100 symmetry-unique roots and 50 beyond-depth roots, with complete exact root-action labels on every scheduled root. The no-gravity Connect4 variant remains deferred: its earlier 24-root probe solved only 12/23 roots at 100,000 nodes/1 second. An intermediate 100-root Reversi6 schedule at 5–8 empty cells had only 40 beyond-depth roots; it was not promoted. The larger Reversi6 schedule and increased Connect4 oracle cap were declared before those V0.3 receipts were generated.

The tracked summary receipt is [`validation/V28_MODEL_BLIND_GATE_DEV03.json`](validation/V28_MODEL_BLIND_GATE_DEV03.json). Raw local receipts are `chess_data/v28_gate/connect4_gravity4x5_dev03.json` (SHA-256 `aa81c201781b46401da47a3ec50af5eca07bba7776e365ad336d353cdf5d0070`) and `chess_data/v28_gate/reversi6_dev03.json` (SHA-256 `1a385be5924bef78e1e297fd694e24ab6f27f6339c2a002861d0577186c90b3a`). They are ignored by Git and must not be uploaded. Their source commit is `d9dc357335d6065850a762cf4eabb4aa47152b86`; script, game adapter, planner, reference rules, and solver hashes are in the JSON summary.

The 200,000-cache DEV04 C4 rerun solved 96/100 and had 49 beyond-depth roots; it failed. At 500,000 cache, DEV05 solved 98/100 C4 roots under the same one-second wall cap; it also failed. Reversi6 had 150/150 exact maps and 54 beyond-depth roots in those schedules. DEV06 uses a uniform two-second cap and is the current feasibility result. All attempts remain in the local ignored folder and their hashes/counts are listed in the current aggregate receipt. None of these gates tests trajectory-level split leakage, opponent-family holdouts/calibration, statistical power, model training, fixed-budget regret, match strength, or transfer. Exposed roots stay out of locked-final confirmation and training. Training remains blocked pending fresh provenance-bearing data, group-first split and overlap checks, opponent audits, power, and independent review.
