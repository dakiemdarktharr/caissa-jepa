# V2.12 root-sampling and inference design review 01

**Disposition: coherent proposal only as a versioned estimand/method change.
Not compatible with the currently reviewed v04, not a statistical calibration
result, and not authorization to generate roots, score models, simulate
coverage, fit, or run matches.** This static review compared `METHOD_SPEC_V212.md`
§§7–8 with the root-sampling amendment, design 02, and the inference audit on
2026-10-04. No simulations, roots, scores, or outcomes were produced or read.

## Findings

The first-valid-slot argument has no identified mathematical flaw under its
stated assumptions: slots are IID within variant × occupancy band; eligibility
uses only that slot's frozen rules and root criteria; and there is no adaptive
retry or rejection by board identity, prior slots, scores, or outcomes. Under
those assumptions, the first 16 valid receipts, conditional on at least 16
valid slots among the fixed 64, are IID draws from the slot-level
success-conditional distribution. Repeated boards therefore remain distinct
sampling units. Deterministic per-slot PRNG streams make the design reproducible
but only operationally approximate independent random draws.

The proposal changes v04 §7 in material ways. It replaces the broadly stated
reachable-situation target with first-passage roots conditional on reaching an
occupancy band after four legal plies; replaces situation IDs with candidate
slot IDs; introduces 16 slots per band and equal occupancy-band weights; and
changes the bootstrap to resample slots separately within variant × band.
The resulting target is neither uniform over reachable states nor over unique
boards, and equal occupancy-band weighting is not natural game occupancy
frequency. Describe it as an **equal occupancy-band mixture**, not an equal
phase mixture, unless cross-game phase comparability is separately justified.

The stratified crossed bootstrap preserves the proposed seed/root pairing,
seat assignments, and fixed weights. That structural alignment does not
establish finite-sample coverage, familywise error control, or calibration of
the max-|T| intervals and centered one-sided p-values with 20 seed clusters
and 16 slots per band. Ten thousand replicates address only Monte Carlo error
in the bootstrap approximation. The reviewed sources do not validate this
procedure for the proposed outcome distribution; Holm adjustment cannot
repair invalid input p-values.

## Decisions required in a v05 proposal

Before any root generation, a versioned method draft must explicitly replace
v04 §7 and freeze:

1. The success-conditional first-passage target; 16 candidate-slot observations
   per occupancy band; the meaning of the ≥40 independent-situation minimum
   when repeated states are separate slot draws; fixed equal occupancy-band
   weights and equal variant macro weights; policy-mixture and seat semantics;
   minimum ply, terminal and forced-pass rules; and whether any failed band
   invalidates the entire schedule without replacement or top-up. Current v05
   and Design02 both propose a global stop if any of the six variant × band
   strata under-yields; that is now editorially aligned but remains unaccepted.
   Reviewers must explicitly accept or revise the rule and decide whether a
   minimum probability of schedule completion is required.
2. The four pinned policies and all ordered-pair probabilities; rules,
   adapter, policy, configuration, and protocol fingerprints; PRNG algorithm
   and version; deterministic independent per-slot stream derivation; the
   exact 64-slot bound; accept-first-16-valid ordering; full rejection ledger;
   and pre-score freeze of the accepted schedule and seat assignments. Any
   adaptive retry or state-identity/outcome rejection invalidates the IID
   argument.
3. Whether a design-matched synthetic calibration is required. If required,
   freeze its data-generating scenarios and numerical acceptance tolerances
   before simulation, covering global and partial nulls, simultaneous
   interval coverage, seed/root effects and seed × root interactions,
   discrete/tied outcomes, slot-yield conditioning, cross-contrast dependence,
   power/width near the +0.05 nomination boundary, and Monte Carlo precision.
   State what failure means for the method or sample size. A/A-only checks are
   insufficient.
4. All 15 contrasts, pairing, bootstrap weights, familywise procedure, and
   fail-closed rules for root-yield failure, missing cells, zero bootstrap SD,
   or nonfinite replicates. Carry forward v04's non-confirmatory development
   status, fresh/disjoint locked-confirmation situations and seeds, and
   no-replacement/no-censoring loss treatment of timeouts and invalid moves.
   Review the exact implementation hash after these choices are frozen.

Until a qualified independent statistical review accepts the versioned
method and disposes the calibration question, v04 remains the current method
and no root or score may be produced under the draft proposal. The separate
v04 §8 novelty, trajectory/split, compute, and pre-fit gates remain unchanged.
Any new OOM fault injection remains subject to separate explicit
authorization.

## Sources reviewed

- `METHOD_SPEC_V212.md` §§7–8.
- `docs/METHOD_SPEC_V212_ROOT_SAMPLING_AMENDMENT_DRAFT_01.md`.
- `docs/V212_DEV_ROOT_SCHEDULE_DESIGN_02.md`.
- `docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md`.
- `docs/METHOD_SPEC_V212_SPLIT_AMENDMENT_DRAFT_V05.md`.
- `docs/V212_GENERATION_PROTOCOL_DESIGN_01.md`.
- `docs/V212_DUPLICATE_AND_OVERLAP_POLICY_AUDIT_01.md`.

## Follow-up editorial consistency review (2026-10-04)

A fresh read-only review by the configured independent reviewer found stale
references to the superseded Design01 root schedule, a generation-protocol
requirement for canonical window deduplication that conflicted with split
amendment v05's source-window sampling unit, and duplicate/overlap text that
still treated symmetry-unique roots as the current sampling unit. These
documents now point to Design02, preserve repeated root states as distinct
slot observations, and report canonical-equivalent fit-window content
diagnostically without dropping or upweighting it. The same pass found that
the global six-stratum under-yield proposal is already shared by current v05
and Design02; the review record's earlier statement that those drafts differed
is corrected.

This reconciliation is editorial only. The success-conditional target, the
interpretation of 48 slot observations as satisfying v04's 40-situation
minimum, the all-six yield rule and its acceptable pass probability, the
stratum-weighted bootstrap's finite-sample calibration, and whether a
design-matched calibration study is required all remain unaccepted. v04
remains current; no roots, simulations, scores, or outcomes were generated or
read, and no generation, scoring, fitting, or match gate advanced.

## Follow-up methods-literature assessment (2026-10-04)

Primary sources on crossed/pigeonhole bootstrap, multiway cluster inference,
few-cluster procedures, and resampling-based multiple testing were reviewed
and summarized in `docs/V212_ROOT_INFERENCE_LITERATURE_NOTE_01.md`. They
support the crossed-resampling analogy only under their own assumptions and
do not directly establish finite-sample coverage or strong familywise control
for the proposed bounded, discrete paired-score statistic, slot-yield
conditioning, 20-seed × 16-slot design, and 15-contrast gate. The research
recommendation is to require design-matched calibration before the draft
procedure supports nomination. This remains a recommendation, not independent
statistical acceptance. Before any simulation, a qualified reviewer must
freeze the scenario grid, tolerances, outer Monte Carlo precision, and failure
response. No roots, simulations, scores, outcomes, or training were produced
or read; v04 remains current.

The independent static reviewer requested and confirmed three refinements:
use the more direct Romano–Wolf step-down sources rather than a generalized
error-rate paper; preserve the algebraic macro-contrast relationship and
paired-seat/shared-arm dependence in any scenario generator; and report
six-stratum schedule-yield probability separately from coverage/FWER
conditional on schedule passage. It also requires explicit variance/covariance
patterns including heterogeneity. These refinements were added to the
literature note. The reviewer agrees calibration is a prudent recommendation,
not a requirement established by theory, and that any calibration conclusion
is limited to its frozen scenarios. This static review is not statistical
acceptance; no gate advanced.

## Follow-up schedule-yield sensitivity (2026-10-07)

An exact Binomial-tail calculation now quantifies the design-02 global yield
gate under equal assumed per-slot validity and independent slots: for 64
candidates and 16 required in each of six strata, the all-six pass chance is
about 36.1% at `p=0.30`, 82.1% at `p=0.35`, and 97.6% at `p=0.40`. Equal
per-slot yields of approximately 0.366, 0.383, and 0.418 correspond to
illustrative global pass targets of 0.90, 0.95, and 0.99. These are analytic
sensitivity values, not observed yields or accepted reliability thresholds.
For unequal strata, the joint probability depends on all six yields; the
independence factorization also depends on the slot-stream assumptions. See
`V212_ROOT_SCHEDULE_YIELD_SENSITIVITY_DRAFT_01.md`. The yield gate, root
schedule, bootstrap calibration, and all downstream research gates remain
unapproved/closed; no roots or simulations were made.

## Follow-up calibration-prerequisite review (2026-10-07)

An approved independent read-only review found the first-16-valid-slot IID
argument mathematically coherent under its stated assumptions: IID candidate
slots within each variant × band, slot-local predeclared validity, identical
within-stratum generation, and no adaptive or identity/score/outcome-based
rejection. The proposed seed × slot bootstrap structurally preserves the
pairing and fixed weights, but neither that alignment nor 10,000 inner
replicates establishes finite-sample coverage or familywise error control.
The proposal remains a material change to v04, which stays current.

The reviewer recommends design-matched synthetic calibration before using the
bootstrap for nomination. This is a recommendation, not a theory-established
requirement or gate disposition. Before any calibration run, the unresolved
decisions must be frozen: the 48-slot versus ≥40-situation interpretation;
equal band and macro weighting; policy, seat, RNG, slot-bound, validity, and
global-yield semantics; any minimum six-stratum schedule-pass probability;
calibration method/comparators; coverage, FWER, power and interval-width
tolerances; outer replication and uncertainty reporting; inner bootstrap
count or precision rule; and failure consequences. The scenario grid must
preserve the 15-contrast family and macro-contrast identity, paired seats and
shared-arm dependence, and cover global/partial nulls, heterogeneous crossed
effects and covariance, bounded/tied outcomes, first-valid/yield conditioning,
near-boundary alternatives, and fail-closed cases. Schedule yield must be
reported separately from conditional inferential error rates.

These findings are a static review only. No method wording or gate changed;
no calibration simulation, root, score, or outcome was produced or accessed.
