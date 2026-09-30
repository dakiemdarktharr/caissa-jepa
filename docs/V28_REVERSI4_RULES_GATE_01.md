# V2.8 Reversi4 exhaustive rules subgate

Date: 2026-09-30. Stage: model-blind rules/runtime feasibility only.

The project-owned 4x4 Reversi adapter was exhaustively enumerated from its initial state and compared against a separate coordinate-ray reference implementation. The post-commit source was `5abbd777261c34228888ecbddd9924686b159b63`. The machine-readable receipt is [V28_REVERSI4_RULES_GATE_01.json](validation/V28_REVERSI4_RULES_GATE_01.json); raw output is excluded from Git at `chess_data/two-player-klent-toy/v28_reversi4_rules_dev02.json`.

The audit covered 62,789 reachable `(board, player)` states, including 6,168 terminal and 56,621 nonterminal states. It checked all 89,332 legal transitions, 8,988 forced-pass states, and 113,900 complete two-ply reply pairs. Maximum legal branching was six. Enumeration was complete. All terminal outcomes, legal-action/pass behavior, transitions, feature shape and finiteness checks passed. The run used local CPU only (Python 3.11.9), taking 8.75 CPU seconds and 8.77728 wall seconds with 92,688,384 bytes peak working set. The receipt pins source and configuration hashes.

This closes only the exhaustive rules, legal-transition, and two-ply coverage subgate for this tiny feasibility variant. It does not establish dataset quality or leakage-free splits, opponent strength, statistical power, compute parity, JEPA training, model superiority, or cross-game transfer. No trajectory dataset was generated and no training started. Reversi4 results cannot support claims about the full target class. The repository regression suite passed 348 tests in 127.285 seconds before this receipt was assembled; the source did not change afterward.

Next, freeze and audit the situation-generation and split protocol without inspecting model outcomes, then assess opponent-bank power and matched compute. Production data generation/training remains gated on those checks.
