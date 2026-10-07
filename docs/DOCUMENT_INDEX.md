# Project documentation inventory

Intake: 2026-09-29. This index classifies originals without deleting or rewriting historical evidence. All entries are copied unchanged to the same relative path under `D:/notes/vault_1/Caissa-JEPA/`, except subsequently updated current documents whose latest copy must be synchronized.

| Document | Status / interpretation |
| --- | --- |
| `GROUND_TRUTH.md` | Current session authority and resume entry; read first |
| `AGENTS.md` | Active project collaboration rules |
| `README.md` | Current two-player research entry plus legacy chess compatibility |
| `docs/V28_DATA_POWER_PROTOCOL_V01.md` | Initial prefit data/power protocol; superseded in status by amendments, retained as immutable history |
| `docs/V28_DATA_POWER_PROTOCOL_V02_AMENDMENT.md` | DEV01-driven component-first and family-diversity correction; historical plan |
| `docs/V28_DATA_POWER_PROTOCOL_V03_AMENDMENT.md` | DEV02/03 support allocation and fixed 48-quota pilot; superseded after DEV04 |
| `docs/V28_DATA_POWER_PROTOCOL_V04_AMENDMENT.md` | DEV04-driven 96-quota DEV05 plan; audit implementation was defective, so its pilot has no valid pass status |
| `docs/V28_DATA_POWER_PROTOCOL_V05_AMENDMENT.md` | Historical scope pivot to Connect4 6x7 plus Reversi6; pilot details superseded by v0.6 |
| `docs/V28_DATA_POWER_PROTOCOL_V06_AMENDMENT.md` | Historical exact-split correction; DEV07 stopped before output |
| `docs/V28_DATA_POWER_PROTOCOL_V07_AMENDMENT.md` | DEV09 protocol and passed prefit data audit; no training approval |
| `docs/V28_MATCH_POWER_PROTOCOL_V08_AMENDMENT.md` | Paired-match primary estimand after the DEV10 exact-root feasibility failure; pre-fit proposal |
| `docs/validation/V28_MATCH_SCHEDULE_V08_COMMITMENT.json` | 9,600-block deterministic schedule and scenario-power commitment; no outcomes, evaluator or power gate pass |
| `docs/validation/V28_DATA_SPLIT_DEV01.json` | Failed original split feasibility receipt |
| `docs/validation/V28_DATA_SPLIT_DEV02_DEV05.json` | Model-blind data diagnostic receipts; DEV05 support gate caveat documented |
| `docs/validation/V28_DATA_SPLIT_DEV06.json` | DEV06 support-feasibility receipt; excluded from fitting after split-schedule enforcement review |
| `docs/validation/V28_DATA_SPLIT_DEV09.json` | Passed strict data-audit receipt for synthetic Connect4 6x7 + Reversi6; raw records are ignored and training is unapproved |
| `ROADMAP.md` | Current milestones and evidence/kill gates |
| `METHOD_SPEC.md` | Frozen original v1; read amendments before implementation |
| `METHOD_SPEC_V212.md` | Current V2.12-06 specification; retains the reviewed v05 raw-state amendment and adds the adopted Adam/EMA update contract; all operational gates remain closed |
| `docs/METHOD_SPEC_V212_V05.md` | Immutable v05 method-spec archive, including the adopted raw-state contract before optimizer semantics were versioned |
| `docs/METHOD_SPEC_V212_V06_ADAM_EMA_AMENDMENT.md` | Adopted narrow v06 optimizer amendment; it opens no data, profile, inference, or training gate |
| `two_player/v212_model.py` and `tests/test_v212_model.py` | No-update six-arm objective/gradient graph and synthetic checks; not a trainer, compute profile, or fit authorization |
| `docs/V212_FLOP_COUNTER_COVERAGE_AUDIT_DRAFT_01.md` | Static source inventory plus optimizer-only analytical accounting subcomponent; unresolved eigensolver and full-counter coverage, not a profile authorization |
| `docs/V212_TRAINING_FLOP_PROFILE_PROTOCOL_DRAFT_03.md` | Accepted v06 preregistration only; profile remains unauthorized and requires fixed 64-window enforcement, exact-rule replay, full counter/branch bounds, frozen runtime, and all separate gates |
| `tools/v212_optimizer_flop_accounting.py` and `tests/test_v212_optimizer_flop_accounting.py` | Analytical scratch Adam/EMA arithmetic intervals and synthetic formula checks; not a full counter/profile or fit authorization |
| `tools/v212_model_matmul_flop_accounting.py` and `tests/test_v212_model_matmul_flop_accounting.py` | Mask-parameterized explicit model matmul counts, including manual backward and covariance products; not a full counter/profile |
| `tools/v212_model_activation_flop_accounting.py` and `tests/test_v212_model_activation_flop_accounting.py` | Mask-parameterized affine-bias/tanh/derivative and separate value-gradient scaling subcounter; other objective and eigensolver work remains open |
| `tools/v212_model_loss_residual_accounting.py` and `tests/test_v212_model_loss_residual_accounting.py` | Mask-parameterized loss residual subtraction and squared-error shape inventory; square convention and remaining objective/reduction/LAPACK work remain open |
| `tools/v212_model_reduction_shape_accounting.py` and `tests/test_v212_model_reduction_shape_accounting.py` | Candidate mask-parameterized NumPy reduction counts including source-expanded v2.4.6 root `std`; loaded runtime/kernel, summation fingerprint, and LAPACK treatment remain open |
| `two_player/v212_trajectory_audit.py`, `two_player/v212_window_batch.py`, and `tests/test_v212_window_batch.py` | Exact-rule in-memory episode/window audit, canonical Window payload digest, and train-only adapter enforcing 64 rows per batch (narrow guard independently reviewed); synthetic fixtures only, no file/data I/O, selection, trainer, or gate authorization |
| `two_player/v212_scheduled_batch.py` and `tests/test_v212_scheduled_batch.py` | No-update paired six-arm batch-call boundary; enforces 64 rows/32 per game and shared read-only adapter input, but does not verify a frozen manifest/replay or provide a trainer/profile |
| `two_player/v212_schedule_manifest.py`, `tests/test_v212_schedule_manifest.py`, and `docs/V212_SCHEDULE_MANIFEST_AUDIT_DRAFT_02.md` | Current structural 20×87 manifest validator; v02 adds per-window payload digests and cross-epoch stability checks, but not provenance, full-episode replay, trainer integration, or profile authorization |
| `two_player/v212_episode_replay_receipt.py`, `tests/test_v212_episode_replay_receipt.py`, and `docs/V212_EPISODE_REPLAY_RECEIPT_AUDIT_DRAFT_01.md` | Synthetic in-memory full-episode replay/content receipt and derived-window digest list; no source-file provenance, schedule/trainer binding, or gate authorization |
| `two_player/v212_receipt_bound_schedule.py`, `tests/test_v212_receipt_bound_schedule.py`, and `docs/V212_RECEIPT_BOUND_SCHEDULE_AUDIT_DRAFT_01.md` | No-update preflight seam for replay-receipt/window/mask/seed binding to one schedule row; high-level test is mocked, duplicate materialization remains, no exclusive trainer or profile authorization |
| `docs/V212_SCHEDULE_MANIFEST_AUDIT_DRAFT_01.md` | Retained v01 structural schedule schema before window-payload digest binding |
| `two_player/v212_scratch_optimizer.py` and `tests/test_v212_scratch_optimizer.py` | Pure scratch Adam/clipping/EMA arithmetic with synthetic tests; no persistent updates, trainer, or profile |
| `docs/V212_TRAINING_FLOP_PROFILE_PROTOCOL_DRAFT_01.md` | Rejected preregistration retained as history; ≤5% gate untested and unpassed |
| `docs/V212_TRAINING_FLOP_PROFILE_PROTOCOL_DRAFT_02.md` | Accepted preregistration for v05, superseded as current protocol by draft 03 after v06 adoption |
| `docs/V212_TRAINING_FLOP_PROFILE_PROTOCOL_DRAFT_03.md` | Independently accepted preregistration for v06 only; now states the existing direct-leaf per-batch valid-H4 rejection condition; opens no data/profile gate and ≤5% remains untested and unpassed |
| `docs/V212_ADAM_EMA_SEMANTICS_AMENDMENT_DRAFT_01.md` | Review record for the Adam/EMA semantics adopted by v06; no profile/training authorization |
| `docs/METHOD_SPEC_V212_V04.md` | Immutable v04 specification archive; includes the Reversi8 2-second p90 negative and pre-v05 raw-state wording |
| `docs/METHOD_SPEC_V212_V05_RAW_STATE_AMENDMENT.md` | Adopted narrow v05 raw-state amendment; method-level review only, no trainer/fit authorization, ≤5% FLOP gate untested and unpassed |
| `docs/METHOD_SPEC_V212_V05_ROOT_SAMPLING_DRAFT.md` | Unreviewed §7 replacement originally based on v04; not current v05, must be rebased and versioned before any future adoption |
| `docs/METHOD_V28_PLANNER_V04_AMENDMENT.md` | Historical exact-root-regret candidate; DEV10 showed current 6x7 oracle budget unresolved |
| `docs/METHOD_V28_PLANNER_V05_AMENDMENT.md` | Current paired-match candidate; pre-fit redesign, independent method review signed off; evaluator/power gate pending |
| `docs/METHOD_V28_SUPERVISED_V02_AMENDMENT.md` | Separate implementation-aligned supervised reply-set JEPA candidate; prefit draft, not frozen/reviewed/trained |
| `docs/V28_MODEL_V02_REVIEW_01.md` | Independent implementation/objective review; no P1, training and V08 gates remain closed |
| `docs/validation/V28_ROOT_ORACLE_DEV10_PILOT.json` | Five-root Connect4 6x7 exact-label pilot; 0/5 complete maps under frozen local budget |
| `docs/METHOD_AMENDMENTS.md` | Active v1.2 middle/late feasibility design and objective controls |
| `docs/RELATED_WORK.md` | Primary-source positioning review; not an exhaustive publication review |
| `docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md` | Research-only statistical source and analytical yield-sensitivity audit; no simulation/root generation authorization |
| `docs/DATA_SOURCES.md` | Source/license register; no external data acquired |
| `docs/TWO_PLAYER_PILOT_20260929.md` | Executed exploratory 21-run evidence, ceiling/negative results and limitations |
| `docs/INDEPENDENT_REVIEW_20260929.md` | Independent agent findings, repairs and unresolved scientific issues |
| `docs/WORKING_PAPER.md` | Exploratory research-note draft; not submission-ready |
| `docs/METHOD_V2.md` | Frozen recurrent reply-fork v2 development specification |
| `docs/V2_RESEARCH_CONTROL.md` | Adaptive development, baseline fairness and protected evaluation stages |
| `docs/V2_PREDICTIVE_RESEARCH.md` | Primary-source predictive consistency review |
| `docs/V2_GAME_EVALUATION_RESEARCH.md` | Game planning, benchmark and adaptive-evaluation review |
| `docs/V2_FORK_GEOMETRY_NOVELTY.md` | Follow-up novelty risks and sibling-loss algebra |
| `docs/BENCHMARK_V2_SPEC.md` | Prospective rule-only survey protocol and amendments |
| `docs/V2_SURVEY_RESULTS.md` | All survey attempts, failures and immutable fork audit |
| `docs/V2_EXPERIMENT_LOG.md` | Attempt ledger including failed candidates and finite grid sequence |
| `docs/V2_GRID01_RESULTS.md` | Executed36-run development outcome; not promoted |
| `docs/V2_INDEPENDENT_RESULTS_REVIEW.md` | Independent action/hash/schedule audit of completed v2 grid |
| `docs/METHOD_V21.md` | Prospective symmetry/auxiliary-weight amendment; no change to original v2 |
| `docs/V2_GRID01_DIAGNOSIS.md` | Read-only training probes motivating finite follow-up; exploratory |
| `docs/V21_GRID02_RESULTS.md` | Executed60-run augmentation/weight study; not promoted |
| `docs/V21_INDEPENDENT_RESULTS_REVIEW.md` | Independent decisions/hashes/RNG schedule replay |
| `docs/V22_MECHANISM_ANALYSIS.md` | Unimplemented sibling-loss proposal, bounds and counterexample |
| `docs/V22_LABEL_BUDGET_OPTION.md` | Exploratory design options, superseded for execution by METHOD_V22 |
| `docs/METHOD_V22.md` | Frozen restricted-label development specification; executed in Grid03 |
| `docs/V22_PREFIT_REVIEW.md` | Independent masked-model/runtime/data and actual-artifact review |
| `docs/V22_GRID03_RESULTS.md` | Executed 72-run restricted-label study; not promoted |
| `docs/V22_INDEPENDENT_RESULTS_REVIEW.md` | Independent decisions, tensor equivalence and all schedule/count checks |
| `docs/V21_VALUE_ALIGNMENT_DIAGNOSIS.md` | Post-hoc value/latent error diagnosis of 18 selected Grid02 checkpoints |
| `docs/METHOD_V23_DIAGNOSTIC.md` | Frozen 18-run training-only convergence/capacity protocol; not a superiority study |
| `docs/V23_PREFIT_REVIEW.md` | Independent runtime/metrics/failure-path review before the training-only diagnostic |
| `docs/V23_FIT_DIAGNOSTIC.md` | Executed 18-run training-fit diagnosis; common budget/capacity effects, no JEPA promotion |
| `docs/V23_INDEPENDENT_RESULTS_REVIEW.md` | Actual source/checkpoint/schedule/root-metadata audit of all 18 runs |
| `docs/METHOD_V24_ORDER_PROBE.md` | Frozen single training-only H1 ordering probe and common future budget decision |
| `docs/V24_ORDER_PREFIT_REVIEW.md` | Independent mathematical/specification review; implementation not yet reviewed |
| `docs/V24_DESIGN_CONSTRAINTS.md` | Prospective controls and claim boundaries for future development |
| `docs/V24_MECHANISM_CRITIQUE.md` | Random minimum-probe proposal deferred after mathematical counterexamples |
| `docs/V24_ADDITIVE_DYNAMICS_LIMIT.md` | Conditional additive-transition order restriction; relevance awaits measurement |
| `docs/EXTERNAL_REFERENCE_FEASIBILITY.md` | Official OpenSpiel compatibility/license/source inspection; no engine acquired |
| `docs/V23_RESEARCH_OPTIONS.md` | Conditional action-dependent dynamics proposals and verified prior-art limits; not an implemented method |
| `docs/PROFESSOR_BRIEF_V2.md` | Vietnamese discussion brief; separates evidence from missing publication requirements |
| `V7_RESEARCH_PROTOCOL.md` | Current implemented chess v3 protocol; separate from multi-game protocol |
| `docs/RESEARCH_IDENTITY.md` | Current implemented MARS-JEPA Chess identity |
| `docs/MARS_JEPA_RESEARCH_IDENTITY.md` | Duplicate current chess identity detail |
| `docs/MARS_HARDENING.md` | Historical f8588e8 handoff with explicit superseding v3 note |
| `docs/RESEARCH_DECISIONS.md` | Current chess decisions, superseding the earlier roster |
| `TECHNICAL_GUIDE.md` | Historical code tour; some objective/UI descriptions are superseded; verify against source |
| `PROMPT_FOR_MARS_JEPA_RESEARCH_HARDENING.md` | Preserved user-authored historical specification; superseded by current request |
| `PROMPT_FOR_RESPONSE_JEPA_CLEANUP.md` | Preserved earlier specification; identity/branch instructions superseded |
| `docs/WORKSPACE_MIGRATION.md` | Historical 2026-09-12 migration receipt; not current workspace authority |
| `docs/D_DRIVE_DATASET_MIGRATION.md` | Historical data copy and quality warning; no current data authorization |
| `docs/MIGRATION_CLEANUP_20260913.md` | Historical migration state; active current task is C: workspace |
| `docs/PIPELINE_AUDIT_20260913.md` | Historical failures and proposed repairs; distinguish later hardening |
| `docs/PIPELINE_RECOVERY_20260913.md` | Explicitly superseded recovery receipt; old data subsequently removed |
| `docs/RELEASE_7_1.md` | Historical packaged release, with current source hardening note |
| `docs/validation/RELEASE_7_1.md` | Historical 41-test/build receipt; fixture-only evidence |
| `docs/validation/VALIDATION.md` | Historical 2026-09-05 receipt; outdated roster/runtime |
| `docs/research-internal/claim-ledger.md` | Historical research/source map; reverify sources for new design |
| `docs/research-internal/report-source.md` | Explicitly superseded historical research handoff |

Initial original project Markdown count: 20 (18 tracked, 2 untracked). Ground Truth and this index bring the first snapshot to 22. Later research documents must be added to the mirror too. Non-Markdown screenshots/JSON receipts stay in the repository and are not part of the requested Markdown mirror.
# Latest V2.4 result

- `V24_ORDER_RESULTS.md`: executed training-only order probe; no material
  obstruction established. It supersedes prospective no-result statements in
  the frozen protocol/review for status only, not their unchanged definitions.
- `V24_INDEPENDENT_RESULTS_REVIEW.md`: verified actual packing, artifacts and
  negative-screen arithmetic, without new fitting or encodings.
- `METHOD_V25.md`, `V25_PREFIT_REVIEW.md`: active frozen42-cell development
  specification and independent method review; not an executed result.
- `V25_ROBUST_PREDICTION_RESEARCH.md`: primary-source follow-up and explicit
  novelty limits for robust complete-reply consistency.
- `V25_RESEARCH_POSITIONING.md`: professor-facing conditional argument and
  claim boundaries, prepared without partial outcome inspection.
- `V25_GRID04_FAILURE_AUDIT.md`: first attempt's resource failure, monitor-only
  causal reproduction and explicit unsaved-prediction accounting.
- `V25_RUNTIME_AMENDMENT.md`: prospective minimal engineering repair; original
  scientific method/source retained and all42 cells must restart fresh.

## V2.6 current development

- `V25_POSTRUN_RESEARCH_UPDATE.md`: post-grid05 primary-source update and
  candidate question; focused review, not an exhaustive systematic review.
- `METHOD_V26.md`: revised, unfrozen proposal for held-out-variant sequential
  JEPA; no labels, model fitting, or performance result yet.
- `validation/V26_INTERFACE_SMOKE_01.json`: exploratory feature/action and
  sampled two-ply closure receipt against project-owned reference rules.
- `validation/V26_ORACLE_FEASIBILITY_01.json`: exploratory exact solver cost
  receipt; timeout/coverage gate currently blocks production labels.
- `benchmarks/alpha_beta_reference.py` and `test_alpha_beta_reference.py`:
  exact bounded alpha-beta oracle and value/budget regression tests.
- `validation/V26_ORACLE_FEASIBILITY_02.json`: same-seed comparison showing
  improved feasibility over plain negamax, still below a root-bank pass gate.
- `tools/v26_oracle_cost_probe.py`: fixed-seed oracle-cost probe for
  Connect4 variants and Reversi6/8; it records outcome-count diagnostics, not
  exact action-value labels.
- `validation/V26_ORACLE_FEASIBILITY_03_*.json`: exploratory per-root probe
  receipts; none is eligible for locked confirmation reuse.
- `validation/V26_ORACLE_FEASIBILITY_04_*.json`: gravity Connect4-4x5 easier and
  early-ply cost strata; coverage remains exploratory.
- `validation/V26_ORACLE_FEASIBILITY_05_CONNECT4_8X8*.json`: larger-board exact
  label-cost samples; a useful search challenge currently exceeds solver caps.

## V2.7 pivot feasibility (proposal only)

- `V27_PRIOR_ART_REAUDIT_20260930.md`: targeted source audit that adds Deep
  Latent Competition, MA-JEPA, minimax-Q/value-equivalence, and learned
  minimax-search ranking precedents; it supersedes the earlier realized-reply
  novelty candidate, but is not a systematic review.
- `V27_RESEARCH_POSITIONING.md`: targeted prior art, estimand change, provisional
  method family, data/evaluation gates and stop criteria; not frozen and not a
  novelty claim.
- `V28_KLENT_JEPA_COMPARISON_DESIGN.md`: new V2.8 candidate design for a fair
  direct policy/Q versus JEPA-augmented comparison; not frozen, implemented, or
  evidence.
- `KLENT_CLEANROOM_BASELINE_SPEC.md`: equation-level K0.1 clean-room baseline
  spec and synthetic fidelity gates; a documented CAISSA adaptation, not a
  reproduction of upstream code or paper-scale results.
- `../two_player/klent_baseline.py`, `../two_player/klent_model.py`, and
  `../test_klent_baseline.py` / `../test_klent_model.py`: K0.1 target/return
  utilities, shared-backbone policy/Q learner and self-play collection/fitting;
  focused synthetic correctness tests, not game-strength evidence.
- `../tools/v28_klent_countup_probe.py`: source-hashed exploratory convergence
  probe on a seven-state synthetic game; its generated raw receipt stays under
  the excluded `chess_data/` tree, with only a small aggregate receipt eligible
  for source control.
- `V28_KLENT_COUNTUP_01.md` and `validation/V28_KLENT_COUNTUP_01.json`: compact
  historical report and receipt for the three-seed Count Up probe. Independent
  review found that its reported policy error scores the improvement target,
  not the learned policy; the report includes this correction. The raw
  state-level receipt remains ignored.
- `../tools/v28_klent_countup_probe_v2.py`: corrected follow-up that evaluates
  the learned network policy and improvement target separately, and hashes
  trajectory identity/role/model metadata. It is an engineering diagnostic,
  not board-game or JEPA evidence.
- `V28_KLENT_COUNTUP_02.md` and `validation/V28_KLENT_COUNTUP_02.json`: corrected
  post-commit, three-seed Count Up receipt. Learned-policy TV is 0.0195–0.0284;
  the one-step improvement-target TV is 0.0161–0.0203. The target remains
  slightly better fit than the learned policy; this establishes no JEPA benefit.
- `KLENT_K0_1_INDEPENDENT_REVIEW.md`: read-only implementation audit, findings,
  repairs and scope limits.
- `V28_PRIOR_ART_DELTA_20260930.md`: targeted primary-source update for H-JEPA,
  ActSWM, Action-Conditioned Predictive Consistency and TD-JEPA; it narrows
  action-sensitivity and transfer novelty claims and records the remaining
  role-conditioned adversarial-game question as unverified.
- `V28_REVERSI4_RULES_GATE_01.md` and `validation/V28_REVERSI4_RULES_GATE_01.json`:
  completed, post-commit model-blind exhaustive rules/transition/two-ply
  subgate for project-owned Reversi4. It is not a data-split/power pass or
  game-strength result.
- `V28_SPLIT_PROTOCOL_REVIEW_01.md`: independent audit of dataset/split,
  situation-bank, opponent-power, and confirmation gaps. It recommends the
  next model-blind gate and does not support training or a JEPA claim yet.
- `V28_PLANNER_DESIGN_AMENDMENT.md`: proposed correction that makes learned
  latent rollouts drive a fixed-depth max-min planner and exact-root regret the
  primary endpoint. It supersedes the auxiliary-only JEPA comparison as the
  primary V2.8 question; it is not frozen or implemented.
- `METHOD_V28_PLANNER_V01.md`: frozen development-candidate algorithm and
  losses/controls for reply-set latent max-min planning; model fitting remains
  gated on fresh data/power and independent review.
- `METHOD_V28_PLANNER_V02_AMENDMENT.md`: independent-review corrections for
  immediate terminal branches, all-root oracle coverage, target-source matching,
  player-perspective equations, and a frozen data sampler; design only.
- `METHOD_V28_PLANNER_V03_AMENDMENT.md`: implementation-contract corrections
  for branch counters, adapter validation, terminal return indexing, and test
  coverage; no learned model/result.
- `V28_MODEL_BLIND_GATE_DEV03.md` and
  `validation/V28_MODEL_BLIND_GATE_DEV03.json`: fixed-schedule model-blind
  historical exploratory receipt, superseded; cache metadata is corrected and
  the old runner lacked quota/support pass enforcement.
- `V28_MODEL_BLIND_GATE_DEV06.md` and
  `validation/V28_MODEL_BLIND_GATE_DEV06.json`: authoritative corrected gate;
  Connect4 4x5 100/100 and Reversi6 150/150 exact maps under 200k nodes, 2s,
  500k cache; support/coverage/rule checks pass, no power or model comparison.
- `V28_DATA_POWER_PROTOCOL_V01.md`: pre-fit proposal for self-play provenance,
  opponent-family holdouts, trajectory/counterfactual split audits, power, and
  locked confirmation; not implemented and does not authorize training.
- `V28_DATA_POWER_PROTOCOL_V02_AMENDMENT.md` and
  `validation/V28_DATA_SPLIT_DEV01.json`: model-blind trajectory/branch split
  pilot failed on Connect4 overlap and positional-policy support; component-first
  splitting and a more diverse pinned policy are required before another pilot.
- `../tools/v28_modelblind_gate.py`, `../tests/test_v28_modelblind_gate.py`,
  `../two_player/planner.py`, and `../tests/test_v28_planner.py`: root schedule,
  exact-oracle/rule check and depth-two max-min planner; focused unittest scope
  only, not strength evidence.
- `V28_GAME_FEASIBILITY_01.md` and `validation/V28_GAME_FEASIBILITY_01.json`:
  24-root no-gravity Connect4 4x5 exact-oracle cost probe (12/23 complete).
  It rejects that tiny sample as a production bank and does not select a
  scientific V2.8 game.
- `../tools/v28_reversi4_rules_gate.py` and
  `../test_v28_reversi4_rules_gate.py`: independent coordinate-ray rules
  comparator, exhaustive gate runner, and bounded regression tests; no
  third-party engine or training data is used.
- `../tools/v27_match_feasibility.py` and `../test_v27_match_feasibility.py`:
  deterministic project-owned match-schedule feasibility helper and its tests;
  not a strength benchmark.
- `validation/V27_MATCH_FEASIBILITY_01.json`: 96 game records across
  Connect4-gravity-8x8 and Reversi8. Tiny random/sanity-heuristic pilot only;
  unsuitable as the learned-model opponent bank. No self-play dataset or model
  training has been produced.
- `../benchmarks/v27_search_opponent.py` and
  `../tools/v27_search_opponent_probe.py`: shallow bounded-search feasibility
  policy, code—not an engine—and a paired-seat exploratory schedule.
- `validation/V27_SEARCH_OPPONENT_01.json`–`04.json`: successive model-blind
  opponent feasibility receipts. They expose Reversi seat bias and search node
  exhaustion; none is model-selection or confirmatory evidence.
- The V2.7 prior-art review now includes Deep Latent Competition and the
  2026-09-27 MA-JEPA preprint. Subsequent full-text review of KLENT (ICML 2026
  accepted) makes regularized direct policy/Q a required compute-conscious
  baseline; the official code repository's license is not established and was
  not downloaded or used. Novelty risk remains critical; no unique method claim
  is frozen. See `V27_PRIOR_ART_REAUDIT_20260930.md` and the unimplemented
  `V28_KLENT_JEPA_COMPARISON_DESIGN.md`.
