# V2.12 root-sampling inference calibration protocol 03 — consolidated draft

**Status: unapproved protocol proposal.** This revision replaces the
contrast-level copula proposal in protocol draft 01 with a shared-arm,
seat-swapped match-score generator. It proposes finite synthetic calibration
for the v05 root-sampling and bootstrap draft, matching its abstract arm,
seed, slot, contrast, and seat-pairing layout. Its yield mechanism does not
model state- or prefix-level score associations in the actual first-passage
root distribution. It does not amend current METHOD SPEC v04, resolve any
root-sampling decision,
authorize a simulation, generate roots, expose scores/outcomes, or advance a
research gate. Independent statistical and method review must accept/revise
the generator and disposition the v05 estimand first. Calibration would
address only the frozen scenarios below; it would not prove general validity
or establish JEPA superiority. Drafts 01 and 02 and the separate stress notes are retained as design history.
This document consolidates their candidate cells and assumptions; it is not
accepted or executable.

## 1. Scope and locked analysis proposal

This protocol assesses the proposed inference rule in
`METHOD_SPEC_V212_V05_ROOT_SAMPLING_DRAFT.md`, conditional on a complete
schedule. Schedule-pass probability is a separate yield property and is not
counted as coverage or error control. Current v04 remains operative until the
versioned method amendment and all applicable reviews are accepted.

The analysis under assessment has ten atomic contrasts (five controls × two
variants) and five macro contrasts, each defined as the arithmetic mean of
the two corresponding variant contrasts. Within each variant, the estimate
is the fixed one-third mean of the three occupancy-band estimates. Each
seed/slot/arm comparison retains its paired two-seat average. The proposed
resampling draws one multiset of 20 seed IDs jointly across all arms,
variants, bands, and contrasts, then separately resamples 16 slot IDs within
each of six variant × band strata. It uses 10,000 replicates, bootstrap
standard deviation with `ddof=1`, the empirical 95th percentile of max-|T|
with linear interpolation, intervals `estimate ± q × SE`, centered one-sided
bootstrap p-values with the `+1` correction, and Holm step-down over all 15
tests. Holm ties are ordered by original contrast ID. Counts use `>=`.

For atomic or macro contrast `i`, the proposed centered one-sided bootstrap
value is `(1 + count(delta_i^b - delta_i >= delta_i)) / (B + 1)`; each
contrast's values are then adjusted by the ordinary Holm step-down rule over
the frozen 15 IDs. The frozen manifest must specify the max-|T| standardization
and behavior on tied statistics exactly.

These implementation details are a proposal to make the calibration
reproducible, not decisions already accepted by the method review. Before a
run, freeze the source revision, dependency lock, RNG algorithm/version,
bootstrap seed derivation, quantile convention, contrast order, and hashes of
the simulator and analysis implementation. Any change creates a new protocol
version and requires review before execution.

The proposed interpretation of “at least 40 independent situations” is 48
accepted slot draws per variant (16 per occupancy band); board duplicates
remain separate draws. This remains an open v05 method decision. The
calibration assumes that interpretation only to emulate the proposed sample
size; it cannot establish that the interpretation satisfies v04.

## 2. Shared-arm synthetic match-score generator proposal

Generate synthetic seat-swapped match results, not arbitrary contrast
vectors, game states, or project game outcomes. Each dataset contains two
candidate arms (`V1`, `V2`), five shared control arms (`C1`–`C5`), 20 paired
model-seed clusters, six variant × occupancy-band strata, 16 accepted root
slots per stratum, and two seat assignments for every candidate × control ×
seed × slot comparison. Create all 15 analysis contrasts from these shared
arm-level results; calculate the five macro contrasts as exact arithmetic
means of the ten atomic contrasts.

For each component, draw one jointly Gaussian zero-mean arm-effect vector in
the fixed order `(V1,V2,C1,C2,C3,C4,C5)`. Draw one standardized seed vector
per seed and reuse its latent draw in all six strata. P1–P4 apply the same
factor in every stratum. P5 applies a deterministic band-specific covariance
factor to that shared seed draw, as specified below; this induces the declared
cross-band seed covariance rather than independent seed effects by band.
Root-slot effects are drawn once per stratum × slot and reused across seeds,
both seat assignments, and all five control comparisons for that candidate
variant. Seed × slot arm effects and the ten-dimensional matchup interaction
vector are drawn once per seed × stratum × slot and reused for both seat
assignments. Root-slot and seed × slot effects are independent across the six
strata. Within one outer dataset, seed latents, root-slot, seed × slot,
matchup, and game-residual components are mutually independent, except for
the within-component shared-arm, seat-pair, and cross-band seed reuse
explicitly defined here. All random-effect components and outcome residuals
are independent across outer datasets.
Within a component, arm effects and matchup interactions follow the frozen
correlation matrices below. Matrices must be PSD and generated by a pinned
Cholesky/eigenfactor routine; invalid matrices fail before any simulation.

For candidate variant `v`, control `c`, seed `s`, stratum `g`, accepted slot
`j`, and seat assignment `e ∈ {-1,+1}`, form the latent candidate margin

```text
Z = eta[v,c,p,g]
  + (Seed[v,s] - Seed[c,s])
  + (Slot[v,g,j] - Slot[c,g,j])
  + (Interaction[v,g,s,j] - Interaction[c,g,s,j])
  + Matchup[v,c,g,s,j]
  + beta*e + Normal(0,1)
```

The random matchup term is common to both seat assignments. The fixed seat
advantage reverses sign when the candidate changes sides. With draw threshold
`tau`, record candidate score 1 when `Z > tau`, 0 when `Z < -tau`, and 0.5
otherwise; the control score is the complement. The seat-averaged paired
candidate-minus-control score is therefore in
`{-1,-0.5,0,0.5,1}`. Use `beta=0.15`. Conditional game residuals are independent across
matchups/seats given the shared arm and matchup effects.

The five predeclared profiles set latent *pair-margin* component variance
fractions `(seed, root-slot, seed×slot)` as follows: P1 seed-dominant
`(0.75,0.15,0.10)` with `tau=0.15`; P2 slot-dominant `(0.15,0.75,0.10)`
with `tau=0.25`; P3 balanced `(1/3,1/3,1/3)` with `tau=0.40`; P4
interaction-dominant `(0.10,0.10,0.80)` with `tau=0.75`; and P5
band- and arm-heteroskedastic stress with `tau=0.40`. P5's fractions by
occupancy band are low `(0.60,0.20,0.20)`, middle `(1/3,1/3,1/3)`, and high
`(0.20,0.60,0.20)`. P5 uses arm scale multipliers in fixed order
`(V1,V2,C1,C2,C3,C4,C5)=(1.50,1.25,0.75,0.75,0.75,0.75,0.75)` for every
seven-arm component. For each band and component, form covariance `k D R D`,
where `D` is the diagonal matrix of multipliers and `R` is the specified
equicorrelation matrix. Choose `k` so the average of the ten
candidate-minus-control margin variances equals the band's listed seed
fraction for seed effects, its listed root-slot fraction for root-slot
effects, and one half of its listed seed×slot fraction for arm interaction
effects. This yields unequal arm variances while retaining shared-arm
dependence. For P1–P4 all multipliers are one, so each pair's margin variance
equals its corresponding target fraction.

For P5's shared seed draw, let `Sigma_seed,g = k_g D R_seed D` be the
band-specific covariance after normalization and `L_g` its deterministic
Cholesky factor. Draw one `xi_s ~ Normal(0,I_7)` per seed and set
`Seed_g[:,s] = L_g xi_s` in each band. Therefore
`Cov(Seed_g[:,s],Seed_h[:,s]) = L_g L_h^T`, explicitly retaining the same
latent seed across bands while permitting the declared marginal variance
change. For P1–P4, use the same factor and realized seed vector in all bands.

Split each profile's seed×slot fraction equally between the seven-arm
interaction margin and the matchup vector. The ten-dimensional matchup
matrix has equicorrelation `-0.05`; its diagonal is half of the band-specific
seed×slot fraction. Add independent game residual variance 1. Seven-arm
correlation matrices use equicorrelation `0.35` for seed, `0.15` for
root-slot, and `-0.10` for seed×slot arm effects. These equicorrelation
matrices are positive definite at the specified dimensions. The manifest
must include exact serialized covariance matrices and pair-specific
variances.

For pair `(v,c)` in band `g`, let `V[v,c,g]` be the sum of the
candidate-minus-control variances of seed, root-slot, and seed×slot arm
effects plus matchup variance. The independent game residual adds variance
one, so define `sigma[v,c,g]=sqrt(1+V[v,c,g])`. For P1–P4, `V=1` and
`sigma=sqrt(2)`; P5 has pair- and band-specific `V`. For fixed `eta`, the
expected paired score difference is

```text
F(eta; tau,beta,sigma) = 0.5 * sum_{e in {-1,+1}} (
    1 - Phi((tau - eta - beta*e)/sigma)
      - Phi((-tau - eta - beta*e)/sigma)
)
```

For every scenario target and policy-pair stratum, solve `eta[v,c,p,g]` by
deterministic bisection so `F` equals the declared target. Freeze the
normal-CDF implementation, bracket, stopping rule, and absolute residual
tolerance `1e-10`; use the bracket
`[-8,+8]` and stop at residual `≤1e-10` or bracket width `≤1e-12`. A failed
or unattainable target invalidates the scenario specification. Targets are
constant across occupancy bands except for the explicit `A-HETERO` band
offsets below. The macro is always
derived from the atomic outcomes, never generated separately. This permits
the declared partial-null and macro-null mean patterns while preserving
shared arm effects and valid discrete match scores.

For the ordinary-yield scenarios, all 16 root-policy pairs have `q_p=0.40`
and the matchup target is constant across pairs. The exact policy identifiers
are `bounded-search`, `positional`, `tactical`, and `uniform` (the latter is
the code family called uniform-random in the method specification). An ordered
pair is `(plus-seat policy, minus-seat policy)`, with the first component
assigned to seat +1 in the score equation. Enumerate all 16 tuples in
lexicographic order on these exact identifiers. The low-yield group consists
of the first eight:

1. `(bounded-search, bounded-search)`
2. `(bounded-search, positional)`
3. `(bounded-search, tactical)`
4. `(bounded-search, uniform)`
5. `(positional, bounded-search)`
6. `(positional, positional)`
7. `(positional, tactical)`
8. `(positional, uniform)`

The high-yield group is the remaining eight, in order:
`(tactical,bounded-search)`, `(tactical,positional)`,
`(tactical,tactical)`, `(tactical,uniform)`, `(uniform,bounded-search)`,
`(uniform,positional)`, `(uniform,tactical)`, `(uniform,uniform)`.
For the two policy-dependent yield cells, low-yield pairs have `q_p=0.20`
and high-yield pairs `q_p=0.60`. Their pair-specific target mean is
`mu_p = target - 0.15` for low-yield pairs and `target + 0.05` for
high-yield pairs. Under uniform preselection pair probability, accepted
weights are 0.25 and 0.75, so the success-conditional weighted mean remains
exactly `target`. Solve the corresponding `eta` values separately. The exact
ordered tuples, not pair indexes alone, are normative for this proposal.

For each of the 64 frozen candidate slots per stratum, draw its ordered
policy pair IID uniformly from all 16 pairs, then draw validity
Bernoulli(`q_p`). Given its pair, validity is independent of arm/random
effects and score residuals; slot-validity draws are independent across all
six strata. Retain the first 16 valid slots in candidate-slot order. Generate
match results for those accepted slots and condition inference summaries on
all six strata passing. Compute/report the exact schedule-pass probability
separately; these assumptions are synthetic design choices, not evidence
about actual root yield.

This selection proxy varies validity probability only by ordered policy pair.
It does not model validity or accepted-slot composition associated with latent
root quality, prefix length/state, or score effects within a policy pair.
Consequently the yield stress tests a shifted success-conditional policy-pair
mix under its declared pair-specific score means; it does not reproduce the
actual policy-mixture first-passage state/score joint distribution. Before
simulation, reviewers must either accept this limited abstract target for the
intended error-calibration question or require additional dependence stresses
and a new reviewed version. Until that disposition, describe this as a
synthetic structural proxy, not a design-matched calibration.

The model is an abstract shared-arm ordinal outcome generator, not a game
simulator. It guarantees arm-level dependence, paired seat-swap structure,
and valid discrete scores while allowing non-transitive matchup means. It
does not model project policies, boards, state-specific play, or empirical
game outcomes. A calibration result remains limited to this frozen DGP.

## 3. Consolidated scenario inventory and target map

This draft contains 39 cells: 30 null and 9 alternatives. The table below is
the complete stable-ID inventory. `P1..P5` are defined in §2. For indexed
families, the target pattern is the exact indexed rule in the next paragraph;
there are no implicit crossed cells.

| ID | Count | Profile assignment | Population atomic means / yield-quality law |
| --- | ---: | --- | --- |
| `N-GLOBAL-01..05` | 5 | P1,P2,P3,P4,P5 in ID order | All ten atomic means 0; ordinary yield |
| `N-ATOMIC-01..10` | 10 | P1,P2,P3,P4,P5,P1,P2,P3,P4,P5 | Indexed atomic contrast exactly 0; other nine +0.075; ordinary yield |
| `N-MACRO-01..05` | 5 | P1,P2,P3,P4,P5 | For indexed control, V1 +0.10 and V2 −0.10; all other atomic means +0.075; ordinary yield |
| `N-CONTROL-01..05` | 5 | P1,P2,P3,P4,P5 | Both variants at indexed control 0; all other atomic means +0.075; ordinary yield |
| `A-BOUNDARY` | 1 | P1 | All atomic means +0.05; ordinary yield |
| `A-MODERATE` | 1 | P2 | All atomic means +0.075; ordinary yield |
| `A-LARGE` | 1 | P3 | All atomic means +0.10; ordinary yield |
| `A-HETERO` | 1 | P5 | Controls 01/03/05 have (V1,V2)=(+.10,+.05), controls 02/04 (+.05,+.10); add low/middle/high offsets (+.10,0,−.10) to each atomic mean; ordinary yield |
| `N-GLOBAL-YIELD` | 1 | P5 | All means 0; policy-pair yield q=.20/.60 and pair targets −.15/+.05 |
| `A-BOUNDARY-YIELD` | 1 | P1 | All means +.05; policy-pair yield q=.20/.60 and pair targets −.10/+.10 |
| `N-GLOBAL-ROOTQ-NEG` | 1 | P2 | All means 0; ordinary q=.40; root-quality slope gamma=−1 |
| `N-GLOBAL-ROOTQ-POS` | 1 | P2 | All means 0; ordinary q=.40; root-quality slope gamma=+1 |
| `A-BOUNDARY-ROOTQ-NEG` | 1 | P2 | All means +.05; ordinary q=.40; root-quality slope gamma=−1 |
| `A-BOUNDARY-ROOTQ-POS` | 1 | P2 | All means +.05; ordinary q=.40; root-quality slope gamma=+1 |
| `N-GLOBAL-YIELD-ROOTQ-NEG` | 1 | P2 | All means 0; pair-yield q=.20/.60, pair targets −.15/+.05; gamma=−1 |
| `N-GLOBAL-YIELD-ROOTQ-POS` | 1 | P2 | All means 0; pair-yield q=.20/.60, pair targets −.15/+.05; gamma=+1 |
| `A-BOUNDARY-YIELD-ROOTQ-NEG` | 1 | P2 | All means +.05; pair-yield q=.20/.60, pair targets −.10/+.10; gamma=−1 |
| `A-BOUNDARY-YIELD-ROOTQ-POS` | 1 | P2 | All means +.05; pair-yield q=.20/.60, pair targets −.10/+.10; gamma=+1 |

For `N-ATOMIC-kk`, use the kk-th member of this fixed order:
`(C01,V1),(C01,V2),(C02,V1),(C02,V2),...,(C05,V1),(C05,V2)`.
For `N-MACRO-kk` and `N-CONTROL-kk`, kk is control C01..C05. Every
scenario uses all 15 contrasts in §1; macro contrasts are exact averages of
their two atomic contrasts. The inventory has 25 base principal nulls and
four base alternatives, two pair-yield cells, four uniform-yield root-quality
cells, and four pair-yield × root-quality cells. Thus there are 30 nulls and
9 alternatives. The 39 simultaneous-coverage endpoints comprise one endpoint
per cell; the 30 strong-FWER endpoints comprise one per null cell; total
family size K=69.

The policy-yield groups and all eight exact tuples per group are fixed in §2.
For pair-yield-only cells, slot validity is Bernoulli(q_pair), independent of
score components given the pair. For root-quality-only cells, use q=.40 and
the quality-linked law below. For interaction cells, use q_pair=.20/.60 and
the group-specific intercept law below. All cells use 64 candidate slots,
retain first 16 valid in each of six variant × occupancy strata, and condition
inference on all six strata passing. Schedule passage remains a separate
reported quantity.

## 4. Root-quality and interaction extensions

For root-quality-only and interaction cells, draw one slot-level
`H ~ Normal(0,1)` and reuse it for every arm, seed, seat, and contrast on that
accepted slot. For each yield group with marginal target q (q=.40 for the
root-quality-only cells; q=.20 or .60 for interaction cells), and each
`gamma ∈ {−1,+1}`, solve `a[q,gamma]` so
`E[logistic(a + gamma*H)] = q`. Slot validity is Bernoulli with probability
`logistic(a + gamma*H)`. Use composite Simpson integration of the standard
normal density over [−10,+10], at 4,096 and 8,192 equal subintervals, and
bisection on [−8,+8], residual ≤1e−12. Require both orders to agree within
1e−10 for intercept, validity integral, selected-root first/second moments,
variance, conditional target outputs, and record both values and residuals.

For P2, reserve root-quality pair-margin variance `v_H=.375`, halve its
original root-slot covariance so residual root-slot pair variance is .375,
and use loadings `(0.5,0.5,−0.5,−0.5,−0.5,−0.5,−0.5)` in arm order
`(V1,V2,C1,C2,C3,C4,C5)`. Add `sqrt(.375)*loading[a]*H` to arm a. Thus
root-quality plus residual root-slot variance remains .75 per candidate–
control pair and P2 total latent pair-margin variance remains 1. For target
M and group offset d (low −.15, high +.05), solve eta under the selected-root
law so the conditional expected ordinal score is `M+d`:

```text
E[ F(eta + sqrt(.375)*H; tau=.25, beta=.15,
     sigma_rest=sqrt(1.625)) | valid, q, gamma ] = M+d
```

Here F is the seat-averaged ordinal expectation from §2. Root-quality-only
cells have one q=.40 group, no pair offsets, and target M. Interaction cells
have two yield groups with separate intercepts and etas. In all cases, the
conditional group means average to the declared global target using accepted
weights .25/.75 for pair-yield cells. These are abstract selection stresses;
they are not estimates of the actual first-passage root/state/score law.

The manifest needed before a future run must serialize every cell/contrast/
band/policy-pair target row, exact covariance/loadings, eta and residual,
intercepts and residuals, selected-root moments, quadrature convergence,
cut points, ordered policy tuples, and source/runtime hashes. A failed
numerical or covariance check invalidates the proposed cell; no silent
resolution increase is permitted.

## 5. Monte Carlo assurance and workload (proposal only)

The candidate endpoint family is K=69 (30 FWER and 39 coverage endpoints).
Use one-sided exact Clopper–Pearson bounds with Bonferroni alpha `.05/69`;
coverage and FWER indicators within a scenario may be dependent, so do not
assume endpoint independence. The existing deterministic assurance audit
for this family reports dependence-robust joint lower bounds:

| R | Lower bound | Status |
| ---: | ---: | --- |
| 18,000 | .751504 | fails proposed .80 target |
| 18,200 | .765070 | fails |
| 18,400 | .799061 | below .80 |
| 18,450 | .806789 | passes this grid point |
| 18,500 | .794551 | fails; discrete non-monotonicity |
| 18,600 | .810013 | passes this grid point |

These are deterministic binomial calculations, not simulated calibration.
An exhaustive integer scan over R=1..18,600 found 145 values meeting the
proposed 0.80 assurance target. The first within this searched range is
R=18,378, where the union lower bound is 0.8020521569 and the exact cutoff is
1,001; R=18,377 is 0.7822841053. The discrete cutoff then produces 0.8010068175
at R=18,379 and 0.7999565426 at R=18,380. A 60-digit Decimal check around the
first crossing agrees with the recurrence/log-PMF reference within the audit
tolerance. This establishes only the first crossing in the finite searched
range. No R, assurance target, or final precision rule is selected. A reviewer
must disposition the endpoint mapping and assurance target, select and justify
a replication rule, and review local feasibility before any calibration
simulation. At the first searched crossing, R=18,378 and B=10,000 imply
7.16742 billion inner bootstrap replicates, up to 107.5113 billion contrast
evaluations; this is not a local runtime or feasibility measurement.

## 6. Proposed reporting, decision, and failure rules

The v05 candidate rule and numeric limits remain proposals: under every null,
the simultaneous upper Monte Carlo endpoint for strong FWER must be ≤.06;
under every cell, the simultaneous lower endpoint for full-family 95%
coverage must be ≥.94. Report power/width at +.05, +.075, +.10, per-contrast
type-I rate, marginal coverage, sign error, and reject-any/all-positive
probabilities as descriptive unless separately frozen. Report schedule-pass
probability separately from conditional inference. Any nonfinite statistic,
zero bootstrap SE, implementation mismatch, or incomplete replication is
retained as an invalid event and fails this proposal; no drop, replacement,
contrast removal, or post-hoc threshold change.

If a criterion fails, stop nomination under this analysis and require a new
reviewed method version before downstream root generation/scoring. If all
criteria pass, conclusions remain limited to these frozen synthetic
scenarios and do not accept v05, the root schedule, the ≥40-situation
interpretation, a schedule reliability target, training, or JEPA superiority.

## 7. Required dispositions before any calibration run

Independent statistical and method reviewers must explicitly disposition:

1. The v05 estimand, ≥40-situation interpretation, 48 accepted roots, equal
   band/macro weights, seat pairing, first-16-valid rule, and six-stratum
   global stop.
2. Whether the shared-arm ordinal DGP and its covariance/profile assumptions
   address the intended calibration question.
3. Whether the 39-cell grid, exact policy-pair grouping, pair-yield offsets,
   root-quality variance split, gamma magnitudes, and interaction law are
   adequate or need revision; explicitly disposition the `N-MACRO` orientation
   (V1 +0.10, V2 −0.10).
4. The endpoint definitions, simultaneous limits, assurance target, whether
   and how to use the finite integer-R search result, exact replication count
   and inner B, and local feasibility.
5. Failure handling, schedule-passage reporting, numerical tolerances,
   quadrature, RNG/runtime/source pinning, and the complete executable
   manifest schema.

No dispositions are recorded here. This consolidation resolves only document
fragmentation and makes a candidate inventory explicit. It does not accept any
component, authorize simulations/root generation, access scores/outcomes, or
advance a gate. METHOD SPEC v04 remains current; all relevant gates remain
closed. Do not run the calibration unless every disposition and execution
prerequisite is independently accepted in a later version.

## 8. Deterministic audits already available (not acceptance)

The supporting deterministic audit tools are `tools/v212_calibration_profile_audit.py`,
`tools/v212_calibration_assurance.py`, `tools/v212_root_quality_calibration_audit.py`,
and `tools/v212_root_quality_yield_interaction_audit.py`. Their existing
focused tests and manifests support arithmetic/proposal consistency only.
For the interaction audit, the reviewed two-resolution check includes
selected-root variance and all target outputs (maximum difference `2.78e-17`).
The 69-endpoint assurance values above are discrete and non-monotone.
No random draws, simulation, roots, scores, outcomes, inference, or training
were generated or accessed for this consolidated draft.
