# CAISSA-JEPA v7 research protocol

CAISSA-JEPA v7 is a chess-focused adversarial JEPA experiment. It is not yet
evidence that JEPA improves chess planning. The protocol exists to make that
claim testable.

## Immutable legacy artifacts

Keep the v6 source, `chess_engine.db`, and `caissa_jepa.npz` unchanged. Train
v7 into a new path such as `chess_data/caissa_a_jepa_v7.npz`. Every experiment
records the FEN dataset manifest hash, model checkpoint, seed, split and
hyperparameters.

## Dataset

The dataset tool emits one JSONL row per game. Each position stores a complete
FEN, UCI action, opponent response, action sequence through four ply and an
outcome from the side-to-move perspective. A game enters the default dataset
when at least one player has PGN title `GM`; all plies are retained so the
model learns opponent behavior as well as GM moves.

Build from a local PGN/ZIP:

```powershell
python fen_dataset_tool.py ingest --input path\to\games.pgn --output fen_dataset
```

Run the resumable public TWIC source:

```powershell
python fen_dataset_tool.py crawl-twic --output fen_dataset --target-gb 4
python fen_dataset_tool.py verify --output fen_dataset
```

The crawler observes backoff, `Retry-After`, HTTP Range resumption and source
errors. It must not be configured to evade rate limits, logins, CAPTCHAs or
terms of service. TWIC material has source-specific redistribution terms; the
manifest records provenance, but publication still requires a license review.

## Model and accuracy changes

The v7 A-JEPA predicts:

```text
H1: state + our action -> next latent
H2: state + our action + opponent response -> future latent
H4: state + action sequence (self, opponent, self, opponent) -> future latent
```

It adds an exact-rule branch score: for each candidate action, enumerate legal
opponent replies and pool by worst predicted root-perspective value. This is
the initial minimax-aware baseline. It is compared against single-future and
direct policy/value baselines; it is not assumed superior.

Train with a game-level deterministic split:

```powershell
python train_caissa_v7.py --dataset fen_dataset --model chess_data\caissa_a_jepa_v7.npz --epochs 5
python train_caissa_v7.py --architecture policy-value --dataset fen_dataset --model chess_data\policy_value_baseline.npz --epochs 5
```

Để tiếp tục một checkpoint đã train dở, dùng `--resume` hoặc runner Windows:

```powershell
.\continue_caissa_training.ps1 -AdditionalEpochs 5
.\watch_caissa_training.ps1 -Follow -IntervalSeconds 10
```

Trainer lưu heartbeat nguyên tử vào file `.training.json` sau mỗi khoảng thời
gian cấu hình bằng `--progress-interval`. Checkpoint chỉ được thay thế nguyên
tử sau mỗi epoch và giữ cả optimizer state cùng EMA target state.

The trainer refuses to resume against a dataset with a different manifest hash
unless `--allow-dataset-change` is given explicitly. Its `.training.json`
report is part of the experiment artifact.

## Required benchmark sequence

1. Validate v6 alpha-beta, uniform MCTS, value-only MCTS and direct
   policy/value under equal time and node budgets.
2. Compare H1-only against H1+H2 and H1+H2+H4 with equal parameters/data.
3. Compare single future against response-conditioned worst-case pooling.
4. Run multiple seeds; keep validation tuning separate from final test games.
5. Report tactical solve rate, action ranking, calibration, nodes/time and
   Elo/SPRT. Loss alone is not a success metric.

Only after this sequence should v7 be used to make claims about adversarial
JEPA value for chess planning.
