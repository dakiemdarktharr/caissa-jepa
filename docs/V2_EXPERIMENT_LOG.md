# V2 experiment ledger and interpretation

Read `METHOD_V2.md` for the frozen algorithm and `V2_RESEARCH_CONTROL.md` for
adaptive-development boundaries. This log records attempted designs, including
failures. It does not replace immutable artifact receipts.

## Attempts before fitting

| Attempt | Evidence and decision |
| --- | --- |
| V1 whole-game audit | Failed split support; no fitting permitted |
| V1.2 local-position pilot | 21 runs completed; no JEPA benefit, exact-search ceiling |
| V2 survey01 | Connect3 beyond-depth support failed; preserve bank |
| V2 survey02 | Reversi4 closure split leaves13 development roots; do not fit |
| V2 survey03 | Connect4/Reversi6 passes rule-only support; proceed to strict fork audit |
| V2 fork dataset01 | PASSED:509 train,209 development,131 selection,135 final roots; zero cross-split closure overlap |
| Fork-relative geometry proposal | Prior-art and algebra audit: all-pair squared residual difference equals centered residual MSE; no uniqueness claim |

## Grid01, started 2026-09-29

Source commit `325afc0502911314d585a659ce456bb150b6231e`; local output
`chess_data/v2-grid-01`. Dataset fingerprint
`3297fa10abd296299ccff6a80238a7db20b883369f0603a03b5f33983ccc57c2`.
The saved source identity covers every v2 module, dependent rules/data helpers,
reference source and frozen method. No edits to these files during training.

Six families x two learning rates x three training seeds =36 planned cells,
fixed40epochs. Each epoch samples261 roots per game,16 complete forks per
sampled root:8,352 fork draws,66 optimizer updates. Connect4 repeats13 roots
per epoch; all261 Reversi training roots appear once before fork sampling.
Every control receives identical encoded-state labels and seeded sample schedules.
Repeated examples are not independent new data.

The grid is the equal-example/update experiment. Different active operations
and training times mean it is not the matched-compute experiment. Initial direct
runs took roughly12–15s; these are provisional resource observations, not a speed
advantage claim. Process-lifetime RSS includes preprocessing and earlier cells.
Hardware: AMD Ryzen AI5 340,6cores/12logical processors,16,418,648,064bytes RAM;
single BLAS/OMP thread, serial training. No cloud/GPU or paid resources.

Engineering verification: full126-test regression passed72.353s plus6 report
tests passed9.614s. Independent reviewer found no remaining blocking gradient,
perspective, pairing or promotion-rule defect. Fixtures are not model results.

Completed36/36. Independent audit verified15,048 learned decisions plus836
fixed controls, every saved action against oracle labels and all hashes/schedules.
No failed/censored decisions or collapse alerts. Totaltraining513.287s;
process-lifetime peak RSS213,417,984bytes; run artifacts36,905,709bytes.

Outcome: **not promoted**. Tuned rjepa exact regret0.249145 versus stronger
value-dynamics0.247664; difference(control minus JEPA)-0.001481, descriptive
development95% bootstrap[-0.049433,0.048714]. Rjepa improves pooled direct/decoded
but loses Connect4 against direct/value-dynamics. Full results:
`V2_GRID01_RESULTS.md` and `validation/V2_GRID01_RESULTS.json`.

No selection/final predictions. A future development pass would trigger a separately
frozen replication/selection protocol; it would not establish Q1 readiness.

## Interpretation limits that remain regardless of the first grid outcome

- Two sampled endgame families and5..8 empty cells do not represent whole-game
  strength, all deterministic games or unseen-family transfer.
- Oracle-admitted roots favor actionable state differences; report that sampling
  distribution. Exact solver costs are separate from learned-model inference.
- Exact-state gains isolate an auxiliary representation contribution. Hybrid
  results are needed to support useful learned latent dynamics for planning.
- Fixed objective weights and one capacity are a bounded first comparison;
  baseline weight/capacity tuning and equal-time experiments remain necessary.
- Development intervals do not undo adaptive model selection. Three seeds give
  limited seed-population uncertainty. Holdout stages are still essential.
- Recent JEPA/SPR/value-equivalence work creates substantial novelty risk.
  A win would motivate further research, not justify a firstness claim.

## Grid02 prospective amendment

METHOD_V21 freezes60 cells with coherent legal-symmetry augmentation and
auxiliary weights0.1/1.0, while preserving the original v2 package and data.
Train-only gradient/sibling probes are in V2_GRID01_DIAGNOSIS. No consistent
gradient conflict justified model partitioning; capacity stays fixed. Sibling
residual reweighting remains a distinct later hypothesis, not mixed into grid02.

Prefit augmentation/runtime tests:13 passed1.791s.100 augmentation-only calls
on128 training fork feature rows took0.190875s; no optimizer steps or development
predictions were made. This timing is a feasibility check, not an efficiency
comparison. Report verification and source freeze precede any grid02 fitting.

Grid02 completed60/60 at086e839. All25,080 learned decisions and836 fixed
controls independently verified, including replay of120 seed/epoch augmentation
plans. No failures/censors/collapse. Raw JEPA0.207425 versus value-dynamics0.212250
gives0.004826 improvement, descriptive95% interval[-0.039003,0.044845]; below the
0.05 gate, with a failed Connect4 comparison against decoded. **Not promoted.**
Totaltraining916.427s; lifetime RSS215,351,296bytes; artifacts63,086,469bytes.
Full results: V21_GRID02_RESULTS and V21_INDEPENDENT_RESULTS_REVIEW.

## Grid03 prospective label-access study

METHOD_V22 changes the question explicitly to restricted label access. It freezes
72 cells, strong EMA-value consistency control, redacted artifacts, separate
development export, real canonical-label accounting and the unchanged promotion
margin. Data/model review and a scarce-label readiness audit must pass first.
No v2.2 results exist yet. Mean-residual reweighting is not implemented in it.
