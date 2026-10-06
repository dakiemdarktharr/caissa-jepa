# V2.12 policy-yield × root-quality stress — design 01 draft

**Status: unapproved calibration extension proposal.** This draft adds an
interaction sensitivity to the separate root-quality/yield addendum 01. It
does not revise calibration draft 02, adopt the prior root-quality addendum,
accept v05, authorize a simulation or root generation, or open a gate. The
four cells below are an abstract synthetic stress and are not a model of the
game-state first-passage process. Independent statistical and method review
must decide whether the combined grid is appropriate, sufficient, or should
be rejected.

## Proposed cells and pair-specific target means

Use P2 and the root-quality variance split from the preceding addendum:
`tau=0.25`, `beta=0.15`, root-quality pair-margin variance `0.375`, and
remaining root-slot pair-margin variance `0.375`. Add four cells:

| Proposed ID | Global target | Validity/root-quality slope |
| --- | ---: | ---: |
| `N-GLOBAL-YIELD-ROOTQ-NEG` | all ten contrasts 0 | `gamma=-1` |
| `N-GLOBAL-YIELD-ROOTQ-POS` | all ten contrasts 0 | `gamma=+1` |
| `A-BOUNDARY-YIELD-ROOTQ-NEG` | all ten contrasts +0.05 | `gamma=-1` |
| `A-BOUNDARY-YIELD-ROOTQ-POS` | all ten contrasts +0.05 | `gamma=+1` |

Retain draft 02's two equal-size ordered policy-pair groups. Each slot first
draws a policy pair uniformly over all 16; the first eight pairs have
`q_low=0.20`, and the other eight have `q_high=0.60`. Let the declared global
target be `M` (0 or +0.05). Reuse draft 02's pair-specific target offsets:

| Pair group | Preselection mass | Slot validity target | Conditional accepted weight | Pair target |
| --- | ---: | ---: | ---: | ---: |
| Low yield | 0.50 | 0.20 | 0.25 | `M - 0.15` |
| High yield | 0.50 | 0.60 | 0.75 | `M + 0.05` |

The marginal slot-validity rate remains `0.5×0.20 + 0.5×0.60 = 0.40`.
Among accepted slots the group weights are `(0.5×0.20)/0.40 = 0.25` and
`(0.5×0.60)/0.40 = 0.75`, so the success-conditional weighted pair target
remains `0.25(M−0.15)+0.75(M+0.05)=M`. The new sensitivity therefore
preserves the yield shift and score-mean convention while linking root quality
selection to the pair group.

## Joint validity and score law

For each candidate slot, draw `H ~ Normal(0,1)` independently of its uniform
policy pair and of the score-effect components. Given its pair group and `H`,
draw validity as

```text
P(valid | H, q_group) = logistic(a[q_group,gamma] + gamma*H),
```

where `a[q_group,gamma]` separately solves
`E[logistic(a + gamma*H)] = q_group`. Thus each ordered pair retains its
declared marginal yield rate, but accepted root-quality distributions differ
between the low- and high-yield groups. The validity coin is independent of
score components conditional on `(H, policy_pair)`. Candidate-slot draws are
IID under this synthetic law. Reuse one `H` for every seed, arm, seat
assignment, and contrast on an accepted slot. Rejected slots receive no match
scores. Retain first-16-of-64 acceptance and six-stratum schedule-pass
conditioning from draft 02; under these IID assumptions, its marginal pass
probability is unchanged from homogeneous `q=0.40`.

For every pair group and gamma, solve a separate conditional `eta` for its
pair-specific target. With `v_H=0.375`, `sigma_rest=sqrt(1.625)`, and `F`
the draft-02 seat-averaged ordinal-score expectation, solve:

```text
E[ F(eta + sqrt(v_H)*H; tau=0.25, beta=0.15, sigma=sigma_rest)
    | valid, q_group ] = M + pair_group_offset.
```

This preserves each pair group's target under its selected-root law before
averaging by its declared success-conditional weight. It does not imply that
the assumed pair-group target offsets or `gamma` magnitudes are adequate.

The root-quality factor continues to load on the seven arms as
`ell=(0.5,0.5,-0.5,-0.5,-0.5,-0.5,-0.5)` and contributes
`sqrt(0.375)*ell[a]*H` to arm `a`. Halve P2's original root-slot covariance
and add the rank-one quality covariance, as in the prior addendum. This keeps
each candidate-control root-slot margin variance at 0.75 and the unconditional
P2 mean margin variance at 1. The covariance and variance split are still
proposal assumptions, not an accepted selection model.

Use composite Simpson integration against the standard-normal density on
`[-10,+10]` with 4,096 and 8,192 equal subintervals. Solve intercepts on
`[-8,+8]` to absolute residual `1e-12`; solve `eta` on `[-8,+8]` to residual
`1e-10` or width `1e-12`. Require every intercept, validity integral,
selected-root first/second moment and variance, `eta`, and achieved target
mean to differ by at most `1e-10` between the two interval counts. Record
Python/runtime identity, both estimates, selected-root moments, q residuals,
and target residuals for every group, scenario, band, and contrast. These
numerical and stopping choices require independent review before use; do not
increase resolution silently.

## Scenario family, assurance, and workload

If the base 31 draft-02 cells, four prior root-quality isolation cells, and
these four interaction cells were all retained, the candidate inventory would
have 39 cells: 30 null and 9 alternative. The proposal uses 30 FWER endpoints
(one per null cell) plus 39 simultaneous coverage endpoints, for 69 outer
assurance endpoints. This count is conditional on retaining all preceding
proposals and requires independent review.

The deterministic assurance helper was run for 69 endpoints/39 cells. Its
dependence-robust union lower bounds are 0.751504 at `R=18,000`, 0.765070 at
`R=18,200`, 0.799061 at `R=18,400`, 0.806789 at `R=18,450`, 0.794551 at
`R=18,500`, and 0.810013 at `R=18,600`. The discrete acceptance cutoff makes
these grid values non-monotone; do not infer a minimum replication count from
the grid or carry over the 63-endpoint proposal's candidate. `R=18,450` is
only one grid point above the proposed 0.80 target, not a selected precision
rule. At `R=18,450`, `B=10,000`, 39 cells, and 15 contrasts, the workload is
7.1955 billion inner bootstrap replicates and up to 107.9325 billion contrast
evaluations. This is arithmetic, not a local feasibility result.

## Deterministic audit and unresolved disposition

`tools/v212_root_quality_yield_interaction_audit.py` computes the four
q-by-gamma intercepts, selected-root moments, conditional targets, P2
covariance check, 240 target rows, endpoint inventory, and assurance grid
without an RNG. Its six focused standard-library tests pass. The maximum
4,096/8,192 integration-order difference across validity, selected-root
first/second moments, variance, and conditional target outputs is recorded in
the JSON manifest; the maximum difference is `2.78e-17`. The maximum
intercept residual is `3.95e-13`; the maximum conditional-mean residual is
`7.48e-11`.
At `gamma=+1`, selected-root mean H is approximately `0.693` for q=0.20 and
`0.332` for q=0.60; signs reverse at `gamma=-1`. This confirms the proposed
synthetic dependence is numerically represented by the audit, not that its
magnitude or estimand is adequate. Reproduce assurance with
`python tools/v212_calibration_assurance.py --replications 18000 18200 18400 18450 18500 18600 --endpoints 69 --cells 39`.
The focused test log and JSON output are
`/tmp/caissa-v212-root-quality-yield-interaction-tests.log` and
`/tmp/caissa-v212-root-quality-yield-interaction-audit.json`.

Open questions include whether pair groups are a defensible proxy for actual
policy-pair/root-state association; whether the inherited mean offsets and
root-quality variance split remain coherent jointly; whether the combined
39-cell family and assurance endpoints match the intended inferential claim;
whether a complete calibration draft 03 should replace the separate drafts;
and whether the compute requirement is feasible. Until independently
resolved, v04 remains current, all calibration/root/model gates remain
closed, and no root, score, outcome, or simulation may be generated under
this proposal.
