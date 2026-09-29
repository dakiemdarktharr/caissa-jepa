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

Prefit gate:186 regression tests passed120.105s. Separate redacted artifacts
retain509roots/6750forks, standalone development209roots/2735forks. Scarce masks
leave2620/3468 Connect4 and4058/5444 Reversi canonical nonterminal states unknown,
passing the50% floor. Root selection62/248 and66/261 is not a state-label rate.
Full byte/source/mask identities are in validation/V22_LABEL_ACCESS_AUDIT.json.
Independent model/runtime/data reviews passed. No production fitting yet.

Grid03 subsequently completed all 72 cells at source
`9e3d10bb3d01f4761db552ec6b2d7241957cf2e0`, with 30,096 learned decisions and
836 fixed controls, no errors/censors/collapse and no selection/final scoring.
Scarce raw JEPA 0.293339 loses to direct 0.283917: improvement -0.009422,
descriptive 95% interval [-0.075730, 0.047922]. **Not promoted.** Full-label
sensitivity retains scarce-selected rates and is not a replacement primary
comparison or evidence against fully tuned controls. Total training 1102.611s,
range 11.930–23.861s, process-lifetime RSS 251,486,208 bytes, artifacts 78,628,950
bytes. All six full-label EMA-value/value-dynamics tensor pairs are identical.
Results and independent review are in V22_GRID03_RESULTS and
V22_INDEPENDENT_RESULTS_REVIEW. Preserve frozen code and all failed hypotheses.

After Grid03 ended, a read-only diagnostic examined all 18 globally selected
Grid02 checkpoints in 15.876s using only standalone full training/development
exports. It performs no new optimization or search. H1 duplicates are removed
per root/action; H2 includes complete legal forks; equal-root and transition
weighting are explicitly separated. Full local output:
`chess_data/v21-value-alignment-01.json`; small aggregate receipt:
`validation/V21_VALUE_ALIGNMENT_DIAGNOSIS.json`. Interpretation follows a separate
review of target distributions and existing learning histories before any new fit.

That review finds real learning beyond some label priors and continued epoch20–40
improvement, not a demonstrated plateau or a proven encoder/dynamics bottleneck.
METHOD_V23_DIAGNOSTIC therefore freezes18 training-only budget/capacity runs,
with snapshots0/40/80/160 and no development inputs. Independent prefit review
passed, including all531tensor hashes in9epoch40 reference checkpoints from
Grid03 FULL. Implementation and validation precede fitting. No new architecture
or JEPA improvement is established by this diagnostic protocol.

V2.3 implementation gate: standalone `two_player_v23_diagnostic` runtime, metrics
and artifact-only report implemented. Full regression210 PASS in124.519s and
final targeted27 PASS in13.952s. Independent review caught and repaired the
post-ledger byte-cap boundary. Four snapshot files, all online/EMA/Adam tensors,
fresh-only execution, failed-cell budget accounting and no development inputs
are verified. No new fitting yet; next action is source commit/push then the
frozen18-run grid. Local generated output remains excluded from Git and Obsidian.

Reproduction commands (PowerShell; after setting both OPENBLAS_NUM_THREADS and
OMP_NUM_THREADS to1, with the verified Python3.11.9 environment):

```text
python -B -m two_player_v23_diagnostic.runtime chess_data/v22-full-01 chess_data/v23-fit-01
python -B -m two_player_v23_diagnostic.report chess_data/v23-fit-01 chess_data/v23-fit-01-report
```

The report output must be outside the immutable run directory. This is a
training-fit diagnostic, not a replacement development strength evaluation.

V2.3 subsequently executed at20f457c63bf07b2dd7f1a9eb9d5528d5d93cbc37:
18/18 complete,160epochs each,72snapshots, no failure/collapse/protected scoring.
Strict report and independent audit PASSED. Total cellwork1627.083500s, maximum
lifetime RSS137,879,552bytes,142,867,189bytes local outputs. All6family/capacity
groups still make material training progress; larger capacity helps3/3seeds
for eachfamily. Direct fits train labels better thanrawJEPA in every paired
seed/capacity. Read V23_FIT_DIAGNOSTIC and V23_INDEPENDENT_RESULTS_REVIEW.

Prospective decision: common128/64×160 operating point for a future development
comparison, no convergence claim or candidate-only extension. METHOD_V24_ORDER_PROBE
freezes one training-only fixed-target H1 restriction probe before any broad
architecture grid. No new development score or JEPA promotion follows from it.

V2.4 prelaunch: separate read-only probe implementation reviewed independently;
239 full-regression tests passed133.537s, final output-hash guard regression suite
11 passed4.852s. Saved disjoint packing precedes model-loading verification;
direct never invokes its unused dynamics. Positive provisional reports are
invalidated if any final guard fails. No real measurement at this source update.
Launch only after commit/push and vault sync:

```text
python -B -m two_player_v24_probe.runtime chess_data/v23-fit-01 chess_data/v22-full-01 chess_data/v24-order-01
```

Executed once at0a7edef:18/18 complete,72 contextual rows,12.875268s,103,759,872
bytes peak RSS; no fits or new evaluation decisions. Allfour primary screens
and their nonterminal sensitivities fail. Read V24_ORDER_RESULTS; retain the
negative finding and do not attribute prior JEPA errors to a demonstrated
additive-order floor. Independent artifact audit is a separate gate.

V2.4 actual-artifact audit subsequently PASSED, preserving all negative screens.
V2.5 frozen method16c4428 implements complete-reply consistency and strong
contemporaneous controls. Independent source review passed after repaired
terminal-perspective, inter-cell resource-journaling and metric-schema issues.
Full290 tests pass106.256s; final49 V2.5 tests pass10.385s. No research fitting
in these checks. After source push/vault sync, launch exactly once:

```text
python -B -m two_player_v25.runtime chess_data/v22-full-01 chess_data/v22-development-01 chess_data/v25-grid04
python -B -m two_player_v25.report chess_data/v25-grid04 chess_data/v25-grid04-report
```

One CPU/BLAS thread,42 cells,160 epochs,600s/cell,25200s cumulative cell cap,
3GB local-output and1GB lifetime RSS cap. Protected splits stay closed.

Grid04 executed at5102ea0588198f993874a495d18bfef1e868e2ec but stopped
INCONCLUSIVE after3 direct cells completed and cell4 failed its1GB peak-RSS
guard (1,004,228,608 bytes);38 cells never started. Cellwork496.259139s includes
failed136.737907s; wall503.946364s. Independent monitor-only reproduction proves
unbounded ctypes type retention in the inherited RSS helper. The failed attempt
is preserved. Its ledger counts1254 saved learned decisions, but source/trace
prove an additional418 computed and unsaved; controls836. No partial outcome
scores used for adaptation. V25_RUNTIME_AMENDMENT prescribes only monitor and
provenance repair, followed after gates by one fresh42-cell grid05 from seeds.
