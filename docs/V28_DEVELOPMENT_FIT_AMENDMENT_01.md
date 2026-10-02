# V2.8 development-fit amendment 01

Date: 2026-10-02
Status: pre-outcome amendment; authorizes bounded development fits only.

## Reason for amendment

The original V02 plan made a full 9,600-block model-blind proxy run a
prerequisite for every fit. V03 stopped after 3,581 of 9,600 blocks; its
prefix is intact, but there is no terminal receipt and its cause is unknown
(see `V28_MODELBLIND_V03_INTERRUPTION_AUDIT_01.md`). More fundamentally, both
seats in that pilot use the same bounded-search proxy. It cannot estimate the
learned JEPA-versus-control treatment contrast or its sampling variance. A
full run would consume substantial local compute without unlocking the
question this project must answer.

No learned-model outcome has been viewed. This amendment changes only the
development-fit gate. It does not change the V02 objective, data labels,
primary endpoint, comparison arms, locked schedule, or confirmatory analysis.

## Development-only fit authorization

The DEV09 synthetic-data audit passed its frozen rules, provenance,
component-isolation, regeneration, and per-game/split support checks. For
development, an explicitly fingerprinted approval record may authorize reads
of `train` only while the source manifest keeps `training_approved: false`.
The production trainer must continue to require the original explicit
production approval. A development checkpoint and receipt must carry a
`development-only` scope and the approval-record hash; locked evaluation must
reject that scope.

The first development panel will compare `reply-jepa`, `task-value-dynamics`,
and `direct-leaf` on the identical DEV09 train roots, using the same
initialization seeds, optimizer schedule, epoch count, latent size, batches,
and model/search budgets. Training uses only the train split. Validation may
be used for diagnostics and the distinct positional-policy selection split
may be used for model selection. Neither split may be merged into training,
and no locked-final split or V08 block outcome may be opened. Every fit and
selection attempt, including failures, remains in the run ledger.

The first run is pinned in
`docs/validation/V28_DEV_FIT_PANEL_V01.json`: all 20 V08 checkpoint seeds,
the three variants, latent width 32, learning rate 0.001, EMA 0.99, batch size
64, the stated collapse/JEPA weights, one epoch, and shuffle seed 701. Its
disjoint 160-block development schedule uses two match seeds per checkpoint
and exists only for feasibility/model-selection direction; it is not powered
confirmatory evidence. The approval JSON binds the exact DEV09 manifest, both
data artifacts, normalized amendment hash, and the exact panel-specification
hash. It contains `scope: development-only`, `fit_split: train`,
`evaluation_splits: [validation, selection]`, and
`training_approved_manifest: false`. Every checkpoint receipt records the
approval-file hash and path; the matcher rechecks its bytes before evaluation.

The first panel is feasibility/development evidence, not a claim. Run the
development-only schedule (disjoint from V08) only after all 20 seed panels
are complete and resource/runtime checks pass. Report each game and control
contrast, color-swapped block count, model-forfeit/censor count, cluster-aware
uncertainty by training seed and match seed, and measured train/inference
compute. Lower latent prediction error alone does not pass.

## Locked-confirmation gates retained

The V08 schedule remains unopened. No development result can support
superiority, general transfer, equilibrium, exploitability, novelty, or Q1
readiness. Before confirmation, freeze the best recipe using development and
selection only; independently review the full candidate, code, data and
fairness; verify the exact V08 commitment and measured per-move budget; and
predeclare the primary effect, multiplicity, practical margin, confidence
interval, censor policy and stopping rule. The candidate must beat **both**
primary non-JEPA controls by the frozen meaningful margin at equal measured
compute. If not, retain the negative result and revise only in a new
pre-outcome development/confirmation version.

This amendment is a workflow correction made before any learned result. It
does not loosen the data audit, create a model result, or establish that the
method is novel or publishable.

## Protocol hardening before fit

Before the first fit, the grant was further bound to the exact DEV09 manifest,
source, trajectory, record, dataset, and canonical audit hashes. The loader
accepts only `chess_data/v28_data_dev09`. The fit and match runners validate all
frozen panel fields, including the complete development schedule hash,
development data identity, one-epoch run configuration, and comparison/color
design. The development evaluator refuses another balanced schedule or a
different inference budget; every entry point also requires a completed
`panel.json` ledger with 60 unique checkpoint/receipt hashes before matching.
The existing V01 approval artifact is stale after
these source/specification changes and must be preserved unchanged; a fresh,
uniquely named grant is required.

The fit runner records ordinary exceptions and completed checkpoint receipts,
but does not resume a panel after a hard process/host interruption. Its output
root is immutable and a retry must use a fresh unique root. Preserve any partial
root as an attempted run; a stale `running` row is not evidence of a completed
fit. This is an explicit recovery limitation, not a claim that hard
interruptions are automatically reconciled.
