# Validation receipt — research upgrade

Date: 2026-09-05. Runtime: D:\chess_robot_app\.venv\Scripts\python.exe; Windows; PySide6 offscreen rendering; OPENBLAS_NUM_THREADS=1 during verification.

Verified commands:

- `run_caissa_jepa_v7.ps1 -Mode tests`: core assertion suite and 27 unit tests (5 dataset/v7, 2 GUI, 6 arena, 14 research-upgrade tests).
- `benchmark_training_runtime.py --games 16`: temporary sampled dataset and temporary models only; raw output in training-benchmark.json.
- `git diff --check`: no whitespace errors.

Coverage includes legal chess transitions and hashing, dataset resume/HTTP Range, train/checkpoint smoke paths, GUI-owned progress, three-JEPA/five-trainable roster, legal arena moves, color-paired schedules, replay state, exact SAN/PGN/FEN logging, independent reference score orientation, mate and NNUE sign regressions, cache reuse/invalid targets, weighted metrics, ETA calibration/completion, protocol timeout/cancel, UCI subprocess startup/analysis/shutdown, checkpoint-bound action metrics and repeated monitor/arena switching.

The live-series integration test advances four short two-ply games through real QThreads, checks paired seeds/colors and stops cleanly. These are censored smoke games, not strength measurements. The UCI process fixture is explicitly not a chess engine. Real Stockfish integration has not been run. Training and arena screenshots use synthetic progress/placeholder state, not trained-model performance. The two main views were rendered and visually inspected; a headless font-loading issue was corrected in the test harness. Screenshots are UI QA artifacts, not scientific figures.

Limits: no full-dataset epoch or 4-GB cache build, long-running five-model concurrency benchmark, full continuous tournament, real-runtime ETA forecast-error calibration, final-test leakage audit, complete gradient finite-difference audit, external Stockfish/Lc0 tournament, or native desktop mouse test. Test success is not a guarantee of all-feature or paper readiness.

Retirement: only caissa_a_jepa_h1_h2.npz, caissa_a_jepa_h1_h2.training.json, caissa_a_jepa_no_response.npz and caissa_a_jepa_no_response.training.json were moved into chess_data/retired_jepa_20260905. No dataset or retained-model checkpoint was deleted. They can be recovered from that directory.
