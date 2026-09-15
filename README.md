# MARS-JEPA Chess

**MARS-JEPA: Multi-Horizon Action-Conditioned Response-Aware State Prediction for Resource-Bounded Zero-Sum Chess**

MARS-JEPA Chess is a CPU/NumPy research prototype for deterministic, two-player,
zero-sum chess. The falsifiable hypothesis is that action-conditioned,
opponent-response-aware H1/H2/H4 latent prediction improves resource-bounded
chess planning over matched H1, H1/H2, and no-response controls.

This hypothesis has not been established. Representation quality, supervised
policy/value quality, and complete search strength must be measured separately.
There is no generic two-player-game transfer claim, demonstrated superiority
over Stockfish, Q1-readiness claim, or acceptance-probability estimate.

The production dataset was intentionally removed because its integrity and
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
