# V2.12 generation receipt/auditor crosswalk — draft 01

**Status: design crosswalk only; not frozen and not an authorization.** This
document proposes how the future episode/window and held-out-root receipts
could bind to an audit without conflating source lineage with repeated
content. It does not amend METHOD_SPEC_V212-04, accept split amendment v05 or
root-schedule design 02, modify the existing in-memory auditor, create a
generator, generate episodes/roots, or open a training/scoring gate.

## Current-versus-proposed status

| Requirement | Current authority/evidence | Candidate disposition | State |
| --- | --- | --- | --- |
| Six arms, loss targets, masks, 928 windows/game, exact rules | `METHOD_SPEC_V212.md` v04 | Preserve unchanged | Current design; fit gate closed |
| Episode ownership and board-size split | v04 §§3/6 says train/development episode split; `METHOD_SPEC_V212_SPLIT_AMENDMENT_DRAFT_V05.md` proposes fit-only episodes on C4 6x7/Reversi6 and standalone held-out-size roots | Explicit matrix in v05 | Material method amendment; not accepted |
| 928-window identity and eligibility | v04 says 928 valid windows; v05 proposes `(rules/game identity, episode_id, start_ply)`, no replacement, and allows a terminal-only window with root supervision but no latent target | Carry both identity and per-horizon masks | Proposed; valid-window meaning not frozen |
| Repeated/canonical-equivalent content | Synthetic auditor rejects any duplicate canonical window; v05 says report repeated content diagnostically and do not silently drop/upweight | Keep source instances; report content multiplicities | Conflict; semantics need method acceptance |
| Held-out root sampling | v04 §7 says at least 40 independent reachable situations and an unstratified bootstrap; design 02 proposes 48 accepted slots/variant, three occupancy bands, fixed first-passage target and stratified bootstrap | Treat slot as draw; retain repeated boards | Substantive inferential amendment; not accepted/calibrated |
| Numeric episode quotas | v04 requires counts fixed from resource measurements; v05 requires quotas but does not give them | Set only after a no-outcome resource/yield basis is approved | Unresolved; cannot be inferred from the optimistic 23/15 episode lower bounds |
| Runtime/compute and data readiness | v04's fixed 2 s Reversi8 rule-only gate failed; pilot V03 remains a candidate, not cleared for runtime; no V2.12 trainer exists | Require separate runtime, data, supervision, and pre-fit gates | Closed |

## Proposed identity and lineage namespaces

Identity values below are design candidates. Exact field encodings, hash
domains, canonical serialization, transform registry, and manifest version
must be frozen before implementation.

| Record | Content identity | Separate lineage/provenance |
| --- | --- | --- |
| Episode | `episode_id` derived from the frozen protocol ID, exact game/rules identity, and episode slot | Game/rules digest; partition owner; master seed ID; episode RNG stream IDs; ordered seat-policy IDs/config/source digests; episode terminal outcome; complete initial-to-terminal state/action sequence |
| Source window | `(game/rules identity, episode_id, start_ply)`; this is the proposed “distinct window” unit | Parent episode ID, absolute start/end plies, selected/unselected disposition, and any selection-stream receipt |
| State occurrence | Key by namespace plus exact game/rules identity, board, and player to move | Episode/window/ply location; repeated occurrences remain separately countable |
| Role-normalized state | Candidate key applies the declared player-to-move sign normalization to board channels and role | Original absolute board/player and the named normalization version |
| Symmetry-normalized state | Candidate key is the minimum representation over a frozen, property-tested legal symmetry set after role normalization | Original orientation and transform ID; never replace raw identity |
| Horizon target | Source-window identity plus horizon and target kind (`latent`, `raw_feature`, `terminal_utility`) | Exact target state occurrence, transition path, and valid/terminal/unavailable disposition; rules/adapter fingerprint binds exact game targets |
| Development root slot | Candidate slot ID derived from frozen schedule ID, variant, occupancy band, and slot ordinal | Candidate slot seed streams, policy pair, prefix actions/length, accepted/rejected reason, exact root state, and both seat assignments |

An episode ID is not a state/content key. A source-window ID is not a
canonical-content key. Separate counts should show (a) source instances, (b)
raw-state multiplicities, (c) role-normalized multiplicities, (d)
symmetry-normalized multiplicities, and (e) cross-partition collisions by
key namespace. Same-content instances within a permitted partition are
retained unless a separately accepted method explicitly changes the sampling
unit. Any cross-partition collision in a key namespace declared fail-closed
is a failure, not a candidate for silent de-duplication.

The exact `episode_id` derivation, field encodings, hash domains, and
canonical serializer are placeholders in this crosswalk. V04/v05 require
reproducible IDs, seed mapping and hashes but do not specify the exact
derivation. The corpus stores exact target states and their masks; an EMA
target-encoder fingerprint belongs to the later training/checkpoint manifest,
because latent targets are computed during fitting rather than episode
generation. Episode outcome provenance is the absolute terminal winner/draw
returned by the adapter; side-to-move utility labels are derived per state
using that state's player and must not be confused with the absolute outcome.

## Proposed receipt layers

These are field groups, not frozen JSON schemas.

### Run manifest

- Schema and protocol candidate IDs; immutable status `training_approved: false`.
- Exact game/rules configurations and source digests; policy IDs, code/config
  digests, RNG algorithm/library versions, and legal-action/tie semantics.
- Variant-by-partition matrix, episode quotas and their approved resource
  basis, seed namespaces, ordered policy-pair draw rule, selection rule, and
  planned window counts.
- Code/runtime/dependency identity, serializer/hash-domain version, and the
  source IDs for the independent method, statistical, and implementation
  reviews required before generation.

### Episode and window ledger

- One episode record per immutable slot, including stream identities, rules
  fingerprint, ordered seat policies, exact legal replay through terminal,
  absolute terminal outcome, and validation disposition.
- One source-window record per potential action-start, with exact source ID,
  up-to-four-ply state/action lineage, H0–H4 state occurrences, and H1/H2/H4
  `valid`, `terminal`, or `unavailable` target masks.
- Selected 928-window IDs and the deterministic selection schedule, with no
  replacement; every omitted or quarantined episode/window retains a reason
  and denominator status. Terminal-only windows must not be silently confused
  with windows having a valid JEPA target.
- Content multiplicity summaries; the proposed policy is diagnostic reporting
  rather than rejection, but that policy remains unaccepted.

### Held-out root schedule ledger

- One row for every predeclared candidate slot, including rejected slots;
  slot ID, variant/rules identity, band, seed-stream identities, ordered
  policy pair, replayed prefix, occupancy and disposition reason.
- Accepted root receipt with exact board/player, policy provenance, paired
  seat assignments, and rules/adapter/protocol digests.
- Accepted/rejected slot counts and repeated raw/canonical state multiplicity
  by variant/band, retained without identity-based replacement.
- Design 02's first-passage target, 16-of-64 per band, global yield failure,
  equal-band weights, and bootstrap must remain labeled proposed until the
  method/statistical review accepts them.

### Audit/commit receipt

- Bind manifest digest, episode/window ledger digest, root-schedule digest,
  audit implementation digest, rules/policy digests, serializer version,
  candidate schedule counts, and all validation summaries.
- Record replay, legal-action, role/value, forced-pass, terminal/mask,
  window-count, key-overlap, duplicate-multiplicity, policy-support,
  root-yield, and resource dispositions with denominators and failure IDs.
- Use explicit states such as `staged`, `audit_failed`, and `audit_passed`; a
  partial artifact must never be presented as a committed corpus. Publish a
  success marker only after all files and hashes are durable. Preserve a
  failed audit receipt and failure ledger for diagnosis; do not set
  `training_approved` true as a side effect of successful generation/audit.
- Atomic directory/receipt mechanics, recovery behavior, exact schema, and
  allowed artifact retention still require an implementation review. This
  sketch authorizes no filesystem output.

## Existing auditor compatibility finding

`two_player/v212_trajectory_audit.py` is explicitly a pure in-memory synthetic
fixture. It replays complete episodes, emits H0–H4 states, records H1/H2/H4
valid/terminal/unavailable counts, and fails on cross-split raw/canonical state
keys. It is not a corpus receipt validator or generator.

The same module unconditionally raises `ValueError("duplicate canonical
window")` for repeated canonical windows, including within a split. That
conflicts with the v05 proposal to preserve distinct source-window instances
and report canonical-equivalent content diagnostically. The current key audit
also flattens keys for all available states in a window into one list, so it
does not emit per-horizon/context-versus-target overlap counts or lineage
links. Do not change these semantics in place: v05 and root design 02 are
unaccepted. Once the split, duplicate, and key-namespace policy is accepted,
create a separately versioned no-I/O auditor candidate and retain the current
fixture behavior/history.

## Fail-closed dependencies

1. Method review must accept/revise the v05 allocation, source-window unit,
   terminal-only eligibility, policy-mixture/RNG contract, overlap key
   namespaces, and repeated-content disposition against v04. Statistical
   review must separately accept/revise the root target, slot independence
   assumptions, schedule yield rule, fixed band weights, bootstrap, and
   calibration/failure criteria. No acceptable schedule-pass probability or
   finite-sample inference guarantee is currently established.
2. After those semantics are accepted, version the receipt/auditor schema and
   a no-I/O synthetic fixture candidate for independent review. The existing
   v01 auditor remains unchanged until then.
3. Numeric production episode quotas, artifact/storage bounds, and runtime
   headroom cannot be obtained from static source inspection or the optimistic
   23/15 episode lower bounds. They require a separate, bounded no-outcome
   feasibility protocol with its own temporary resource limits, independent
   review, explicit authorization, and a namespace excluded from production
   data. Any root-slot yield measurement likewise requires the root target and
   schedule to be reviewed first; it cannot be inferred from assumed per-slot
   rates or from the 64-slot proposal.
4. Use only accepted no-outcome measurements to fix quotas and production
   caps, then freeze the complete generation/root protocols before any
   production episodes, roots, or model outputs. Data audit, compute,
   supervision, and pre-fit gates remain separate; successful generation
   cannot set `training_approved` true.
5. Current fail-closed state:
   `generation_protocol_frozen=false`, `generator_implemented=false`,
   `roots_generated=false`, `training_approved=false`.

No episode, root, score, outcome, simulation, service, inference, or training
was run/accessed for this crosswalk; generation-policy implementations were
inspected statically but not executed.
