# CAISSA-JEPA: two-player JEPA research

The active research program tests action-conditioned latent prediction in
alternating, deterministic, fully observed, zero-sum games. Read
[Ground Truth](GROUND_TRUTH.md), [roadmap](ROADMAP.md), [frozen method](METHOD_SPEC.md)
and its [amendments](docs/METHOD_AMENDMENTS.md) first. The primary-source
[related-work matrix](docs/RELATED_WORK.md) identifies substantial novelty risk,
including MuZero, SPR/EfficientZero and RePAIR. No planning advantage or Q1
publication readiness has been established.

`two_player/` is the GUI-independent, shared-weight tiny-game research pipeline:
tic-tac-toe, gravity connect-3 and 4x4 Reversi; a 3x4 connect-3 size combination
is held out. Scope is middle/late local-position diagnostics, not whole-game
strength or unseen-family transfer. Seven controls include latent JEPA, recurrent
H1 inference, no-response, no-variance, direct policy/value, decoded dynamics and
value-only dynamics. The original whole-game data audit failed and is preserved.

Use Python 3.11.9 and `requirements-research-lock.txt` for the verified environment.
The following creates fresh ignored directories; existing paths are refused:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python -B -m two_player.data chess_data/my-audit --games 200 --seed 1701 --scope middle-late
python -B -m two_player.train chess_data/my-audit chess_data/my-pilot
```

Training replays the data audit and rejects failure. Selection/final predictions
are excluded. Generated self-play is locally authorized project-owned data; its
public artifact license is unassigned, so datasets/checkpoints are not published.
See [source and license register](docs/DATA_SOURCES.md). No external corpus was
downloaded. The legacy chess confirmatory gate is unconditionally blocked pending
independent full-history rule validation; UCI evaluation is not such validation.

## Legacy MARS-JEPA Chess compatibility implementation

**MARS-JEPA: Multi-Horizon Action-Conditioned Response-Aware State Prediction for Resource-Bounded Zero-Sum Chess**

MARS-JEPA Chess is a CPU/NumPy research prototype for deterministic, two-player,
zero-sum chess. The falsifiable hypothesis is that action-conditioned,
opponent-response-aware H1/H2/H4 latent prediction improves resource-bounded
chess planning over matched H1, H1/H2, and no-response controls.

This hypothesis has not been established. Representation quality, supervised
policy/value quality, and complete search strength must be measured separately.
There is no generic two-player-game transfer claim, demonstrated superiority
over Stockfish, Q1-readiness claim, or acceptance-probability estimate.

The legacy chess production dataset was intentionally removed because its integrity and
split validity were not trusted. No production training or valid model-v-model
result was created by the research-hardening task. Old receipts describe
historical runs and do not authorize using old data or checkpoints.

## Implemented model roster

| Research alias | Stable compatibility ID | Model |
| --- | --- | --- |
| `h1` | `a-jepa-h1` | H1 action-conditioned EMA JEPA; no reply exists within H1 |
| `h1-h2` | `a-jepa-h1-h2` | H1/H2 response-aware EMA JEPA |
| `full` | `a-jepa-v7` | H1/H2/H4 response-aware EMA JEPA |
| `no-response` | `a-jepa-no-response` | Matched allocated JEPA capacity with reply conditioning removed |
| `lejepa-inspired` | `lejepa-sigreg` | Shared-encoder SIGReg adaptation; no theoretical reproduction claim |
| `direct-policy-value` | `policy-value-v1` | Non-JEPA policy/value control |
| `nnue-style` | `nnue-style-v1` | Local NumPy evaluator, not Stockfish NNUE |

`model_registry.py` provides the shared GUI/CLI registry, configuration,
parameter-count and fingerprint metadata. Active and allocated capacity differ
for horizon ablations; this must be disclosed when matching compute budgets.

## Running and verifying

The legacy launchers remain `run_caissa_app.ps1`, `run_caissa_jepa_v7.ps1`,
`train_caissa_v7.py` and the installed CAISSA-JEPA executable. Python imports,
installer IDs, checkpoint filenames and CAISSA-JEPA storage paths are retained
for compatibility. This is a research-name migration, not a storage migration.
Application UI text is English.

```powershell
python -B -m unittest discover -v
git diff --check
```

Training requires explicit fresh/resume selection and matching verified data.
GUI Fresh mode archives existing weights after dataset verification; CLI fresh mode requires an unused path unless `--archive-existing` is explicit. An existing checkpoint is preserved and marked incompatible/unverified when
its dataset fingerprint cannot be verified. The former dataset-change override
is rejected. The test suite and release self-test use explicitly marked,
test-created temporary fixtures; they produce no research evidence.

An explicit offline audit command is available for a future separately acquired,
licensed dataset. It does not download data:

```powershell
python -B tools/audit_pipeline_dataset.py DATASET --research --report AUDIT_PLAN.json
python -B train_caissa_v7.py --dataset DATASET --split-plan AUDIT_PLAN.json --model-id full --model NEW_CHECKPOINT.npz
```

Do not run these against the intentionally removed production dataset. Audit
failures must be addressed in a separate derived version, preserving provenance.
The audit records excluded games/positions, source hashes, license metadata,
complete FEN checks, deterministic event splits, and position-overlap removal.

See [research identity](docs/RESEARCH_IDENTITY.md),
[research protocol](V7_RESEARCH_PROTOCOL.md), and
[hardening limitations](docs/MARS_HARDENING.md).
