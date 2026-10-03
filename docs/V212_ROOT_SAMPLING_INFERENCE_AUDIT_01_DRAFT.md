# V2.12 root-sampling inference source audit 01 — draft

**Status: research note for independent statistical review only.** This audit
checks what the cited statistical sources establish relative to the proposed
root-slot/seed bootstrap. It does not validate the procedure, amend METHOD
SPEC v04, select an estimand, authorize root generation, model scoring,
training, matches, or outcome access.

## Candidate design being assessed

The current root-schedule proposal uses 64 candidate slots per occupancy
stratum and selects the first 16 valid slots in schedule order, retaining
repeated board states as repeated slot draws. The proposed inference resamples
20 model-seed ids and 16 slot ids separately within each variant/occupancy
stratum, retains the paired arms and seat assignments, combines the three
stratum estimates at fixed one-third weights, and computes max-|T| intervals
plus centered one-sided tests with Holm adjustment across 15 contrasts.

If slots are generated independently and eligibility is determined only by
each slot's predeclared validity predicate, first-16 acceptance is intended to
sample from the validity-conditional distribution within a stratum. That
argument depends on frozen, identically specified slot generators and does
not establish the actual yield, policy/prefix mixture, duplicate rate, or
sampling distribution. No root schedule was executed for this audit.

## What the cited sources support

- Owen's *The Pigeonhole Bootstrap* studies crossed random-effects data and
  shows a mean-consistency property for separately resampling rows and
  columns, including heteroscedastic crossed unbalanced random-effects models.
  This is a relevant analogy for crossed seed and root dimensions, not a
  finite-sample coverage result for this CAISSA design.
- Owen and Eckles (2012) extend crossed-factor bootstrap reweighting to
  arbitrary order. Their product-weight method estimates variance of a mean
  and is mildly conservative under stated crossed-random-effects conditions;
  their analysis also identifies regimes where interaction-only components
  can be substantially overestimated. This is a candidate variance-method
  comparison for a design-matched study, not validation of percentile or
  max-|T| intervals, centered tests, or Holm familywise behavior here.
- MacKinnon, Nielsen, and Webb derive conditions for asymptotic inference
  using particular two-way cluster-robust variance estimators and
  t-statistics in regression models. That paper does not validate the
  proposed pairs bootstrap, the max-|T| construction, or the centered
  bootstrap p-values here.
- Preston's rescaled bootstrap treats stratified multistage survey sampling
  with simple random sampling without replacement. Its sampling design and
  estimator differ from independently generated, success-conditional
  candidate slots with crossed model-seed/root outcomes.
- MacKinnon and Webb study few-treated-cluster inference for linear treatment
  models, including wild-bootstrap procedures and treatment-cluster
  conditions. This is cautionary evidence about small-cluster inference, not
  a direct justification for the CAISSA paired crossed bootstrap.
- Tho, Chambers, and Welsh's 2026-v2 proportional random-effect block
  bootstrap reports finite-sample simulation coverage for a one-factor
  clustered linear mixed model with nested observations, estimated random
  effects, and residuals. It does not cover the crossed seed-by-root-slot
  layout or the CAISSA max-|T| family. It is therefore not a drop-in
  alternative; its model-based setup is only another method for a reviewer to
  consider if the estimand is reformulated accordingly.
- Holm adjustment controls a family of valid p-values; it does not repair
  invalid or poorly calibrated input p-values. Ten thousand resamples reduce
  Monte Carlo error in the computed bootstrap distribution but do not
  increase the number of independent model seeds or root slots.

## Consequence for the V2.12 gate

The cited work motivates preserving the crossed and stratified sampling
structure, but does not prove finite-sample coverage or type-I error control
for 20 model seeds, 16 slots per occupancy stratum, two variants, paired seat
assignments, 15 contrasts, and the proposed max-|T|/Holm decision rule. This
is an unresolved validation requirement, not evidence that the method is
invalid.

Before independent review can accept the development inference, it should
decide whether to require a design-matched synthetic coverage/power study;
freeze its data-generating scenarios and acceptance criteria before running
it; assess sensitivity to seed/root variance components, seed-root
interactions, outcome discreteness/ties, conditional slot yield, and
cross-contrast dependence; and specify what failure means for the estimand,
sample size, or inferential method. It may compare the ordinary
pigeonhole-style resampling with Owen-Eckles product-factor reweighting, but
must first define whether both target the same statistic and whether variance
estimation alone suffices for the familywise interval/test rule. A nested
random-effect block bootstrap is not comparable without a compatible model
and estimand. A simulation would diagnose only the declared scenarios and
would not itself establish general validity.

The amendment and existing schedule remain drafts. Do not generate roots or
read scores while these choices are unresolved. A statistical reviewer must
make the disposition before the gate advances.

## Additional primary-source evidence: null and effect scenarios

Bakshy and Eckles evaluate bootstrap inference for dependent user–item
experiments using three real Facebook datasets to construct synthetic A/A
experiments, then use probit random-effects simulations with item–treatment
interactions. Their A/A experiments assess the sharp null; in the simulated
zero-average-effect setting, one-way user bootstrap coverage falls as those
interactions grow (87.5% for a nominal 95% interval in one reported condition),
while their multiway bootstrap remains mildly conservative in the studied
conditions. They explicitly caution that A/A checks alone cannot reveal
potentially serious inferential problems under effects. The arXiv v4 notice
also withdraws the Section 3.4/Figure 4 item-imbalance simulation because of a
software error; that result is excluded from this audit.

This is design guidance, not validation for CAISSA. The source concerns
user–item online experiments, large observational layouts, product-factor
bootstrap weights, and normal-quantile intervals. It does not evaluate 20
model seeds × 16 root slots per stratum, the proposed max-|T| intervals,
centered tests, or Holm adjustment. Its numerical coverage must not be
transferred to CAISSA.

If the independent statistical reviewer requires a design-matched simulation,
the frozen scenario set should include both (a) sharp-null/zero-contrast
scenarios and (b) nonzero mean contrasts with heterogeneous seed and
root-slot effects and seed × root interactions. Freeze variance components,
discreteness/tie behavior, slot-conditioning assumptions, cross-contrast
dependence, and acceptance criteria before running anything. Assess familywise
Type I error and interval coverage under nulls, and coverage, power, interval
width, and direction/magnitude error under alternatives as applicable to the
reviewed estimand. A/A-style null checks alone are insufficient. This
recommendation does not itself authorize a simulation or settle whether one is
required; independent review must decide. No simulation or root schedule has
been run.

## Few-factor regime and regression-based alternatives

A second primary-source scan adds a small-factor caution. MacKinnon, Nielsen,
and Webb's multiway wild-bootstrap work derives asymptotic validity for
specified two-way cluster-robust regression statistics under explicit
conditions; it does not establish finite-sample accuracy for every crossed
design. Roodman et al.'s implementation paper explains that one wild-cluster
weighting dimension cannot preserve dependence along multiple dimensions
simultaneously, and the choice of bootstrap clustering matters. The
cluster-robust practice literature warns that conventional two-way
cluster-robust inference can be unreliable when either cluster count is small
or clusters are heterogeneous; it discusses applying a one-way restricted
wild-cluster bootstrap along the smaller/more unbalanced dimension.

These results sharpen, but do not resolve, the V2.12 issue: each occupancy
stratum has only 20 seed clusters crossed with 16 sampled root-slot clusters.
The cited methods target regression coefficients, score vectors, and
cluster-robust variance estimators. V2.12 instead proposes paired arm
contrasts, stratified reweighting of both crossed factors, max-|T| intervals,
and centered tests with Holm adjustment. Therefore, wild-cluster bootstrap,
multiway CRVE, or jackknife methods are not drop-in replacements. They are
reviewer comparison candidates only if a regression/score formulation can be
shown to preserve the reviewed estimand and simultaneous-inference target.
No source found here gives a universal “safe” cluster-count threshold or
validates this finite-sample CAISSA procedure.

Independent review should explicitly address whether 20 × 16 per stratum is
adequate for the chosen inferential method and whether a design-matched
simulation must compare (i) the proposed two-factor pairs bootstrap and
product-factor reweighting and (ii) any regression-based alternative that has
a defensible mapping. Any comparison must preserve paired arms, fixed
stratum weights, and the full 15-contrast family, and must include sharp-null
and heterogeneous-effect scenarios with criteria frozen first. No method is
selected by this scan; no simulation or root schedule was run.

## Crossed mixed-effects models as a model-based comparator

The literature also supplies a structurally closer model family. Baayen,
Davidson, and Bates describe linear mixed models with crossed subject and item
effects, including random slopes, to generalize over both sampled dimensions.
Kenward and Roger propose a small-sample adjusted covariance estimator and
scaled Wald statistic with an approximate F distribution for fixed effects in
Gaussian mixed models; they report good performance in a range of small-sample
settings.

This makes a crossed mixed-effects analysis a plausible reviewer comparator,
not a validated replacement. The cited work does not establish calibration for
CAISSA's bounded/discrete paired game scores, 20 seeds × 16 roots per
occupancy stratum, three fixed-weight occupancy strata, 15 related contrasts,
or the proposed familywise decision rule. To map it to the study, a new
versioned protocol would have to define the response scale/likelihood,
arm-by-seed and arm-by-root random slopes and their covariance constraints,
fixed stratum weighting, missing/incomplete cells, variance-boundary handling,
and simultaneous intervals/tests across the 15 contrasts. Kenward–Roger's
approximation alone does not supply that full familywise procedure.

Independent review may compare such a preregistered model-based analysis with
the crossed pairs/product-weight bootstrap in a design-matched synthetic
study, using the already identified null and heterogeneous-effect scenarios.
The model and acceptance criteria must be frozen before simulation. This
source scan neither selects the mixed model nor authorizes a fit, simulation,
or outcome access.

## Interaction-dominated variance and finite-factor geometry

Owen and Eckles derive product-factor bootstrap variance for the mean under a
crossed random-effects model, not a general confidence/test guarantee. For two
factors with unit-variance weights, the interaction-only variance component
is multiplied by about three; their paper explicitly notes that this extreme
case overestimates the true mean variance by roughly 3×. Their near-correct
relative-variance result instead assumes the main-effect components are
positive and bounded, with main effects dominating and duplication ratios
small. They also note that in a complete rectangular design the maximum
proportional duplication is the inverse of the smaller factor count.

For the proposed complete 20-seed × 16-root-slot grid within one occupancy
stratum, those design ratios are epsilon = max(1/20, 1/16) = 1/16 and
eta = max(1/20, 1/16) = 1/16. These are descriptive consequences of the
planned grid, not evidence that the asymptotic approximation is accurate at
these counts. The number and relative size of seed, root, and seed × root
variance components are unknown until data exist. Owen and Eckles also cite
McCullagh's result that no exact unbiased resampling bootstrap exists for the
crossed-random-effects mean-variance problem in the broad class studied.

This narrows the simulation question: if independent review requires a
design-matched study, it should include both main-effect-dominated and
seed × root-interaction-dominated variance regimes, under null and
heterogeneous/nonzero contrast scenarios. Compare variance/coverage and the
full familywise rule separately; a variance approximation for one mean does
not validate max-|T| intervals or Holm-adjusted tests. The product-factor
method is a candidate comparator, not the declared winner; the proposed
pairs bootstrap is not identical to Owen-Eckles reweighting. No variance
components have been observed and no simulation, roots, or outcomes were
accessed.

## Primary sources

- Baayen, Davidson, and Bates (2008), [Mixed-effects Modeling With Crossed Random Effects for Subjects and Items](https://doi.org/10.1016/j.jml.2007.12.005).
- Kenward and Roger (1997), [Small Sample Inference for Fixed Effects from Restricted Maximum Likelihood](https://doi.org/10.2307/2533558).
- MacKinnon, Nielsen, and Webb (2021), [Wild Bootstrap and Asymptotic Inference With Multiway Clustering](https://doi.org/10.1080/07350015.2019.1677473).
- Roodman, MacKinnon, Nielsen, and Webb (2019), [Fast and Wild: Bootstrap Inference in Stata Using boottest](https://doi.org/10.1177/1536867X19830877).
- MacKinnon, Nielsen, and Webb (2023), [Leverage, Influence, and the Jackknife in Clustered Regression Models](https://doi.org/10.1177/1536867X231212433) (two-way discussion; regression scope).
- Bakshy and Eckles (2013), [Uncertainty in Online Experiments with Dependent Data: An Evaluation of Bootstrap Methods](https://arxiv.org/abs/1304.7406) (arXiv v4; Section 3.4/Figure 4 withdrawn).
- McCullagh (2000), [Resampling and Exchangeable Arrays](https://doi.org/10.2307/3318577).
- Owen (2007), [The Pigeonhole Bootstrap](https://arxiv.org/abs/0712.1111).
- Owen and Eckles (2012), [Bootstrapping Data Arrays of Arbitrary
  Order](https://arxiv.org/abs/1106.2125).
- Preston (2009), [Rescaled Bootstrap for Stratified Multistage
  Sampling](https://www150.statcan.gc.ca/n1/pub/12-001-x/2009002/article/11044-eng.pdf).
- MacKinnon and Webb (2018), [The Wild Bootstrap for Few (Treated)
  Clusters](https://doi.org/10.1111/ectj.12107).
- Tho, Chambers, and Welsh (2026, arXiv v2), [A Proportional Random Effect
  Block Bootstrap for General Clustered
  Data](https://arxiv.org/abs/2510.07770).
