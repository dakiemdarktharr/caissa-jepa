**Project review and paper-completion proposal — 25 October 2026**

Reviewed repository: [dakiemdarktharr/caissa-jepa](https://github.com/dakiemdarktharr/caissa-jepa), local and remote `main` at `b3e14fde7fd389956626bd4374f9cca74e81a8f2` before this report. User constraints: no fixed deadline or venue; up to **US$50/month on Vast.ai**; the paper should contribute a novel approach, without requiring JEPA superiority.

**Recommendation:** turn this into **Counterplay: Counterfactual Audits of Latent Planning in Adversarial Games**. Preserve CAISSA-JEPA as the historical implementation name. The next paper should ask which opponent-reply distinctions a predictive representation must preserve for a decision to remain sound. JEPA becomes one experimental family, alongside value-only, decoded-state and exact-state controls.

The project is technically salvageable and has useful reusable infrastructure and negative evidence. It is not currently a completed research method, a reproduced end-to-end V2.12 experiment, or a submission-ready paper. Its largest immediate risks are objective correctness, an unsuitable superiority-driven completion rule, architectural confounding of board-size transfer, and an expanding infrastructure workload. More GPU time alone will not resolve these problems.

This report proposes a new study; it does not silently amend V2.12, rename packages, change historical results, or launch paid computation. A complete manuscript is a controllable deliverable. High novelty and publication acceptance cannot be guaranteed in advance.

**October 25 follow-up — chess and data recovery:** the [chess/Elo and data-readiness note](COUNTERPLAY_CHESS_AND_DATA_READINESS_2026-10-25.md) records the proposed chess extension and a newly located local Windows archive outside this checkout. It contains 1,694 historical experiment files (932,981,707 bytes); selected V2 and DEV09 data match the historical receipt hashes. The active checkout still lacks an accepted current corpus. Earlier statements about missing artifacts describe the checkout, not absence from every local archive. Recovery improves historical reproducibility but does not make DEV09 compatible with V2.12 or establish a current chess dataset. The [fresh inventory receipt](validation/DATA_READINESS_2026-10-25.json) documents this narrower verification.

**1. Review coverage and fresh verification**

The repository inventory contains 631 tracked files: 339 Python files, 196 Markdown files, 59 JSON files, and assets/figures/build scripts. I mapped every tracked path and Python top-level definition, parsed every Python file, checked the JSON evidence, and followed the current method, objective, optimizer, rules, trajectory/window/schedule boundaries, references, runtime proposals, historical experimental reports and repository history. I also examined the legacy chess pipeline's audit/recovery history. This is a repository-wide research/engineering review, not a claim of exhaustive formal verification or a line-by-line certification of every archived version.

GitHub's API showed the same `main` commit as the local checkout, one branch, no returned issues, and zero Actions runs. The initial working tree was clean. There are no tracked GitHub workflow files, top-level license, or citation metadata. An empty issue tracker does not imply an absence of defects; the issue record currently lives largely in Markdown.

Fresh checks used Linux, Python 3.11.9 and NumPy 2.4.6, with BLAS/OMP threads set to one:

| Check | Result | What it establishes |
| --- | --- | --- |
| Parse all tracked Python | 339/339 parsed | Syntax, not correctness |
| Parse curated JSON | 59/59 with UTF-8 BOM handling | One historical file has a BOM; a strict `utf-8` JSON reader rejects it |
| Current `tests/` suite | 617 tests: 612 passed, 3 errors, 2 skipped; 121.227 seconds | Current-source behavior within available fixtures/environment |
| V2.12 subset within that suite | 488 tests, all passed | Existing objective, schedule, receipt, accounting, reference and mocked-supervision checks |
| Selected root-level rules/reference/model suites | 68 tests: 63 passed, 5 skipped; 15.495 seconds | Additional historical model and independent-rule regression coverage |
| New targeted gradient probe | Objective/gradient mismatch reproduced in all six V2.12 arms | A real defect missed by the passing suite |

Two errors require missing `chess_data/v29_fit_panel_dev01/panel.json`; the third reaches a Windows-only V2.9 supervisor guard. The two skips concern Windows behavior. The five additional skips require unavailable pinned external Reversi source. The full Qt GUI, Windows installer, all root-level tests, live systemd failure paths and historical research runs were not executed. No protected final outcomes were opened. No production training, matches, corpus generation, GPU rental or model selection occurred; tests used their temporary fixtures.

[Machine-readable review evidence](validation/PROJECT_REVIEW_2026-10-25.json) records the new checks. The earlier [handoff verification](handoff/VERIFICATION_2026-10-25.md) is historical evidence from its own execution, not a substitute for these fresh checks.

**2. What the project has become**

There are three distinct layers:

| Layer | Existing assets | Present role |
| --- | --- | --- |
| Legacy CAISSA/MARS chess application | PySide6 UI, chess rules, ingestion, FEN tools, model registry, cache/resume, arena, installer | Historical application and engineering work; not the active paper's experimental system |
| Two-player research history, V1–V2.11 | Tiny-game and larger-board datasets/protocols, NumPy models, exact/learned planning, development grids, negative-result receipts | Pilot evidence and reusable rules/model/evaluation code |
| V2.12-06 | Six-arm objective/manual gradients, scratch Adam/EMA, replay/window/schedule helpers, partial cost counters, runtime proposals | Pre-training research implementation; not an integrated production trainer |

The active specification trains one shared model on Connect Four 6×7 and Reversi6, with Connect Four 8×8 and Reversi8 as board-size holdouts. It uses 198 input features, a 32-dimensional latent, 65 action IDs, recursive prediction at 1/2/4 plies, exact legal transitions and terminal utility, and four-ply alternating max/min search. The value head predicts terminal outcomes under a specified behavior-policy mixture. It is not trained on minimax values and does not model a particular opponent.

Its six arms are multi-step JEPA, two-ply-only latent JEPA, recursive decoded-state prediction, value-only latent rollout, exact direct-leaf value, and one-ply-only latent JEPA. The adopted decoded arm is `F → D → E`, including differentiation through the decoded features. The method specifies 928 windows per training game, 64-window balanced batches, 87 updates across three epochs, and 20 paired seeds. Those are planned counts, not evidence of an accepted corpus or completed training.

The current hypothesis remains: JEPA must beat all five controls on both held-out sizes and the macro score, at a specified margin and multiplicity-adjusted uncertainty, while passing compute gates. **That is no longer the right definition of project completion given your instruction.** Preserve it as the historical V2.12 hypothesis; write a separate prospective protocol for the new question.

**3. What changed, and what the experiments actually say**

The repository has 537 commits through the reviewed snapshot. The September application work evolved into a multi-game representation study, then into a broad implementation/audit program. The October 25 merge reconciled an incoming local checkout with 415 newer GitHub commits, preserved the older local edits in `e3d73bd`, merged to `4d67caf`, and published the handoff at `b3e14fd`. The merge's tracked tree matched the newer GitHub tree. This was reconciliation and documentation, not a new positive experiment.

| Stage | Evidence | Correct interpretation |
| --- | --- | --- |
| Initial pilot | 21 runs; exact-state search reached a diagnostic ceiling | The benchmark often could not discriminate learned objectives |
| V2 | 36 fits; selected projected JEPA regret 0.249145 versus value dynamics 0.247664 | No demonstrated advantage |
| V2.1 | 60 fits; raw-JEPA improvement 0.004826, interval crossing zero | Small descriptive movement; promotion failed |
| V2.2 | 72 fits; scarce-label raw JEPA regret 0.293339 versus direct 0.283917 | No demonstrated label-efficiency benefit |
| V2.3 | 18 longer/larger training diagnostics | All families fit better; direct fitted labels better than raw JEPA; not a strength study |
| V2.4 | Reused checkpoints; largest median order-bound ratio 0.002787 versus 0.10 screen | The proposed material order obstruction was not established |
| V2.5 | Repaired grid05 completed 42 fits; raw-tail exact regret 0.202446 versus direct 0.203775; hybrid 0.268340 | Tiny uncertain exact-state gain; learned rollout was worse; preserve grid04's failed runtime attempt |
| V2.8 | 60 fits, 320 games; JEPA minus task-value macro −0.01875 | No observed incremental benefit over the relevant dynamics control |
| V2.9 | 60 fits, 320 games; JEPA minus task-value macro −0.0625 | Three epochs did not rescue the recipe; duration-only continuation stopped |
| V2.10 | 400 train-only gradient diagnostic cells | Frozen conflict screen failed; not a justification for projected-gradient training |
| V2.11 | 20 candidate fits, 480 games; λ=8 macro −0.0500 versus task-value | Weight-only continuation failed; not evidence against every JEPA method |
| V2.12 | Random-weight V02 compute pilot: 1,152 cells, p90 0.7970 s, maximum 3.7419 s | Inference feasibility evidence for that historical proxy/hardware, not fitted-model performance |

V2.8 did have a positive descriptive macro contrast against direct-leaf (+0.0875); its unadjusted t interval crossed zero. This must coexist with the negative task-value comparison. V2.9's task-value macro interval was approximately [−0.12961, +0.00461]. These are exploratory results, not proof of equivalence or universal JEPA inferiority. Do not compare regret magnitudes across versions as one leaderboard: data, labels and protocols changed.

Sources: [master handoff](../MASTER_HANDOFF.md), [V2.8 analysis](validation/V28_DEVELOPMENT_MATCH_ANALYSIS_V01.json), [V2.9 analysis](validation/V29_DEVELOPMENT_MATCH_ANALYSIS_V01.json), [V2.10 review](V210_GRADIENT_DIAGNOSTIC_REVIEW_01.md), [V2.11 review](V211_DEVELOPMENT_RESULT_REVIEW_01.md), [V02 compute report](validation/V212_RANDOM_WEIGHT_COMPUTE_PILOT_02.md).

**4. Newly verified defects and design concerns**

**4.1 The covariance gradient does not differentiate the reported loss — high priority, confirmed.**

In `two_player/v212_model.py`, `_regularize` adds the unweighted variance and covariance derivatives into one `dz` (lines 195–214). `loss_grad` multiplies that combined derivative by 0.1 (line 257), while its scalar loss uses `0.1 * variance_loss + 0.01 * covariance_loss` (line 258). The covariance component therefore receives **10× its declared weight** in backpropagation. Every arm uses this path.

A deterministic synthetic finite-difference check at encoder coordinate `[125,31]`, seed 9, gives:

| Arm | Returned derivative | Numerical derivative of reported loss |
| --- | ---: | ---: |
| Multi-step JEPA | 0.007839358 | 0.040969020 |
| Recursive raw-state | −0.057281490 | −0.024151828 |
| Direct-leaf value | −0.062919870 | −0.029790208 |

All six arms have the same approximately −0.033129662 discrepancy on this fixture, matching the analytically predicted excess covariance derivative. This is a synthetic correctness probe, not a legal-board performance measurement. The existing finite-difference test samples only one coordinate per arm, mostly outside the encoder, and uses small-amplitude inputs. Its single encoder check does not expose this case. V2.8's inspected regularizer weights the two derivatives separately; do not retroactively attribute its historical results to this V2.12 defect.

Required repair: weight the two derivatives separately or inside the helper consistently with the scalar loss; verify directional derivatives across every parameter tensor and covariance-active inputs, with frozen EMA targets. Update source-bound accounting references when source changes. This report leaves implementation unchanged so the failure remains reproducible at the reviewed commit.

**4.2 Board-size transfer activates previously untrained coordinates — high priority, structural.**

`BoardGame.features` uses fixed 8×8 coordinates, and the encoder and action-conditioned predictor have dense position-specific weights. The union of the two training boards covers only the top-left 6×7 cells. An 8×8 board introduces **22 new cells, 66 previously zero input coordinates across the three feature planes, and 22 cell-action IDs never used in training**.

For the JEPA/value-rollout/direct arms, exact-state encoder rows for those coordinates receive zero input-driven gradient; their corresponding JEPA target rows retain the initialization through EMA. Predictor action rows for unseen action IDs receive no training examples. The raw-state re-encoder can receive gradients through its own decoded padded features, but that is not training on real occupancy/actions in the new cells. There is no spatial weight sharing that resolves this issue automatically.

This does not prove transfer must fail. It means the experiment confounds representation quality with unsupported position/action parameters. An 8×8 loss would not diagnose JEPA alone. Make same-size adversarial decision analysis primary. Treat size transfer as an extension requiring a shared spatial/graph architecture or an explicit parameter-coverage control.

**4.3 The computation requirement is fighting the architecture — high priority, design conflict.**

Equal examples, seeds and updates are useful controls. Requiring all six heterogeneous graphs to also land within 5% total FLOPs is a separate, restrictive requirement. The raw arm has 18,440 trainable parameters versus 11,906 for JEPA and 8,546 for direct-leaf. Its static forward count is 72,544 versus JEPA's 40,864 MAC/window. The repository's all-valid **partial** per-invocation ledger spans about 4.59 million to 27.13 million operations. These are not complete measured training FLOPs, and the formal gate remains untested; they are strong reasons to reconsider the design before expanding the counter project.

Recommended new protocol: a controlled equal-data/equal-update comparison for attribution, plus a separately specified equal-cost sensitivity or performance–cost curve. Report parameters, update count, forward/backward MAC estimates, measured fit time, model calls, exact-rule calls and evaluation time. Do not hide diagnostic eigensolver costs or use useless computation to manufacture parity. A change to the old gate must be versioned prospectively.

**4.4 Exact rules already generate every branch — scientific motivation needs sharpening.**

This system does not replace a costly simulator: exact transitions are already traversed to determine legal actions and terminal states. A tiny direct-state encoder is a serious baseline. The reason to learn latent dynamics must therefore be representation/decision structure or demonstrable useful computation savings, rather than an assumed simulator-free advantage. This is why an adversarial representation audit is a more natural use of the current system than a claim of a new general world-model planner.

**5. Consolidated issue register**

The table consolidates materially distinct known issues. Historical repairs are separated below; repeated Markdown warnings are not counted as new defects. “Open” means unresolved evidence or implementation, not necessarily a proven runtime failure.

| ID | Priority / status | Issue and consequence | Closure evidence |
| --- | --- | --- | --- |
| I01 | P1 confirmed | Covariance gradient mismatch | Corrected full-objective derivatives across all arms/tensors |
| I02 | P1 structural | Unsupported coordinates/actions confound board-size transfer | Same-size primary or reviewed shared spatial architecture plus coverage controls |
| I03 | P1 strategic | Paper completion depends on JEPA beating every control | New outcome-independent research question and completion checklist |
| I04 | P1 open | No integrated V2.12 trainer, persistent optimizer loop, checkpoint/resume path or fitted evaluator | One audited end-to-end fixture and fresh finite panel |
| I05 | P1 open | No accepted production corpus; DEV09 is incompatible with the new four-policy/16-pair/H4 contract | New versioned generator, source manifest and replay audit |
| I06 | P1 open | No actual selected-window bank and 20×87 replay-bound schedule | Immutable selected IDs, balanced batches, masks and terminal rules verified before fitting |
| I07 | P1 contract conflict | Synthetic auditor rejects every canonical duplicate window; production proposal would retain distinct source rows | One adopted source/content identity policy with explicit weights |
| I08 | P1 split feasibility | Strict cross-split state isolation includes shared starts/prefixes; ordinary episodes from the same initial board collide | Declare separate shared-opening and genuinely disjoint-position tracks; measure retained yield |
| I09 | P1 open | Receipt-bound helper is not the exclusive model entry point; source receipts are not full corpus authentication | Trainer uses one validated loading/scheduling path; corruption/replay fixtures |
| I10 | P1 design | Policy-mixture outcome values differ from worst-case values used to motivate max/min decisions | Keep estimands explicit; diagnose value-target mismatch using exact-state and reference substitutions |
| I11 | P1 scientific | Recorded trajectories need not cover counterfactual or critical replies searched at test time | Support audit by state-action, action ID, ply, role and criticality |
| I12 | P1 compute | Six-arm ≤5% FLOP condition unpassed; source accounting/runtime kernels incomplete | Versioned cost design and measured complete workload under its declared convention |
| I13 | P1 scope | Large part of current work concerns LAPACK, binary identity and supervision rather than new scientific evidence | A bounded research path with advanced attestation as an optional systems workstream |
| I14 | P1 reference | Full exact-root values failed larger-board feasibility; fixed-H and interval references are different objects | Tractable solved subset plus separately named fixed-H reference, with completed action tables |
| I15 | P1 statistics | Root population, occupancy weighting, repeated-state sampling and yield stops remain proposals | Freeze estimand, sample units, failure treatment and resampling before outcomes |
| I16 | P1 inference | No completed fresh locked study; historical adaptation prevents retrospective confirmation | Fresh locked roots/data with no outcome-dependent retuning |
| I17 | P2 confirmed limit | Rule-only Reversi8 failed old 2-second p90; V02 had 12 cells >2 seconds | Measured new common budget on the actual implementation; timeout outcomes retained |
| I18 | P2 open | V02 raw-state proxy differs from adopted `F→D→E`; random weights alter pruning | Actual-graph runtime measurement and fitted runtime disclosure |
| I19 | P2 open | V03 pilot, request adapter and external supervisor lack complete live integration/failure evidence | Minimal reliable worker/time limit first; fuller fault suite only if operational claim requires it |
| I20 | P2 open | Sampled RSS is not hard containment; same-cgroup observer may die; request byte cap does not bound waiting for EOF | External deadline/worker lifecycle, appropriate OS limit and clear receipts |
| I21 | P2 open | File/package hashes do not attest all executed interpreter/native bytes | Ordinary reproducible environment manifests; stronger attestation only for stronger claims |
| I22 | P1 reproducibility | Clone lacks raw historical datasets, fitted checkpoints and match traces | Recover original hashes or mark unavailable; publish a new reproducible artifact plan |
| I23 | P2 test gap | Passing source/accounting tests missed a real objective defect; broad suite is not clean on Linux | Numerical mathematical tests and portable/optional test tiers |
| I24 | P2 documentation | README has stale “running/not yet run” V2.9 text; method ends with stale “no model code” statement | Single current-status page plus dated historical archive |
| I25 | P2 maintenance | 196 Markdown files, long repeated status trails, 339 Python files and a 356 KB GUI module increase navigation burden | Active module map, named experiment configs, one issue register; freeze historical code |
| I26 | P2 reproducibility | No CI workflow, top-level license or citation file; NumPy research lock also includes Qt | Portable core CI; explicit optional GUI dependencies and owner-selected license |
| I27 | P2 metrics | Raw latent MSE is scale-dependent; rank/collapse checks do not prove usefulness | Within-arm error, train-calibrated normalization, value/ranking/regret and intervention endpoints |
| I28 | P2 architecture | Small affine/tanh predictor, sparse data and fixed three-epoch budget may limit fit | Train-only learning/gradient sanity checks; bounded duration choice before final evaluation |
| I29 | P2 attribution | Direct-leaf receives a different latent path and H4-only leaf supervision; raw arm predicts known mask/descriptor coordinates | Explicitly report unequal paths/targets; identical-trunk value control for the JEPA effect |
| I30 | P2 legacy | Chess confirmation lacks independent full-history rule validation and current licensed/audited production artifacts | Keep outside the new paper; do not let it block the two-game study |

Additional legacy limitations remain: local NNUE/LeJEPA-style implementations are not automatically faithful reproductions of external engines/methods; no real current Stockfish strength claim is supported; endless arena rankings are exploratory; full-corpus memory/runtime and current native GUI behavior remain unverified. Conversely, the original junction `FileExistsError`, stale dataset counters, duplicate raw rows, cache-integrity and timing defects have documented recovery/hardening work. They should be reported as historical repaired findings, not fresh open bugs. The original production chess dataset was later intentionally removed.

Primary issue sources: [current method](../METHOD_SPEC_V212.md), [decision register](V212_PREFIT_ACTION_REGRET_DECISION_REGISTER_DRAFT_01.md), [generation compatibility](V212_GENERATION_PROTOCOL_COMPATIBILITY_AUDIT_01.md), [overlap policy](V212_DUPLICATE_AND_OVERLAP_POLICY_AUDIT_01.md), [counter audit](V212_FLOP_COUNTER_COVERAGE_AUDIT_DRAFT_01.md), [supervision audit](V212_SUPERVISION_ARCHITECTURE_AUDIT_01.md), [chess recovery](PIPELINE_RECOVERY_20260913.md), [chess hardening](MARS_HARDENING.md).

**6. Novelty: what is occupied, and what remains a candidate**

Your correction is scientifically appropriate: a paper can contribute a method of investigation, a benchmark, a theoretical characterization or a well-supported failure mechanism without winning a leaderboard. However, “JEPA sometimes loses” and “prediction error is not planning quality” are already occupied territory.

The current literature check on October 25 used original papers and author sources, extending the repository's earlier searches. It is a targeted novelty review, not proof that no overlapping work exists.

| Prior work | Relevant established territory | Required distinction for this project |
| --- | --- | --- |
| [MuZero](https://arxiv.org/abs/1911.08265), [SPR](https://arxiv.org/abs/2007.05929) | Learned latent planning in games; recurrent predictive representations | Do not claim those ideas as new |
| [Value Equivalence](https://proceedings.neurips.cc/paper/2020/hash/3bb585ea00014b0e3ebe4c6dd165a358-Abstract.html), [minimal value-equivalent models](https://proceedings.mlr.press/v232/alver23a.html) | Preserve decision-relevant quantities rather than every physical detail | A generic decision-preserving representation principle is not new |
| [AD-WM, September 24](https://arxiv.org/html/2609.30264v1) | Counterfactual action discrimination, action-recovery losses and planner-facing elite regret | Neither action sensitivity nor action-ranking diagnostics alone distinguishes us |
| [Counterfactual Action Evaluation, October 2](https://arxiv.org/html/2610.02860v1) | Exact-state forks separating physical, observation, representation and prediction effects | Our distinction must concern adversarial replies and actual decisions; merely adding forks is insufficient |
| [Dual-Frontier, September](https://arxiv.org/html/2609.26293v2) | Failure attribution through fixed-operator oracle interventions and decision-relevant reliability | Do not claim oracle substitution or model/agent decomposition itself as new |
| [One-Step Prediction Fidelity, October 14](https://arxiv.org/html/2610.19375v1) | Controlled JEPA prediction/planning dissociation and matched continued-training controls | A generic negative prediction-versus-planning result would overlap directly |
| [Supervise What Decides Success, October 1](https://arxiv.org/abs/2610.01224) | Auxiliary targets aligned with quantities determining task success | A generic decision-aware auxiliary loss is not sufficient novelty |

The repository also already identifies JEPA multi-step planning, value-aligned models, RePAIR, LAMIR and ConnectX as close context. Their complete feature crosswalk should be retained, but rebased to the new proposed question rather than continually expanded without a study.

**The recommended contribution candidate is an adversarial fork-intervention benchmark and analysis of critical-reply preservation.** It would jointly provide:

- Exact symbolic observations, removing visual ambiguity as an explanation.
- Complete legal own-action/opponent-reply forks on a declared tractable population.
- Common reference utilities across models, avoiding each model grading itself in its own latent metric.
- Separate tests of factual prediction, reply ranking, root decision regret and closed-loop behavior.
- Within-checkpoint interventions distinguishing learned-transition drift, exact-state value error and search truncation.
- Cost- and magnitude-matched critical/noncritical branch interventions, so a mechanistic claim is stronger than a cross-model correlation.
- A fresh locked evaluation across two games, with all negative and inconclusive outcomes retained.

The individual components have precedents. The proposed novelty is their tightly specified use to measure **which adversarial reply distinctions are necessary for preserving root decisions**, and to identify whether JEPA loses those distinctions differently from matched alternatives. This is a promising research direction, not an established “first.” A closest-work review must assess the exact operational definition and intervention before the main experiment.

An optional method extension is a fork-ranking/critical-reply auxiliary objective. It must compete against identical-label value-only ranking and an action-recovery control. If it simply spends more oracle labels or extra updates, it cannot support a JEPA-specific mechanism claim. Do not make this extension necessary to finish the first paper.

**7. The proposed scientific question and experiment**

Recommended main question:

> When a learned latent model is used inside exact-rule adversarial search, which errors erase the opponent's decisive replies, and how can we distinguish those errors from value-target mismatch and limited search?

The primary setting should be **same-size Connect Four 6×7 and Reversi6**. Use a prospectively defined tractable late-position population for terminal-solved references. A second, separately labeled fixed-horizon population can cover less terminal-adjacent decisions. Board-size transfer, a third game, large architectures, self-play RL and the chess GUI are optional later work.

For a two-ply fork, let `q_ref(s,a,b)` be utility for the root player after own action `a`, legal opponent reply `b`, and the pinned reference continuation. Define `Q_ref(s,a)=min_b q_ref(s,a,b)`. Terminal first actions bypass the reply set with exact utility. Pass is an ordinary legal transition; draws and ties have explicit sets. For an executed action `a_hat`, regret is `max_a Q_ref(s,a) − Q_ref(s,a_hat)`. With utility in [−1,1], regret lies in [0,2]. A finite-horizon reference gives finite-horizon regret; only terminal-complete search gives full-game regret.

Use the same roots, exact legal tree, action order and tie rule for paired interventions within each checkpoint:

| Intervention | Held fixed | What the comparison probes |
| --- | --- | --- |
| Natural latent rollout | Original checkpoint and planner | Actual deployed decision behavior |
| Exact-state re-encoding at a declared boundary | Same learned encoder/value head and complete tree | Sensitivity to replacing the predicted representation with its exact-state encoding |
| Reference-value substitution | Same root and search contract | Residual gap associated with the learned value/readout; privileged diagnostic only |
| Exact traversal versus capped search | Same checkpoint/leaf function | Search approximation and budget effects |
| Critical-reply repair versus matched noncritical repair | Same number of repaired entries, ply, root stratum, and predeclared error-size caliper | Whether the location of representation/value errors matters beyond their average magnitude |

Repairs that require an oracle are diagnostic upper bounds, not deployable improvements. Their effects can be signed, nonlinear and order-dependent; do not add them as independent causal percentages. Re-encoding changes the predictor/readout interface and by itself does not separate representation information loss from readout miscalibration. A train-only frozen probe is an optional follow-up, not a license to fit on evaluation labels.

Freeze criticality using reference utilities and a declared margin, without using which intervention improves the model. Match control branches by a deterministic rule. Report the unmatched fraction and analyze the qualified matched population as such; never silently discard difficult roots. Terminal-resolved roots remain reported separately because learned latents cannot improve decisions already determined by rules.

A useful intuition is a move with many favorable continuations and one losing refutation: averaging prediction error can make that model look accurate while max/min selects a losing move. This intuition is not itself a novel theorem. Likewise, the familiar 2ε regret bound from uniformly bounded action-value error is useful background, not a new contribution. The research burden is to establish when this mechanism occurs in actual models and whether the proposed measurements/interventions reveal something beyond existing work.

**8. Metrics and explicit completion standards**

The following are proposed engineering/precision targets to freeze after the feasibility stage. They are not already achieved results or guaranteed statistical power.

| Quantity | Definition/reporting rule | Completion criterion |
| --- | --- | --- |
| Objective correctness | Finite differences with frozen targets, active regularizers and mixed horizon masks | Per-tensor directional and sampled-coordinate checks satisfy `abs(error) ≤ 1e-7 + 1e-4*max(abs(analytic),abs(numeric))` on declared float64 fixtures |
| Rules/reference agreement | Legal sets, transition, terminal utility, color perspective, pass; independent solver on tractable roots | Zero unexplained mismatches in frozen fixtures and sampled replay; all benchmark actions have complete references |
| Data integrity | Episode/source IDs, target lineage, canonical overlap, masks and duplicates | 100% retained trajectories replay; zero prohibited split collisions; all exclusions counted |
| Decision regret | Common reference utility loss of the selected root action | Per-game and equal-game means/intervals; solved and fixed-H strata never pooled |
| Primary mechanism contrast | Within multi-step JEPA, regret after matched noncritical repair minus regret after critical-reply repair | Two game-specific estimates with simultaneous 95% intervals; positive, zero-compatible or negative all reportable |
| Reply preservation | Whether the model's minimizing reply belongs to the reference ε-worst-reply set; tie-aware | Report by role, depth, branch support and root margin; ε fixed before evaluation |
| Decision agreement | Selected action belongs to reference best-action set | Tie-aware frequency plus regret severity, not accuracy alone |
| Dynamics versus readout sensitivity | Paired regret changes under the fixed interventions | All preregistered contrasts reported, including worsening after a repair |
| Representation diagnostics | Within-arm latent error; train-calibrated normalized error; effective rank | No raw cross-arm MSE leaderboard; rank is not a utility certificate |
| Resources | Total fit time, analytical MACs, exact transitions, model calls, CPU/wall time, peak RSS | 100% runs accounted for; separate diagnostic and training cost; no hidden restarts |
| Precision | Interval half-width for the main regret contrast on [0,2] scale | Planning target ≤0.05 per game; if not attainable within fixed budget, report limited precision rather than keep sampling for significance |
| Reliability | Missing cells, invalid actions, timeout/forfeit and incomplete references | No silent replacement; prespecified conservative treatment and explicit denominators |
| Paper completeness | Methods, all planned cells, figures, limitations, related-work comparison, reproduction package | Completion independent of the sign of JEPA comparisons |

The mechanism contrast needs no “JEPA must win” gate. Non-JEPA intervention results explain whether the phenomenon is JEPA-specific or general. Declare cross-arm difference-in-differences secondary unless sample design can support them. Do not promote a favorable secondary endpoint after a null primary result.

Use paired comparisons and preserve dependence: model seeds are crossed with root/episode groups; roots from one episode or symmetry class are not IID observations. Analyze each of two training corpora separately and report replication direction rather than claiming population-level corpus uncertainty from only two corpora. A crossed cluster bootstrap can quantify root/seed variation, but its calibration must be checked on design-matched simulations. Freeze multiplicity for the two primary game contrasts; treat the many diagnostic plots as descriptive. A non-significant result is not equivalence. An equivalence claim requires a predeclared practical margin and an appropriate interval/test.

For orientation only, if paired regret differences had SD 0.5 and were independent, a 95% half-width of 0.05 would require about `(1.96*0.5/0.05)^2 ≈ 385` observations. Clustering can increase that requirement substantially. Neither 200 roots nor 10 seeds is automatically “enough”; measure variance/dependence on development data and fix the final sample once, before the locked evaluation.

**9. A finite roadmap to a completed manuscript**

Planning estimate: roughly 10–16 focused working weeks, possibly longer at part-time pace. This is a work estimate, not a deadline or acceptance forecast. Each milestone produces an artifact; do not create a new version merely to avoid reporting a failed hypothesis.

| Milestone | Work and deliverable | Exit rule / fallback |
| --- | --- | --- |
| M0 — 2–3 days | One-page contribution statement, current issue register, new protocol identifier, explicit separation from V2.12 superiority study | Exact novelty claim survives comparison with AD-WM, counterfactual JEPA audits, Dual-Frontier and value equivalence; otherwise revise once or choose a scoped empirical/benchmark paper |
| M1 — 3–7 days | Repair covariance derivative; broaden mathematical tests; portable NumPy-only environment and test tiers | Numerical tests pass; known artifact/OS skips explicit; no new model family needed |
| M2 — 1–2 weeks | Small benchmark feasibility build; independent rule/reference checks; duplicate/shared-opening policy; terminal and critical-reply strata | Model-blind eligibility fixed; complete references; useful nontrivial roots obtainable within cost. If not, shrink reference horizon/empties prospectively and rename the estimand |
| M3 — 1 week | One integrated trainer/evaluator path, finite schedule, Adam/EMA, atomic checkpoints, resumability and provenance | Tiny end-to-end fixture reproduces metrics/checkpoint state; fresh/resume agreement; altered inputs rejected; train-only fit sanity passes |
| M4 — 1–2 weeks | Bounded development run; choose duration from train/development only; measure inference/reference cost and variance | Freeze configurations, reference, strata, root count, failure policy and analysis before final scoring; no duration/weight fishing |
| M5 — 2–4 weeks | Frozen main panel and prescribed interventions; complete failures ledger | Every planned cell terminally resolved; no favorable-seed selection; storage/budget respected |
| M6 — 1–2 weeks | Locked root evaluation, second-corpus replication, small paired-match external-validity check | Report both games, all controls and uncertainty; retire unsupported claims |
| M7 — 1–2 weeks, writing starts at M0 | Final manuscript, generated tables/plots, artifact README and limitations; fresh reproduction by another person/environment if available | Every quantitative claim maps to a result row and code/config/data identity; manuscript complete regardless of JEPA ranking |

A concrete planning envelope is **five model families × 10 paired seeds × two independently generated training corpora = 100 fits**. The five are multi-step JEPA, one-step JEPA, value-only rollout, decoded-state dynamics and direct-leaf. Each fit is one shared two-game checkpoint; do not multiply by two games again. An initial budget estimate can use 4,096 selected windows per game/corpus and 200 fresh evaluation roots per game, with H4 restricted initially to a preselected 50-root subset per game. These are proposed starting sizes, to be replaced once by a model-blind cost and development-precision decision before the final protocol freezes. The new five-arm panel is not a completed or authorized rerun of the historical six-arm design.

The 100-fit count must include failed runs and bounded feasibility allowance in the compute ledger. Choose one train-duration policy in M4 and apply it consistently; fixed three epochs from an earlier method should not be inherited without a fit check. A training-quality failure is an engineering/modeling result to resolve before the locked study, not something to explain away afterward.

Use a small paired-match suite as external validity, not 16,000 games as the main route to an answer. For example, a planning allowance of 200 color-swapped pairs distributed across games, fixed opponents and all selected model seeds can check whether root-level findings survive play. It cannot establish Elo or broad strength. Final counts must follow measured runtime and the declared claim.

M5/M6 stop rules: stop an unsafe or corrupted run and retain its status; do not replace failed seeds invisibly. If the monthly budget is exhausted, pause the predeclared queue and preserve incomplete status, rather than analyzing only the favorable completed fraction. If reference yield or precision fails, deliver the bounded feasibility/limitations result and narrow the paper; do not change the scientific target after looking at final outcomes.

**10. What $50/month buys, and what it does not**

The present implementation is CPU NumPy with Python game-tree traversal. A CUDA GPU is not used by this code. These models have roughly 8.5k–18.4k parameters; a GPU port could be slower for tiny sequential calls. Existing V2.9 receipts report about 1,308 seconds of total fitting wall time across 60 historical fits on their old workload; that is context, not a forecast for a larger new dataset or deeper search. Exact-reference generation and search may dominate the new study.

Recommended monthly envelope:

| Allocation | Amount | Rule |
| --- | ---: | --- |
| Active computation | $35 | Rent only after a measured end-to-end throughput/$ comparison against local CPU |
| Storage and transfer | $10 | Check offer-specific costs; sync small immutable results/checkpoints |
| Contingency | $5 | Failed setup/interruption allowance, not an untracked hyperparameter sweep |

At hypothetical active rates of $0.20/$0.40/$0.60 per hour, $35 buys 175/87.5/58.3 active hours. These are budgeting scenarios, **not current Vast.ai offers**. Actual offers vary, and storage/bandwidth are separately charged. Vast's official billing documentation says stopping an online instance does not end storage charges. Preserve and verify outputs before deleting rented storage. [Vast.ai billing](https://github.com/vast-ai/docs/blob/main/guides/reference/billing.mdx)

Spend month one mainly on local correctness, benchmark design and a bounded setup/throughput probe (at most about $5–10 of the monthly envelope). Rent larger GPU time only if a PyTorch/JAX implementation shows useful end-to-end acceleration, including transfers and search. Such a port needs objective/gradient equivalence tests; it is not required for the first paper. Avoid large pretrained visual models and self-play scaling within this budget.

The unchanged V2.12 head-to-head design implies at least `20 seeds × 40 situations × 2 variants × 5 controls × 2 seat assignments = 16,000 games`. At 60 moves/game and five seconds/move, a conservative time envelope is about 1,333 hours; at an actual average 0.1 second/move it is about 26.7 hours. Neither is a measured forecast. This range illustrates why profiling actual complete games matters and why root/intervention evaluation is the more controllable primary study.

A compact study over three or four months has a total cash ceiling of $150–200 if every month's full budget is spent, but spending the allowance is not a milestone. Local compute may be sufficient. Human effort, experimental definition and reference quality are more likely bottlenecks than neural training capacity.

**11. Paper outline and outcome-independent success**

Working title: **Counterplay: Do Predictive Representations Preserve Critical Opponent Replies?**

The manuscript should contain: the adversarial decision problem and prior-work boundary; benchmark population and exact/reference semantics; the fork metrics and intervention design; matched model/training settings; primary mechanism results with uncertainty; representation/value/search attribution; resource accounting and limited match validation; limitations and reproduction instructions. Historical V1–V2.11 experiments belong in a concise motivation/appendix, not a stitched cross-version leaderboard.

Plan six principal figures/tables: (1) fork and intervention diagram, (2) benchmark/support/terminal coverage, (3) regret and reply-preservation by model, (4) paired intervention effects, (5) error-versus-regret stratified by margin/support/depth, and (6) cost/replication/limited-play checks. Generate tables from result files rather than manually copying numbers.

| Outcome | Legitimate paper conclusion |
| --- | --- |
| JEPA improves regret and preserves critical replies | Scoped positive evidence for the particular objective and population; compare against all declared controls |
| JEPA loses, and controlled repairs localize failures | A mechanism/benchmark contribution explaining the loss under declared conditions |
| All learned dynamics lose to exact-state re-encoding | Evidence about the value of learned transitions when exact rules are already available |
| Models are similar with narrow intervals | A bounded practical-equivalence result only if equivalence was preregistered |
| Models are similar with wide intervals | Inconclusive comparison; report limits without claiming equality |
| Proposed criticality diagnostic fails to predict/intervene usefully | Retain the negative validation of the diagnostic; narrow the contribution to what the study actually establishes |

A publishable novelty claim needs more than completed experiments: a clearly differentiated question/measurement and informative evidence or theory. If the diagnostic contributes no insight beyond existing work, completing a rigorous report is still possible, but a high-novelty methods paper is not justified. Decide that honestly at M0 and again after analysis. No roadmap can ensure acceptance, journal quartile or a novel empirical discovery.

**12. Name recommendation and immediate decisions**

**Recommended project name: Counterplay.** It fits opponent replies, counterfactual evaluation and multiple games without assuming a winning architecture. Suggested repository name if later adopted: `counterplay-lab`. Suggested descriptive subtitle: **Counterfactual Audits of Latent Planning in Adversarial Games**. This is a naming proposal, not a claim of trademark or repository-name uniqueness.

Alternatives: **CAISSA-Lab**, if retaining historical recognition matters; **ReplyScope**, for a narrower diagnostic toolkit. Avoid another JEPA acronym that commits the paper to proving the success of one objective.

Immediate order of work: repair and verify the gradient; agree a one-page new scientific question; move size transfer out of the primary claim; freeze a tractable fork/reference benchmark; build one minimal end-to-end trainer/evaluator; then run the bounded study. Defer detailed native-runtime attestation, exhaustive LAPACK accounting, the installer and full live-service failure certification unless the eventual paper makes claims that require them. Preserve ordinary reproducibility and resource safeguards.

**Appendix: reproducing the newly found gradient mismatch**

Run at the reviewed source commit in the pinned environment. This uses an existing synthetic unit-test fixture, changes only in-memory arrays, performs no optimizer update and writes no checkpoint. The tenfold input scaling makes the covariance derivative visible; it is not an experimental dataset.

```python
import importlib.util
import numpy as np
from two_player.v212_model import ARMS, V212Config, V212Model
spec = importlib.util.spec_from_file_location("fixture", "tests/test_v212_model.py")
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
for arm in ARMS:
    batch = fixture.synthetic_batch()
    batch["x"] *= 10
    model = V212Model(V212Config(arm=arm, seed=9))
    _, gradient = model.loss_grad(batch)
    z = model._encode(batch["x"])
    c = z - z.mean(axis=0, keepdims=True)
    covariance = c.T @ c / len(c)
    off = covariance - np.diag(np.diag(covariance))
    excess = batch["x"].T @ ((0.09 * 4 * c @ off / (len(c)*32)) * (1-z*z))
    index = np.unravel_index(np.argmax(np.abs(excess)), excess.shape)
    old = model.params["ew"][index]
    eps = 1e-6
    model.params["ew"][index] = old + eps
    plus = model.loss_grad(batch)[0]["loss"]
    model.params["ew"][index] = old - eps
    minus = model.loss_grad(batch)[0]["loss"]
    model.params["ew"][index] = old
    print(arm, index, gradient["ew"][index], (plus-minus)/(2*eps), excess[index])
```
