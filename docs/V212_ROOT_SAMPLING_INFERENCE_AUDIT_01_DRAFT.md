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

## Primary sources

- Owen (2007), [The Pigeonhole Bootstrap](https://arxiv.org/abs/0712.1111).
- Owen and Eckles (2012), [Bootstrapping Data Arrays of Arbitrary
  Order](https://arxiv.org/abs/1106.2125).
- MacKinnon, Nielsen, and Webb (2021), [Wild Bootstrap and Asymptotic
  Inference With Multiway Clustering](https://doi.org/10.1080/07350015.2019.1677473).
- Preston (2009), [Rescaled Bootstrap for Stratified Multistage
  Sampling](https://www150.statcan.gc.ca/n1/pub/12-001-x/2009002/article/11044-eng.pdf).
- MacKinnon and Webb (2018), [The Wild Bootstrap for Few (Treated)
  Clusters](https://doi.org/10.1111/ectj.12107).
- Tho, Chambers, and Welsh (2026, arXiv v2), [A Proportional Random Effect
  Block Bootstrap for General Clustered
  Data](https://arxiv.org/abs/2510.07770).
