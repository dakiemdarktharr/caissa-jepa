# CAISSA-JEPA: research decisions and implementation handoff

Date: 5 September 2026. Audience: project owner and future paper reviewers.
Scope: chess only; the current CPU/NumPy code, existing GM/FEN dataset, multi-model training and continuous arena. This is an engineering/research handoff, not evidence that the paper is ready for a Q1 journal.

## Decision

Keep exactly three JEPA choices in the training UI:

| UI name | What differs | Why retain it |
| --- | --- | --- |
| JEPA One-Step EMA | Predict the next-position representation; EMA target encoder; inference uses the trained one-step predictor and reverses next-player value | Small, interpretable predictive baseline |
| JEPA Multi-Horizon Response EMA | Predict 1/2/4-ply targets; condition on action/reply sequences; inference pools opponent replies using H2, while H4 is an auxiliary training objective | Main chess-specific hypothesis: explicit responses and longer-horizon training help planning |
| LeJEPA SIGReg No-EMA | Shared encoder receives gradients through both branches; sliced Gaussian regularization; no EMA teacher | A contrasting anti-collapse mechanism rather than another minor horizon variation |

This is a selection for **research value and controlled comparison**, not a claim that these are the three strongest chess JEPAs. There is no verified chess tournament evidence establishing that ranking. I-JEPA provides representation-prediction precedent; V-JEPA 2 supports investigating action-conditioned latent planning, but their visual/robotic results do not establish chess strength. [I-JEPA, Assran et al., 2023](https://arxiv.org/abs/2301.08243), [V-JEPA 2, Assran et al., 2025](https://arxiv.org/abs/2506.09985).

LeJEPA's published method removes EMA/stop-gradient dependencies using SIGReg. Our small NumPy adaptation now resamples directions per update and saves its seed. It still uses bounded tanh embeddings and a simplified quadrature, unlike a faithful reproduction of the paper's Gaussian assumptions. Therefore label it **LeJEPA-inspired chess adaptation**, not a validated reproduction of the authors' theoretical guarantees. A faithful unbounded/projection-head implementation and gradient checks remain a priority before publication. [LeJEPA, Balestriero and LeCun, November 2025](https://arxiv.org/abs/2511.08544), [authors' minimal implementation](https://github.com/galilai-group/lejepa/blob/main/MINIMAL.md).

The H1-H2-only and no-response choices are removed from the active GUI and training CLI. Their two checkpoints and two reports were moved into `chess_data/retired_jepa_20260905/`; they are recoverable. Low-level legacy loaders remain for compatibility. The retained checkpoints, GM dataset and non-JEPA models were not reset.

## Best non-JEPA directions for chess

**Stockfish 18 / NNUE + alpha-beta:** the strongest practical CPU reference family to prioritize. Its official January 2026 release describes SFNNv10 with threat features. The project reports +46 Elo over Stockfish 17 in its own tests; that is not an absolute universal rating and must not be transferred to this app. Our NNUE-style baseline is a small king-conditioned NumPy network, not Stockfish NNUE, not a Stockfish-compatible network loader, and not incremental Stockfish search. Keep it as a controlled local baseline. [Stockfish 18 release, 31 January 2026](https://stockfishchess.org/blog/2026/stockfish-18/).

**Lc0 / transformer policy-WDL + MCTS:** the priority GPU-oriented comparison family. The official recommended-net page lists BT4-it332 as a competition-strength option and documents its memory needs; choosing a net depends on available hardware. The existing Direct Policy / Value v1 is a small MLP-style baseline and must not be presented as an Lc0 implementation. Keep it, but a trained-from-scratch compact transformer under the same data/compute budget is a separate future experiment. [Lc0 recommended networks, updated November 2025](https://lczero.org/play/networks/bestnets/), [Lc0 WDL head](https://lczero.org/blog/2020/04/wdl-head/).

A further research baseline is supervised searchless transformer action-value prediction. It is informative for representation-versus-search ablations, not automatically a replacement for a strong search engine. Published ratings depend on opponent pools, inference policy and repetition handling. [Ruoss et al., Grandmaster-Level Chess Without Search, 2024](https://arxiv.org/abs/2402.04494).

No Stockfish/Lc0 binary, weights, GPU trainer, or third-party dataset has been downloaded or trained in this change. External pretrained engines belong in a separate reference track, not the same-data causal comparison.

## Training speed: implemented and measured

The main implemented change is a shared transactional SQLite sample cache. FEN parsing, legal alternatives and target-transition checks run at preparation, then compressed per-game records are reused across models/epochs. Only a committed COMPLETE cache is consumed. Concurrent trainers wait for its builder; cancellation rolls the build back. Games and positions are shuffled reproducibly for training; validation negatives remain seed-stable. Running metrics use bounded-memory sample-weighted accumulators.

The launcher now uses one BLAS thread by default to limit oversubscription when multiple small CPU models train together. Override with `-BlasThreads 2` or another measured value. This is a workload setting, not a promise that one thread is optimal on every computer. NumPy itself delegates relevant parallelism to its numerical backend. [NumPy global-state/threading documentation](https://numpy.org/doc/stable/reference/global_state.html).

Local microbenchmark: 16 source games, 1,459 train positions, 64-position batches, 96 latent dimensions, three cache/uncached passes, one BLAS thread. Median preparation was 2.789 seconds uncached versus 0.0458 seconds cached: about **60.9x faster for preparation only**, after a 1.936-second initial build. The cache occupied 303,104 bytes for this sample. Raw measurements and the reproducible script are in `docs/validation/training-benchmark.json` and `benchmark_training_runtime.py`. This is not an end-to-end training speedup, a full-dataset disk estimate, or a five-model concurrency benchmark.

Next speed experiments, in order:

1. Profile full-epoch wall time and memory with 1/2/5 simultaneous models; avoid competing with arena search.
2. Tune batch size and BLAS threads using positions/second plus validation quality, not utilization alone.
3. Remove unused H2/H4 forward preparation in the one-step implementation; use sparse active-row updates for the NNUE-style network rather than dense training features.
4. If profiling justifies a PyTorch port, benchmark data workers, pinned transfers, mixed precision and compilation. These do not accelerate the current NumPy implementation merely by installing CUDA. Check numerical quality before accepting a speed gain. [PyTorch performance tuning guide](https://docs.pytorch.org/tutorials/recipes/recipes/tuning_guide.html).

The first full cache build can take substantial time and disk space. The full 4-GB dataset was not prepared or trained during this handoff.

## ETA and training monitor

All five trainable models have separate plots on one English-language screen. Green is train loss; cyan is validation loss. The loss-components graph is no longer rendered. Bounded plot history is persisted in per-model training reports; old epoch reports provide a fallback on restart.

Progress uses actual valid batch counts across requested additional epochs. ETA starts CALIBRATING, becomes PROVISIONAL while validation speed is unknown, then uses separate observed train/validation rolling timings. Local estimated finish time and a timing-variability range are shown.

The range is a heuristic spread, **not a statistical confidence interval**. ETA cannot be exact under changing CPU load, thermal throttling, cache preparation, filesystem contention or future checkpoint-write overhead. Unmeasured cache build time is not silently counted as completed training. Full-run ETA forecast error has not yet been calibrated; log predicted-versus-actual finishes across several real runs before asserting an accuracy percentage.

## Accuracy: fixes now, experiments next

Implemented correctness fixes:

- Delivering checkmate receives positive root-perspective JEPA value.
- One-step JEPA no longer relies on an untrained H2 predictor.
- NNUE side-to-move scores are converted correctly to White perspective before alpha-beta negamax conversion.
- A-JEPA and direct policy/value reported total loss match the weights used by gradients. Train/validation A-JEPA horizon weights now agree.
- A sample with only one legal action no longer creates an impossible positive-versus-itself ranking penalty.
- LeJEPA resamples projection directions per update; its gradient is reused instead of recomputed.
- Seeds are saved for all baseline checkpoints. Resume protects the recorded seed and validation percentage.
- Cache preparation rejects non-finite outcomes, unknown game results and inconsistent legal target transitions.
- All-legal top-1/top-5, NLL, MRR and value MSE evaluation is saved with checkpoint/dataset fingerprints. Empty evaluation sets are marked unmeasured, not 0% accuracy.

**Margin ranking accuracy is not all-legal top-1 accuracy.** Matching a GM move is not equivalent to finding the strongest move; multiple moves can be equally good.

Priority experiments before a paper:

1. Freeze a new training protocol and train fresh checkpoints after correctness fixes. Old losses/objectives are not directly comparable; continuations are marked objective/runtime version 2.
2. Audit deduplication by canonical initial position + legal move sequence, not raw PGN formatting. Create locked train/validation/final-test splits at game/event level. Quantify shared positions separately, especially opening overlap; do not tune on the final test.
3. Test same-data/same-search JEPA versus direct policy/value first. Match parameter count and compute in separate analyses. NNUE + alpha-beta versus JEPA + MCTS is a whole-system comparison, not an isolated representation ablation.
4. Add strong-engine value/WDL teacher labels on a separate controlled track; preserve engine version, nodes/depth and uncertainty. Prefer all-legal policy cross-entropy or multiple hard legal negatives over treating one random negative as the complete policy problem.
5. Investigate side-to-move normalization and legal symmetry augmentation with correct castling, en-passant, action and value transforms. Add repetition/halfmove features in a versioned architecture.
6. Track representation collapse, latent effective rank, target error by horizon, calibration and tactical/endgame performance—not only training loss. Include several independent seeds and report dispersion. Leakage and experiment-design failures can dominate apparent model improvements. [Kapoor and Narayanan, leakage and reproducibility, 2022](https://arxiv.org/abs/2207.07048), [grouped cross-validation documentation](https://scikit-learn.org/stable/modules/cross_validation.html).

## Arena and a more defensible evaluation bar

The existing black/green arena and brown board remain. White's boxed nametag sits below the evaluation bar, Black's above. Clicks do not play moves. The monitor displays SAN, UCI, turn, last-move highlight, search time, nodes/NPS or MCTS simulations, available PV/root visits, referee score/WDL/depth, seed, match/round, score and uncertainty. Validation metrics appear only if a saved validation report matches the current checkpoint hash; otherwise they say not measured.

Every pair appears in a continuous paired round-robin: first color assignment is seeded/random, the next leg reverses colors using the same opening seed. A common opening-book prefix is used, and once book play ends it does not resume midgame. Start/continue blocks simultaneous GUI training. A changed model/book signature stops the series to avoid mixing experiments. Continue replays the last saved matchup, and exact replay identities are deduplicated for completed statistics.

JSONL stores UCI/SAN, FEN before/after each move, search and referee telemetry, model hashes, dataset fingerprints, trained steps and settings. PGN is also appended. Cancelled, errored and move-limit-truncated games are not counted as draws or valid wins. Snapshot restart is matchup replay, not exact in-search continuation.

For evaluation, both players use one independent referee whose score never feeds their move selection:

- Choose a trusted local Stockfish executable with **REFERENCE ENGINE...** in the arena. Alternatively use `CAISSA_REFERENCE_ENGINE`, or `chess_data/arena_reference.json` with an absolute `path`. Start a new series after changing the referee.
- The UCI adapter requests Threads=1, Hash=32 MB, UCI_ShowWDL and 150 ms per analysis, sending full start-position move history. It preserves White/Black orientation, mate scores and bound metadata and has bounded reads/shutdown.
- With WDL, White's bar height is **expected score W + D/2**, not win probability. Stockfish WDL is a model fitted to engine-game conditions and material; do not generalize it to human or arbitrary-engine outcome probabilities. [Stockfish WDL model](https://github.com/official-stockfish/WDL_model).
- Without a configured engine, the app explicitly displays an independent **Classical referee (uncalibrated)** score. Its compressed centipawn bar is visual only. Exact terminal results are computed from rules.
- Referee wall time is outside contestant search budgets. Small Python search-budget overruns remain possible; measured move time is logged.

Protocol tests use a deliberately labelled UCI stub. A real Stockfish installation, its WDL output and its runtime on this machine have **not** been verified here.

## Metrics and evidence required for the paper

Already recorded/displayed where measured: completed W/D/L, score (wins + half draws)/games, complete color pairs, context-specific relative Elo, paired score bounds, nodes/simulations, elapsed move time, FEN/SAN/PGN history, checkpoint/dataset identity and held-out action metrics.

The current score bound is a conservative fixed-sample Hoeffding bound over paired scores. It is exploratory, assumes appropriate independent sampling, and is **not sequential evidence** during unlimited live play. Do not stop when a desirable number appears and call that a confirmatory result. Choose a fixed game budget or preregister a suitable SPRT before formal engine claims. Pair-aware outcomes/pentanomial methods address the dependence introduced by color-swapped openings. [Fishtest mathematics](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html), [Fastchess manual](https://github.com/Disservin/fastchess/blob/master/man.md).

Still required: final-test isolation, multiple training seeds, fixed opening suite, parameter/FLOP and wall-clock budgets, confidence intervals for offline metrics, tactical/endgame strata, teacher-label provenance, hardware/power measurements where claimed, calibration/reliability diagrams and Brier/NLL for genuine probabilistic WDL heads. Accuracy and calibration are different properties. [Guo et al., On Calibration of Modern Neural Networks, 2017](https://arxiv.org/abs/1706.04599).

Q1 acceptance is not guaranteed by any model choice or arena win rate. The publishable contribution needs a falsifiable hypothesis, correct implementation, fair baselines, repeatable evidence, meaningful ablations and limitations.

## Run and verify

Open the app from PowerShell in the project folder:

```powershell
.\run_caissa_app.ps1
```

Use the Train Model dropdown to choose models. Train/stop/resume remains GUI-owned. Do not run separate training scripts against the same checkpoint simultaneously.

Run the local suite:

```powershell
.\run_caissa_jepa_v7.ps1 -Mode tests
```

Evaluation reports can be generated by `evaluate_action_ranking.py` for a specified checkpoint and validation split; the arena then displays matching results. This does not start training.

Verification scope: core rules/parser/database tests; dataset/download-range tests; all five model training smoke paths; GUI controller tests; paired schedule/replay/history tests; new ETA, scoring, caching, protocol and render tests. Monitor render images use explicitly synthetic progress, not project training results. No full-dataset epoch, sustained all-model tournament or real-Stockfish integration test was performed. See `docs/validation/VALIDATION.md` for the final test count and limitations.
