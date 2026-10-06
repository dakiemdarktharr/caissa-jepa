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

## Follow-up calibration protocol design review (2026-10-07)

An approved read-only review found the draft's scenario arithmetic and null
identities consistent: 23 null patterns, four alternatives, and two
policy-dependent yield stresses give 29 cells; macro contrasts remain exact
averages of the variant contrasts. The success-conditional policy-pair
weighting is correct when ordered pairs are drawn uniformly, validity is
Bernoulli by pair, and the stated independence assumptions hold. At the
provisional `R=6,000`, the workload is 1.74 billion bootstrap replicates
(about 26.1 billion contrast evaluations).

The review did not accept the protocol. Its main concern is that the
contrast-level copula does not enforce shared candidate/control-arm outcomes
or seat-swap mechanics; reviewers must accept it as a broad dependence stress
model with a justified covariance envelope or require a shared-arm generator.
The protocol also needed to state policy-pair/validity/outcome dependence,
cross-stratum assumptions, exact scenario/profile mappings and metric
definitions, and the multiplicity inventory for Monte Carlo endpoint
decisions. A follow-up correction clarified that scenario RNG streams are
independent, but FWER and coverage indicators within a null scenario share
datasets; therefore the joint-assurance claim uses a dependence-robust union
bound rather than assuming all 53 endpoints independent. Stable IDs were
added for both yield-stress cells.

An analytic binomial-tail calculation for the proposed one-sided
Bonferroni-Clopper–Pearson rule (`alpha=0.05/53`) gives individual pass
assurance 0.5854 at `R=6,000` and 0.9971 at `R=18,000` when each true rate is
at its boundary (FWER .05 or coverage .95). The dependence-robust union-bound
lower limit for all 53 endpoints at `R=18,000` is 0.8439. This is a
pre-simulation calculation only; independent statistical review must accept
the 80% target, endpoint definitions, and calculation, and local compute
feasibility is unmeasured. The copula/shared-arm choice remains unresolved.
No simulations, roots, scores, or outcomes were produced/accessed. v04
remains current and all gates remain closed.

A final read-only consistency pass confirmed the corrected endpoint counts,
stable yield-stress IDs, and dependence-robust assurance framing. It found no
new major inconsistency; the shared-arm-generator disposition remains open.
The protocol is still unapproved and no execution gate advanced.

## Follow-up shared-arm generator and profile review (2026-10-07)

An approved read-only reviewer found the replacement ordinal shared-arm
generator coherent under its stated assumptions. It checked seed/slot/arm
covariance normalization, the P5 `k D R D` variance scaling and
pair-specific `sigma`, the ordinal-score normal-CDF mean equation, seat-swap
averaging, policy-dependent yield weighting, and the null/alternative/cell
and workload arithmetic. The profile grid now covers seed-dominant,
slot-dominant, balanced, interaction-dominant, and band/arm-heteroskedastic
variance. P5's band-varying seed variance uses one standardized latent seed
vector transformed by band-specific factors, with induced cross-band
covariance `L_g L_h^T`. `A-HETERO` maps to P5; positive alternatives cover
P1/P2/P3/P5, while P4 is explicitly null-only in this finite grid. The DGP
now states mutual independence of seed latent, root-slot, seed×slot, matchup,
and game-residual components within a dataset except for the specified
shared/reused structure. The reviewer confirmed these corrections resolved
the profile/covariance findings and remaining wording/independence issues.

The scenario inventory is 25 principal nulls, four principal alternatives,
and two yield stresses (31 cells); the acceptance family is 26 null FWER plus
31 joint-coverage endpoints (`K=57`). At `R=18,000`, the recorded binomial
calculation uses `alpha=0.05/57`, cutoff 981, individual pass probability
`0.9970554080688392`, and union-bound lower limit `0.8321582599238337`; the
31-cell workload is 5.58 billion inner bootstrap replicates (up to 83.7
billion contrast evaluations). The reviewer checked endpoint/count and
workload arithmetic by inspection but did not independently recompute the
binomial tails. These are design calculations, not simulation findings.

This review does not accept the calibration protocol, decide that calibration
is required, resolve v05/v04 compatibility, establish local compute
feasibility, or open a gate. The grid remains finite and excludes P4
alternative coverage. No simulation, root, score, outcome, inference, or
training was performed or accessed; v04 remains current and downstream
activity remains closed.

## High-precision assurance reproduction (2026-10-07)

Added `tools/v212_calibration_assurance.py` to make the analytic K=57 outer
replication assurance reproducible without generating datasets. It compares
downward binomial recurrence, log-PMF summation, and 60-digit Decimal tails;
the latter uses integer `choose(n,k)` and verifies both sides of each
acceptance cutoff. It confirms the R=18,000 cutoff is 981, with boundary tail
at the cutoff `0.0008665164123315592`, next-count tail
`0.0009669245316312552`, individual pass assurance `0.9970554080891540`, and
dependence-robust lower bound `0.8321582610817799`. At R=6,000 the cutoff is
303 and individual assurance is `0.5854327569152956`, so the joint union
bound is uninformative. This corrected roughly 1e-11-scale rounding drift in
the preceding double-only report. The independent reviewer did not
recompute these tails; the script and output are an auditable local analytic
calculation, not independent statistical acceptance or a simulation. No
gate advanced.

## Follow-up calibration draft-02 scope review (2026-10-07)

An approved read-only `gpt-6-luna/high` reviewer inspected the current shared-
arm calibration DGP, its deterministic profile/target audit tools, root
schedule design 02, and the v05 root-sampling amendment. Static inspection
found the arm/seed/slot dependence, seat-swap complement, macro derivation,
covariance normalization, P5 cross-band seed construction, target mapping,
scenario inventory, endpoint counts, and workload arithmetic consistent
under the draft's assumptions. The reviewer did not independently recompute
binomial tails or run the audit tools.

The reviewer identified a material scope limit: slot validity depends on
policy-pair yield `q_p`, but conditional on the pair is independent of score
effects/residuals. The DGP therefore has no state/prefix-level score-yield
association or within-pair root-quality selection. It tests an abstract
success-conditional law, not the actual first-passage root-state/score joint
distribution. Before any simulation, independently accept this limited stress
model or require added dependence stresses and a newly reviewed version. The
48-slot interpretation, equal-band estimand, yield contract, calibration
requirement, tolerances, failure response, and root schedule remain unaccepted;
v04 remains current. No simulation, root, score, outcome, inference, or training
was run/accessed, and no gate advanced.

## Follow-up review: root-quality/yield stress addendum 01 (2026-10-07)

An approved read-only reviewer inspected the new, unapproved root-quality
stress addendum. The initial review requested two corrections: state the
root-factor independence assumptions needed by the conditional target
integral, and record the exact assurance-helper parameters because its
defaults describe the old 31-cell/57-endpoint family. Both corrections were
made; a follow-up confirmed that those findings are resolved. The reviewer
found the P2 variance split, conditional root-factor density/target equation,
four-cell and 63-endpoint counts, workload products, and helper calculation
consistent under the stated assumptions. This was static review and not
independent tail recomputation or protocol acceptance.

The addendum remains separate from draft 02 and unapproved. With 63 endpoints,
the deterministic assurance audit gives a dependence-robust union lower bound
of `0.7947410752547584564` at `R=18,000`, below the proposed 0.80 target; at
`R=18,200` it gives `0.8059483244733129964`, making 18,200 a candidate only
if reviewers retain that target and accept the endpoint family. The exact
helper command is in the addendum; output is at
`/tmp/caissa-v212-root-quality-assurance-audit.log`. No synthetic dataset,
root, score, or outcome was generated or accessed. No simulation, inference,
training, method freeze, or gate transition occurred; v04 remains current.
