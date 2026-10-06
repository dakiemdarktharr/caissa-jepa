# V2.12 calibration root-quality/yield stress — design 01 draft

**Status: unreviewed proposal only.** This addendum responds to the scope gap
identified in calibration draft 02: policy-pair-only validity does not model
selection of root states whose latent quality is associated with scores. It
does not revise draft 02, accept v05, authorize any simulation or root
generation, or open a research gate. The stress below is a synthetic
root-factor sensitivity, not a game-state generator and not a claim that
real first-passage roots follow this distribution. Independent statistical
and method review must decide whether to adopt, revise, or reject it and
whether additional interactions are needed.

## Proposed paired stress cells

Add four cells to the draft-02 grid, all using profile P2, its `tau=0.25`
ordinal outcome rule, and the ordinary marginal slot-validity rate `q=0.40`
for every ordered policy pair:

| Proposed ID | Atomic target means | Root-quality/yield association |
| --- | --- | --- |
| `N-GLOBAL-ROOTQ-POS` | all ten means 0 | `gamma=+1.0` |
| `N-GLOBAL-ROOTQ-NEG` | all ten means 0 | `gamma=-1.0` |
| `A-BOUNDARY-ROOTQ-POS` | all ten means +0.05 | `gamma=+1.0` |
| `A-BOUNDARY-ROOTQ-NEG` | all ten means +0.05 | `gamma=-1.0` |

The two signs check whether success selection favors roots with higher or lower
candidate-versus-control latent margins. P2 is chosen because it gives the
largest root-slot component among the existing profiles; this is a proposed
stress choice, not an accepted adequacy claim. These cells isolate root
quality while holding policy-pair yield uniform. They do not test interactions
between policy-pair-specific yield and root quality; reviewers must decide
whether the existing pair-only yield cells plus these cells cover enough of
that joint dependence.

## Root-factor and validity law

For each variant × band stratum and each of its 64 candidate slots, draw an
ordered policy pair uniformly as in draft 02 and independently draw
`H ~ Normal(0,1)`. Within an outer dataset, `H` is mutually independent of
the policy pair, seed effects, residual root-slot effects, seed × slot arm
effects, matchup effects, seat effects, and game residuals. The slot's
Bernoulli validity coin is independent of all score components conditional
on `H` and the policy pair. Draws of `(policy_pair,H,validity coin)` are
independent across candidate slots and strata under this synthetic law. Use
`H` as one latent root-quality factor for that slot, shared by every seed,
arm, seat assignment, and candidate-control comparison on the accepted root.
Draw slot validity as

```text
P(valid | H, policy_pair) = logistic(a_gamma + gamma * H)
```

where `gamma` is the signed value in the cell table and `a_gamma` is the
unique intercept satisfying `E[logistic(a_gamma + gamma*H)] = 0.40`.
Solve the intercept before any simulation using composite Simpson integration
of the standard-normal density on `[-10,+10]`, at 4,096 and 8,192 equal
subintervals. Use monotone bisection on `[-8,+8]` with absolute residual
tolerance `1e-12`. The omitted normal tail probability is below `2e-23`.
Record the Python version, interval counts, bisection residual, and validity
integral at both orders. Require the intercept and validity integral to agree
across orders within `1e-10`.

This preserves marginal `q=0.40`, so under the stated IID slot assumptions
the six-stratum schedule-pass probability remains the same as the ordinary
equal-yield case. The association changes which root factors are selected,
not the marginal yield rate.

In P2, split one half of the root-slot pair-margin variance into the root
factor. For each band, the original root-slot pair variance is `0.75`; set
`v_root_quality = 0.375` and multiply the existing seven-arm root-slot
covariance by `0.5`, leaving its other covariance components unchanged. In
arm order `(V1,V2,C1,C2,C3,C4,C5)`, define root-factor loadings
`ell=(0.5,0.5,-0.5,-0.5,-0.5,-0.5,-0.5)` and add
`sqrt(v_root_quality) * ell[a] * H` to arm `a`'s latent margin for the slot.
Every candidate-control pair then receives the same root-factor margin
`sqrt(0.375)*H`; its variance is `0.375`. The residual root-slot component
has pair variance `0.375`, so total root-slot variance remains `0.75` for
every pair and the unconditional P2 mean pair-margin variance remains 1.
This creates a shared, rank-one score component tied to root validity while
retaining the declared shared-arm contrast construction.

Use the accepted slots only. Draw each accepted slot's `H` once and reuse it
across all model seeds and arms; do not redraw root quality by seed or seat.
Rejected slots have no generated match scores. Continue to reverse the fixed
seat effect across seat assignments and derive macro contrasts exactly from
the ten atomic contrasts, as in draft 02.

## Conditional target calibration

After selection, the root-factor density is

```text
f_gamma(h | valid) = phi(h) * logistic(a_gamma + gamma*h) / 0.40.
```

For P2, the non-root-quality latent-margin standard deviation is
`sigma_rest = sqrt(1 + 1 - 0.375) = sqrt(1.625)`: unit game residual plus
the remaining profile components. For target mean `m`, solve `eta` from

```text
integral f_gamma(h | valid)
       * F(eta + sqrt(0.375)*h; tau=0.25, beta=0.15, sigma=sigma_rest) dh
= m,
```

where `F` is draft 02's exact seat-averaged ordinal-score expectation. This
sets the population mean under the success-conditional root distribution,
not the preselection distribution. Use the same 4,096/8,192-subinterval
Simpson pair on `[-10,+10]` to evaluate the integral. Require the solved
`eta` and achieved conditional mean to agree across orders within `1e-10`;
use the existing `[-8,+8]` `eta` bisection and `1e-10` residual tolerance
with the draft-02 normal CDF. Record the Python version, domain, interval
counts, and both estimates. These integration and stopping choices are
proposals and must be independently reviewed before implementation or use.
If convergence fails, do not increase the interval count silently; revise and
review the protocol.

The calibration audit manifest must include `gamma`, `a_gamma`, marginal
yield residual, root-quality loadings/covariance, remaining root-slot
covariance, selected-root mean/variance of `H`, the quadrature convergence
record, solved `eta`, and achieved conditional target mean for every cell,
band, and candidate-control contrast. A failed intercept, integral, target,
or covariance check invalidates the proposed cell before simulation.

## Multiplicity, precision, and workload implications

If all four cells are adopted unchanged, the proposal would contain 35
scenarios: 28 null cells and seven alternatives. Its one-sided outer
Monte-Carlo family would contain 63 endpoints: 28 strong-FWER endpoints over
null cells and 35 full-family interval-coverage endpoints. The draft-02
`R=18,000` precision calculation for 57 endpoints cannot be carried forward;
Bonferroni cutoffs and dependence-robust joint assurance must be recomputed
for 63 before any run. Reproduce the analytic values with
`python tools/v212_calibration_assurance.py --replications 18000 18200 --endpoints 63 --cells 35`;
the output is recorded in `/tmp/caissa-v212-root-quality-assurance-audit.log`.
At 63 endpoints, the analytic assurance helper gives
a dependence-robust union lower bound of `0.7947410753` at `R=18,000`, below
the proposed 0.80 target. At `R=18,200`, the one-sided Bonferroni cutoff is
991 failures, its boundary pass assurance is `0.9969198147`, and the union
lower bound is `0.8059483245`. Thus `R=18,200` is a candidate replacement if
reviewers retain the 0.80 target; the reviewer must verify the endpoint
mapping and accept the precision rule. At 35 cells, `R=18,200`, and
`B=10,000`, workload is 6.37 billion inner bootstrap replicates, or up to
95.55 billion contrast evaluations. These are analytic workload counts, not
a local feasibility result. Any precision or replication change requires
review.

The four additions are not a full cross of profile × yield × root-quality
association. If reviewers require that broader grid, recalculate the endpoint
family, Monte Carlo assurance, workload, and local resource preflight in a
new version before simulation. Do not run a subset and describe it as the
full proposed calibration.

## Open review questions

1. Is the shared slot-level `H` a useful abstract stress for root-state or
   prefix-quality selection, or does it fail to represent a material feature
   of the actual first-passage process?
2. Are `gamma=±1`, a half-root-slot variance allocation, and the P2 profile
   defensible stress magnitudes? What sensitivity range is needed?
3. Is uniform `q=0.40` an adequate isolation, or must policy-pair-specific
   yield be crossed with root quality in the calibration grid?
4. Are the score loadings, shared-factor reuse, conditional-mean calibration,
   and quadrature contract mathematically and operationally coherent?
5. Are 35 cells / 63 endpoints sufficient, and what replication count gives
   the predeclared joint precision target? Is the resulting compute workload
   feasible locally?
6. Does adopting this stress require a complete new version of calibration
   draft 02 and a fresh method review before any simulation?

Until these questions and the draft-02 dispositions are independently
resolved, v04 remains current, calibration remains unapproved, and root
generation, simulation, scoring, inference, training, and match gates remain
closed. No random draws, roots, model outputs, scores, or outcomes were
accessed or generated in preparing this proposal.

## Deterministic proposal audit (2026-10-07)

`tools/v212_root_quality_calibration_audit.py` implements the proposed
composite-Simpson intercept/conditional-mean calculations, P2 root-slot
covariance split, 120-row cell × band × contrast manifest, and 63-endpoint
assurance call without an RNG. Its seven standard-library fixture tests pass;
the focused test log is `/tmp/caissa-v212-root-quality-calibration-tests.log`
and the JSON manifest is `/tmp/caissa-v212-root-quality-calibration-audit.json`.
The current audit runtime is Python 3.14.7, whereas the research runtime lock
records Python 3.11.9 on Windows. This audit does not change or satisfy the
runtime pin; simulator runtime and numerical/source fingerprints must be
frozen and independently reviewed before any calibration run. Read-only
source review found no major formula/scope issue; its requested dedicated
intercept bracket-width constant is implemented and follow-up confirmed
resolution.
