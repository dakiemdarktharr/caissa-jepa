# V2.4 fixed-target order probe: obstruction not established

2026-09-29. Training-only diagnostic at source
`0a7edef6bf5a651c37ca4c23186dbbf472ea2b26`; all18 final V2.3 checkpoints,
both online and actual EMA target spaces,72 contextual rows. The single fresh
attempt `chess_data/v24-order-01` completed with no errors, optimizer updates,
new development/selection/final predictions or planner decisions. Independent
postrun audit is recorded separately. This is not a JEPA strength result.

The prespecified material-obstruction screen failed in all four game/capacity
groups. Coverage was sufficient; the conservative lower bound was very small
relative to observed H1 latent error. Therefore this experiment does not support
the proposed additive-order restriction as a material explanation of the current
errors. It also does not prove the additive architecture adequate: the bound and
greedy disjoint packing are conservative and coordinate dependent.

| Game | Capacity | Primary coverage | Median bound / all H1 SSE | Nonterminal coverage | Median NT bound / all NT SSE |
| --- | --- | ---: | ---: | ---: | ---: |
| Connect4 4x5 |64/32|71.689%|0.000326|55.224%|0.000243|
| Connect4 4x5 |128/64|71.689%|0.000174|55.224%|0.000119|
| Reversi6 |64/32|68.136%|0.001933|68.136%|0.001933|
| Reversi6 |128/64|68.136%|0.002787|68.136%|0.002787|

These ratios are fractions, not percentages:0.002787 is approximately0.279%.
The frozen heuristic requires a median at least0.10 and at least two of three
seed ratios at least0.10, with coverage at least25%. None passes. The same is
true of the separately declared all-four-nonterminal sensitivity. Seed values,
all contextual controls, target-value diagnostics, gap quantiles and both
normalizations are retained in the compact machine-readable receipt.

Packing was saved before model loading and used only game/rule identities:
Connect4 has248 roots,876 unique H1 edges,2825 eligible root pairs,4001 candidate
blocks and157 retained disjoint blocks; terminal-count histogram is
111/39/7/0/0 for0/1/2/3/4 terminal targets. Reversi has261 roots,1180 H1 edges,
2988 eligible pairs,4480 candidates and201 retained blocks, all nonterminal.
No state/edge was repacked after inspecting embeddings or outcomes.

Runtime12.875268s, process-lifetime peak RSS103,759,872bytes and1,875,856bytes
output excluding journal; all within600s/1GB/200MB acceptance limits. Before and
after tensor hashes matched for every model. The runtime rechecked saved schedule
and all18 measurement-file hashes at completion. Report SHA-256:
`19523d039427fb4521e69dfe9c65103d24caa29e633515e28ff424820cc4ada4`.
Schedule-file SHA-256:
`c47a5f8ee2a8d95ab435ae0a3575c009a038de5bfc0a1d1022e98249abf5d658`.

Any later nonlinear transition experiment must be motivated and controlled
separately; it cannot cite this diagnostic as a demonstrated bottleneck. All
controls retain the common128/64×160 future operating budget. Superiority,
cross-game transfer, opponent behavior calibration and Q1 readiness remain
unestablished. Original data/checkpoints/schedule remain local and excluded;
only source, aggregate receipts and documentation are published.
