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

The [executed 21-run pilot](docs/TWO_PLAYER_PILOT_20260929.md) found no demonstrated
JEPA advantage: exact-state search hit a diagnostic ceiling; hybrid full JEPA
did not outperform direct or decoded controls. The next roadmap milestone is
benchmark redesign, not scaling this setup. See the
[working research note](docs/WORKING_PAPER.md) and
[independent review](docs/INDEPENDENT_REVIEW_20260929.md). Engineering verification:
87 unit tests, standalone core checks and 13 source-release smoke checks passed.

V2 is a separately frozen [recurrent reply-fork study](docs/METHOD_V2.md).
Its [prospective benchmark audit](docs/V2_SURVEY_RESULTS.md) passes for Connect4
4x5 and Reversi6, with independent bitboard labels and complete cross-split
context/target isolation. `two_player_v2/` uses a shared two-layer encoder and
recurrent dynamics with direct, value-dynamics, decoded, projected JEPA, raw JEPA
and no-response comparisons. This is development work; improvement is unproven.
The [36-run v2 grid](docs/V2_GRID01_RESULTS.md) completed without errors, but
JEPA did not beat the strongest tuned value-dynamics baseline (regret0.249145
versus0.247664). Development continues; selection/final predictions remain closed.
The [v2.1 amendment](docs/METHOD_V21.md) preserves that source and uses
`two_player_v21/` for coherent legal-symmetry augmentation and a finite auxiliary
weight grid. [Training-only diagnosis](docs/V2_GRID01_DIAGNOSIS.md) motivates the
change; it does not establish a positive outcome or a new objective.
Its [60-run result](docs/V21_GRID02_RESULTS.md) has a small raw-JEPA improvement
over value dynamics(0.004826 regret), but the interval crosses zero and the
predeclared promotion gates fail. [Independent review](docs/V21_INDEPENDENT_RESULTS_REVIEW.md)
replayed every sampling/augmentation plan and verified saved decisions. The
next [v2.2 label-access study](docs/METHOD_V22.md) completed all 72 runs.
Its [results](docs/V22_GRID03_RESULTS.md) also fail promotion: scarce-label raw
JEPA regret 0.293339 versus direct 0.283917. The full-label sensitivity arm cannot
replace the predeclared primary arm. All three development grids are preserved.
The [Vietnamese professor brief](docs/PROFESSOR_BRIEF_V2.md) separates completed
evidence from the still-unproven model and publication claims.

The [18-run training diagnostic](docs/V23_FIT_DIAGNOSTIC.md) then found that
longer training and larger capacity help all tested families. Direct fits the
training labels better than raw JEPA; no new strength comparison was made.
All72 snapshots passed [independent audit](docs/V23_INDEPENDENT_RESULTS_REVIEW.md).
The [next fixed-target order probe](docs/METHOD_V24_ORDER_PROBE.md) tests a
specific restriction of additive action conditioning before another model grid.
It cannot promote a JEPA candidate or establish novelty.

The [completed order probe](docs/V24_ORDER_RESULTS.md) failed its materiality
screen in every game/capacity group and passed independent artifact audit.
The [V2.5 method](docs/METHOD_V25.md) therefore tests a separate hypothesis:
complete-reply mean/max latent consistency, compared with strong recurrent
policy/value, scalar, decoded and gradient-allocation controls. Its42-cell
development design is frozen; implementation verification precedes training.
This is not a demonstrated model improvement or a novel-principle claim.

The first V2.5 attempt then stopped **inconclusive** at cell4 because its Windows
memory observer leaked retained ctypes types. Three cells completed; the failed
attempt and costs are preserved. A [prospective runtime repair](docs/V25_RUNTIME_AMENDMENT.md)
keeps all scientific settings and budgets unchanged and requires a fresh42-cell
attempt after verification. The [positioning note](docs/V25_RESEARCH_POSITIONING.md)
explains the intended contribution and its boundaries for professor discussion.

![V2.1 development means and uncertainty](docs/figures/v21-grid02.png)
![V2.2 restricted-label development](docs/figures/v22-grid03.png)
Read [adaptive research controls](docs/V2_RESEARCH_CONTROL.md) and the
[novelty-risk follow-up](docs/V2_FORK_GEOMETRY_NOVELTY.md) before interpreting it.

Use the verified CPython runtime (bare `python` may resolve to another Windows
installation). After the source/test gate passes, reproduce the new local study:

```powershell
$py='C:/Users/ANHKHOI/AppData/Local/Programs/Python/Python311/python.exe'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
& $py -B -m benchmarks.survey chess_data/my-v2-survey --expanded --reversi6
& $py -B -m two_player_v2.data chess_data/my-v2-survey chess_data/two-player-pilot-v12 chess_data/my-v2-forks
& $py -B -m two_player_v2.runtime chess_data/my-v2-forks chess_data/my-v2-grid
& $py -B -m two_player_v2.report chess_data/my-v2-grid chess_data/my-v2-report
# Separate adaptive follow-up, after its source/test gate:
& $py -B -m two_player_v21.runtime chess_data/my-v2-forks chess_data/my-v21-grid
& $py -B -m two_player_v21.report chess_data/my-v21-grid chess_data/my-v21-report
# Restricted-label study: trainer receives only three standalone exports.
& $py -B -m two_player_v22.data chess_data/my-v2-forks chess_data/my-v22-scarce --fraction 0.25
& $py -B -m two_player_v22.data chess_data/my-v2-forks chess_data/my-v22-full --fraction 1
& $py -B -m two_player_v22.data chess_data/my-v2-forks chess_data/my-v22-development --development
& $py -B -m two_player_v22.runtime chess_data/my-v22-scarce chess_data/my-v22-full chess_data/my-v22-development chess_data/my-v22-grid
& $py -B -m two_player_v22.report chess_data/my-v22-grid chess_data/my-v22-report
# Training-only diagnostics; V24 requires the exact independently audited V23 inputs.
& $py -B -m two_player_v23_diagnostic.runtime chess_data/v22-full-01 chess_data/my-v23-fit
& $py -B -m two_player_v23_diagnostic.report chess_data/my-v23-fit chess_data/my-v23-report
& $py -B -m two_player_v24_probe.runtime chess_data/v23-fit-01 chess_data/v22-full-01 chess_data/my-v24-order
# Same frozen study with the audited constant-memory monitor amendment:
& $py -B -m two_player_v25r.runtime chess_data/v22-full-01 chess_data/v22-development-01 chess_data/my-v25-grid
& $py -B -m two_player_v25r.report chess_data/my-v25-grid chess_data/my-v25-report
```

The V24 probe accepts the pinned audited V23 ledger, not an arbitrary rerun with
different checkpoint bytes. It performs no training or development evaluation.

The prior v1.2 dataset is required to audit its training-state exclusion; use
the original v1 generation command above with its frozen seed and parameters.
All output paths must be fresh. The finite grid is serial and bounded; no paid
compute is used. An interrupted attempt with unaccounted elapsed compute cannot
be silently resumed inside the same grid budget.

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
