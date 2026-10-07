# V2.12 training-schedule manifest validator — draft 01

**Status: structural software contract only.** `two_player/v212_schedule_manifest.py`
validates an already constructed in-memory manifest object. It does not select
windows, read or generate data, replay episodes, create a schedule, run a model,
profile compute, or authorize fitting. The accepted v06 specification and D03
preregistration are unchanged.

## Validated schedule structure

Schema `caissa.v212.training-schedule.v01` requires 20 ordered seed records;
each seed has a distinct integer initialization seed and exactly 87 chronologically
ordered updates. Update `u` must map to epoch `(u-1)//29` and batch `(u-1)%29`.
Each update carries exactly 64 ordered window IDs `[game, episode_id,
start_ply]`, with 32 identities from `connect4-gravity-6x7` and 32 from
`reversi6`. IDs cannot repeat within a batch. In each epoch the schedule must
cover 928 distinct IDs for each game; the same per-seed banks must recur in all
three epochs, though order may differ.

Every update declares D03 horizon counts for all six arms and horizons 1, 2,
and 4: `valid_nonterminal`, `terminal_masked`, `missing_or_truncated`, and
`invalid_transition`. Counts must be nonnegative and within their batch/horizon
bounds; every arm's counts must match because masks are derived from the shared
batch. The direct-leaf arm must have at least one valid nonterminal H4 leaf in
every update. The validator returns a canonical JSON SHA-256 over the declared
manifest and a summary of its structural coverage.

## What this does not verify

The digest covers the manifest fields and window IDs, not the underlying window
payloads or source episode bytes. The validator does not prove train-split
provenance, exact-rule replay, policy/generator identity, mask counts against
actual windows, or that the ordered windows were selected by the frozen
procedure. It also does not enforce use by a trainer; direct `loss_grad` calls
remain possible. Those requirements need payload/replay receipts and trainer
integration before this structure can be used as operational evidence.

Six tests exercise a fully sized synthetic 20×87 manifest and fail-closed
cases for missing/reordered updates, invalid seed roster, game imbalance,
duplicate IDs, the direct-leaf H4 rule, arm-mask mismatch, and a changed window
bank across epochs.
The fixtures are synthetic identifiers and declared counts, not research
windows or an empirical schedule. This validator does not clear the separate
data/preflight, replay, six-arm compute, runtime, or pre-fit gates; the ≤5%
compute result remains untested and unpassed.
