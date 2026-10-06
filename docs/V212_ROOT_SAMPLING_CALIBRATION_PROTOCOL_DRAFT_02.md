# V2.12 root-sampling inference calibration protocol 02 — draft

**Status: unapproved protocol proposal.** This revision replaces the
contrast-level copula proposal in protocol draft 01 with a shared-arm,
seat-swapped match-score generator. It proposes a finite, design-matched
synthetic calibration for the v05 root-sampling and bootstrap draft. It does
not amend current METHOD SPEC v04, resolve any root-sampling decision,
authorize a simulation, generate roots, expose scores/outcomes, or advance a
research gate. Independent statistical and method review must accept/revise
the generator and disposition the v05 estimand first. Calibration would
address only the frozen scenarios below; it would not prove general validity
or establish JEPA superiority. Draft 01 is retained as superseded design
history, not as the current calibration proposal.

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
and the matchup target is constant across pairs. For the two policy-dependent
yield stress cells, designate the first eight ordered policy pairs in
lexicographic policy-ID order as low-yield (`q_p=0.20`) and the remaining
eight as high-yield (`q_p=0.60`). Let the pair-specific target mean be
`mu_p = target - 0.15` for low-yield pairs and `target + 0.05` for
high-yield pairs. Under uniform preselection pair probability, the accepted
policy weights are 0.25 and 0.75, so the success-conditional weighted mean
remains exactly `target`. Solve the corresponding `eta` values separately.

For each of the 64 frozen candidate slots per stratum, draw its ordered
policy pair IID uniformly from all 16 pairs, then draw validity
Bernoulli(`q_p`). Given its pair, validity is independent of arm/random
effects and score residuals; slot-validity draws are independent across all
six strata. Retain the first 16 valid slots in candidate-slot order. Generate
match results for those accepted slots and condition inference summaries on
all six strata passing. Compute/report the exact schedule-pass probability
separately; these assumptions are synthetic design choices, not evidence
about actual root yield.

The model is an abstract shared-arm ordinal outcome generator, not a game
simulator. It guarantees arm-level dependence, paired seat-swap structure,
and valid discrete scores while allowing non-transitive matchup means. It
does not model project policies, boards, state-specific play, or empirical
game outcomes. A calibration result remains limited to this frozen DGP.

## 3. Proposed finite scenario grid

Use the same scenario definitions for every contrast family member. Name the
scenario IDs `N-GLOBAL-01..05`, `N-ATOMIC-01..10`, `N-MACRO-01..05`,
`N-CONTROL-01..05`, and `A-BOUNDARY`, `A-MODERATE`, `A-LARGE`, `A-HETERO`.
Use atomic contrast order `(control-01, variant-01)` through
`(control-05, variant-02)`; for `N-ATOMIC-kk`, the zero is the kk-th atomic
contrast in that order. For `A-HETERO`, controls 01/03/05 have variant base
means `(+0.10,+0.05)` and controls 02/04 have `(+0.05,+0.10)`; add band
offsets `(+0.10,0,-0.10)` for low/middle/high bands to each atomic mean.
Assign P1–P5 to `N-GLOBAL-01..05` in order. For every remaining principal ID
in stable listed order (`N-ATOMIC-01..10`, `N-MACRO-01..05`,
`N-CONTROL-01..05`, `A-BOUNDARY`, `A-MODERATE`, `A-LARGE`, `A-HETERO`),
cycle P1, P2, P3, P4, P5 and repeat, except assign `A-HETERO` to P5 so the
band/arm-heteroskedastic profile is assessed under a positive alternative.
`N-GLOBAL-YIELD` uses P5;
`A-BOUNDARY-YIELD` uses P1. The pre-run manifest must serialize the resulting
ID-to-profile mapping, numerical covariance/loadings, discrete cut points,
pair-specific variances, means, and solver residuals. Profile labels alone
are not executable scenario specifications.

The resulting principal mapping is explicit: `N-GLOBAL-01..05` map to
`P1,P2,P3,P4,P5`; `N-ATOMIC-01..10` map to
`P1,P2,P3,P4,P5,P1,P2,P3,P4,P5`; each of `N-MACRO-01..05` and
`N-CONTROL-01..05` maps to `P1,P2,P3,P4,P5`; and
`A-BOUNDARY`, `A-MODERATE`, `A-LARGE`, `A-HETERO` map to `P1,P2,P3,P5`.
The yield cells map as stated above.

The principal grid has 25 null scenarios and four alternatives, for 29
principal cells total. The five N-GLOBAL cells use all five profiles. Assign
the remaining patterns to profiles in the frozen round-robin order above, so
all profiles cover global and partial nulls and positive alternatives cover
P1, P2, P3, and P5. P4 is assessed under nulls only; this grid does not assess
alternative coverage under P4. The grid does not silently cross every profile
with every mean pattern.
The manifest must list each scenario's exact variance components, tie cut
points, loadings, means, and profile assignment before execution.

| ID family | Count | Population contrast pattern | Purpose |
| --- | ---: | --- | --- |
| N-GLOBAL | 5 | All ten atomic means zero; cover seed-dominant, slot-dominant, balanced, interaction-dominant, and band/arm-heteroskedastic profiles, including discrete ties | Global-null FWER and joint interval coverage across covariance/tie profiles |
| N-ATOMIC | 10 | One atomic contrast exactly zero; the other nine are +0.075; rotate over five controls × two variants | Partial-null strong-FWER behavior and coverage of true zero contrasts |
| N-MACRO | 5 | For one control, its two variant means are +0.10 and −0.10, so its macro mean is exactly zero; all other atomic means are +0.075 | Macro-only null coverage and familywise testing with exact contrast dependence |
| N-CONTROL | 5 | Both variant means are zero for one control; other controls’ atomic means are +0.075 | Correlated pair of atomic nulls plus their macro null |
| A-BOUNDARY | 1 | All atomic means +0.05 | Power and interval width at the proposed per-variant nomination boundary |
| A-MODERATE | 1 | All atomic means +0.075 | Power and interval width above the boundary |
| A-LARGE | 1 | All atomic means +0.10 | Power and interval width at a larger effect |
| A-HETERO | 1 | Variant means alternate +0.10 and +0.05 by control, with macro means computed exactly | Heterogeneous effects and unequal power across the family |

Thus all five profiles occur under null patterns, and the positive alternatives
include P1, P2, P3, and the P5 band/arm-heteroskedastic stress; P4's
interaction-dominant profile is assessed under null patterns only. The grid
includes low-, medium-, and high-draw regimes, seed- and slot-dominant
variance, band and arm heteroskedasticity, positive shared-arm and negative
matchup covariance. If reviewers require a full cross of all
mean patterns with all profiles, the cell count and compute budget must be
recalculated and reviewed before execution. Do not silently omit or add cells.

Use two yield mechanisms: (a) equal validity probability `q=0.40` for every
ordered policy-pair as the principal conditional-inference case; (b) a
policy-dependent stress with half of ordered pairs at `q=0.20` and half at
`q=0.60`. The second case has marginal validity 0.40 but shifts the
accepted policy mixture. For that stress, use pair-specific means and the
success-conditional target above. Add exactly two policy-dependent stress
cells, IDs `N-GLOBAL-YIELD` and `A-BOUNDARY-YIELD`, one global null and one
+0.05 boundary alternative with the same variance/tie profiles as their
principal counterparts. Thus the proposed total is 31 cells (29 principal
plus two yield-mixture stresses). Generate
the fixed 64 candidate slots per stratum, accept first 16 valid, and condition
inference summaries on all six strata passing; estimate/report schedule-pass
probability separately. Also report exact-binomial six-stratum yield
sensitivity at equal `q=0.30`, `0.35`, and `0.40`; these are analytic yield
calculations and require no synthetic inference run. The existing sensitivity
note reports approximately 0.361, 0.821, and 0.976 respectively under
independent slots and strata; those are hypothetical values, not observed
yields or an accepted minimum reliability threshold.

## 4. Replication and Monte Carlo precision proposal

Use `B=10,000` inner bootstrap replicates and independent outer RNG
substreams by stable scenario ID. Within each null scenario, the FWER and
coverage indicators come from the same datasets and may be dependent; do not
assume all 57 endpoint events are independent. With the proposed 57-endpoint
Bonferroni CP procedure, exact binomial calculation at the boundary rates
(FWER .05 and coverage .95) gives an individual endpoint pass probability
of 0.5854 at `R=6,000`; the dependence-robust union bound gives no useful
joint assurance there. At `R=18,000`, the individual pass probability is
0.9971 and the union-bound lower limit on all 57 endpoints passing is 0.8322.
Specifically, with `alpha=0.05/57 = 0.0008771929824561404`, the FWER
acceptance count is at most 981 because
`P[Binomial(18,000,0.06) ≤ 981] = 0.0008665164123139177 ≤ alpha`, while the
boundary pass probability is
`P[Binomial(18,000,0.05) ≤ 981] = 0.9970554080688392`. The lower union bound
is `1 − 57 × (1 − 0.9970554080688392) = 0.8321582599238337`.
The coverage condition is its binomial complement at 0.94/0.95. At `R=6,000`,
the corresponding FWER count is at most 303 because the tail is
`0.0008337079827290311 ≤ alpha`; its boundary pass probability is
`0.5854327569149984`. These are analytic binomial-tail calculations only.
Thus `R=18,000` is the proposal for at least 80% joint pass assurance at
boundary rates, without assuming endpoint independence. This is an analytic
binomial assurance calculation, not a simulation or empirical calibration;
the independent reviewer must accept the 80% target and calculation before
execution. If local resource preflight finds this workload infeasible, stop
and request a newly reviewed protocol. Do not choose `R` based on interim
calibration outcomes. No cloud, paid compute, or GPU is implied.

At proposed `R=18,000`, the workload is 5.58 billion inner bootstrap
replicates across all cells before accounting for each replicate's
15-contrast statistic (up to 83.7 billion contrast evaluations). This is an
explicit feasibility risk; a smaller run is not an acceptable substitute.

The acceptance inventory is 57 one-sided endpoints: the upper FWER endpoint
for each of 26 null scenarios and the lower full-family-coverage endpoint for
each of 31 scenarios. Use exact one-sided Clopper–Pearson bounds with
Bonferroni familywise alpha `0.05/57`; freeze and publish the endpoint list
and implementation hash. Require every relevant endpoint to meet the
proposed tolerance below. This inventory, not the descriptive diagnostics,
defines the acceptance family.

Also report per-contrast type-I rates for true nulls, marginal interval
coverage, power per positive contrast, probability of rejecting at least one
positive contrast, probability of rejecting every positive contrast,
median/95th-percentile interval width, and sign error (estimated contrast
nonpositive when the target is positive). Label these as descriptive
diagnostics unless a separately corrected acceptance family is frozen.
Report Monte Carlo intervals for them with their pointwise/simultaneous status
clearly identified. The assurance values above apply only at the declared
boundary rates and endpoint family; they do not predict actual calibration
or power.

The result is conditional on schedule passage for coverage/FWER. Report
schedule passage and its uncertainty in a separate table. Do not combine
yield failure with a false rejection or a coverage miss.

## 5. Proposed acceptance and failure rules

These numeric limits are review proposals, not accepted criteria:

1. In every null scenario, the upper endpoint of its simultaneous Monte Carlo
   interval for strong FWER must be at most 0.06.
2. In every null and alternative scenario, the lower endpoint of the
   simultaneous Monte Carlo interval for full-family 95% interval coverage
   must be at least 0.94.
3. Report power and width at +0.05, +0.075, and +0.10, but do not use an
   unreviewed minimum-power target to change the method. The +0.05 boundary
   power is descriptive of this finite design and may be low even if error
   calibration passes.
4. Any nonfinite statistic, zero bootstrap SE, implementation mismatch, or
   incomplete replication is recorded as an invalid-analysis event in its
   original dataset; do not drop or replace that dataset. Any such event
   means the method fails this calibration proposal unless a reviewed
   version defines a different estimand/procedure first. No contrast may be
   dropped and no threshold may be relaxed after results.

If any proposed calibration criterion fails, v05 cannot support nomination
under this analysis. Stop before any root generation/scoring under v05; a
revised inferential method, sample design, or explicit abandonment requires a
new version and independent review. If criteria pass, the conclusion is
limited to the declared synthetic scenarios and does not itself accept v05,
the root schedule, the ≥40-situation interpretation, a yield-reliability
threshold, or any downstream gate. Calibration does not authorize training,
scoring, inference, matches, or outcome access.

## 6. Decisions required before execution

The independent statistical reviewer and method reviewer must record an
explicit disposition on each item before any simulation:

1. Is synthetic calibration required, and is the shared-arm ordinal generator
   with its specified covariance structure adequately representative for the
   intended inference rule?
2. Are 48 accepted slot observations (16 per band) an acceptable
   interpretation of the ≥40 independent-situation minimum, with repeats
   retained as separate draws?
3. Are the equal occupancy-band weights, equal macro weights, seat pairing,
   first-16-valid rule, and six-stratum global under-yield stop acceptable?
4. Is a 0.95 global schedule-pass target required? If so, define the evidence
   and assumptions that can establish it before roots are generated. The
   `q` sensitivities here do not establish feasibility.
5. Are the 25 null patterns, four alternatives, five variance/tie/covariance
   profiles, band/arm heteroskedastic stress, and policy-dependent yield stress
   sufficient? Specify additions before execution.
6. Is `B=10,000`, `R=18,000`, and the dependence-robust 80% union-bound
   assurance proposal acceptable at the FWER .05/coverage .95 boundary? Is
   the analytic calculation correct for the frozen endpoint rule? Are the
   0.06/0.94 limits acceptable?
7. What is the disposition if precision, coverage, FWER, or power is
   inadequate? This draft proposes stopping nomination and requiring a
   separately reviewed method revision; it does not authorize post hoc
   changes.

No reviewer disposition or simulation is recorded in this draft. v04 remains
the current method; the v05 root-sampling design and every downstream gate
remain unaccepted/closed.
