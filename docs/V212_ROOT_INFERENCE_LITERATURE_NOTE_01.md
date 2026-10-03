# V2.12 root-inference literature note 01

**Status: no-training methodological research.** This note evaluates whether
the proposed V2.12 crossed, stratified bootstrap can be accepted from general
theory alone. It does not select a replacement inferential procedure, approve
the v05 estimand, authorize synthetic calibration, generate roots, or open
scores/outcomes. The statistical-review disposition in
`docs/V212_ROOT_SAMPLING_REVIEW_01.md` remains required.

## Design under review

The v05 draft resamples 20 model-seed IDs jointly across arms, variants and
bands, then resamples 16 accepted slot IDs independently within each of six
variant × occupancy-band strata. Pairing and the fixed band/variant weights
are retained. It proposes 10,000 bootstrap replicates for 15 contrasts,
studentized max-|T| intervals, centered one-sided bootstrap p-values and Holm
adjustment. The accepted slots are the first 16 valid receipts among 64
predeclared candidates in each stratum, conditional on passing the global
six-stratum yield gate.

## What the primary methods literature establishes

Owen's pigeonhole bootstrap treats crossed row/column effects by separately
resampling both dimensions. Its result is a mean-consistency property under
crossed random-effects assumptions; the paper also notes that no bootstrap is
exact in general and that naive resampling can mislead. This supports viewing
the seed × slot resampling structure as a recognizable crossed-bootstrap
family, but does not establish finite-sample coverage for this outcome,
stratification, yield conditioning, studentization, or simultaneous contrasts
([Owen 2007](https://arxiv.org/abs/0712.1111)).

Work on multiway cluster inference derives validity under stated asymptotic
conditions and compares procedures by simulation. Those conditions and
estimators are not the V2.12 paired-score statistic; the literature therefore
does not transfer an automatic guarantee to 20 seeds and 16 slots per band
([MacKinnon, Nielsen & Webb 2020](https://pure.au.dk/portal/en/publications/wild-bootstrap-and-asymptotic-inference-with-multiway-clustering/),
[Cameron, Gelbach & Miller 2011](https://doi.org/10.1198/jbes.2010.07136)).
Few-cluster work likewise documents that apparently reasonable cluster
procedures can over- or under-reject, and studies alternatives under specific
regression/treatment designs; it is a reason to validate rather than a drop-in
method recommendation ([MacKinnon & Webb 2018](https://onlinelibrary.wiley.com/doi/10.1111/ectj.12107)).

Resampling-based max-statistic or step-down multiplicity methods exploit
dependence among contrasts, but their error guarantees depend on the procedure
and assumptions. Romano and Wolf discuss finite- and large-sample step-down
methods for familywise error, including how resampling uses dependence among
test statistics; this does not validate the particular max-|T| intervals or
centered bootstrap p-values proposed for V2.12
([Romano & Wolf 2005](https://doi.org/10.1198/016214504000000539),
[Romano & Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x)). Holm
adjustment can control familywise error when its input p-values are valid; it
cannot make miscalibrated marginal bootstrap p-values valid.

## Research disposition

The literature does not establish that the proposed procedure is valid at the
draft's finite sample size. A design-matched calibration is therefore the
recommended disposition before using the v05 bootstrap for a nomination gate.
This is a research recommendation, not independent statistical acceptance;
the reviewer must explicitly decide whether calibration is mandatory and may
instead reject or replace the procedure. Replacing it with a wild, pigeonhole,
or another bootstrap without matching its assumptions would not close the
gap.

If calibration is approved, freeze the data-generating scenarios, estimator
and failure behavior before running any simulation. At minimum the scenario
grid must cover global and partial nulls across the 15-contrast family;
seed, slot, and seed × slot heterogeneity; bounded/discrete paired outcomes
with ties; the success-conditional first-valid-slot/yield mechanism and
global-yield conditioning; and power/interval width around the +0.05
nomination boundary. The scenario generator must preserve the algebraic
constraint that each macro contrast is the fixed average of its two variant
contrasts, as well as paired-seat outcomes and shared candidate/control-arm
dependence. Specify variance/covariance patterns and heterogeneity across
seed, slot, seed × slot, variant, band, and arm, including unequal-variance
cases. Report the probability that the full six-stratum schedule passes its
yield gate separately from coverage and familywise type-I error conditional
on passing that gate. Freeze outer Monte Carlo size, an uncertainty interval
for each calibration rate, acceptable numerical tolerances, and the
consequence of a failed scenario. Distinguish the outer calibration repetitions from the
10,000 inner resamples used by the proposed analysis. The inner bootstrap
count only controls Monte Carlo noise in a bootstrap approximation; it does
not measure the procedure's repeated-sampling coverage. Any conclusion from
calibration is limited to the frozen scenario grid; it is not a general
validity proof.

For scale planning only, if a true rate is near 0.95, 10,000 independent outer
calibration repetitions give a binomial standard error of about 0.0022
(`sqrt(0.95 × 0.05 / 10,000)`) before accounting for scenario/model uncertainty.
This arithmetic is not an acceptance threshold and does not authorize a run.
The reviewer must choose tolerances and sufficient outer repetitions in
advance. A calibration failure must trigger a predeclared response such as
rejecting the inferential procedure, revising the sample design in a new
version, or stopping the candidate; it must not prompt post-outcome tuning.

Until that review is complete, v04 remains current. No roots, simulations,
scores, training, matches, or outcomes were generated or accessed for this
note.
