# Counterplay contribution candidate

25 October 2026, Asia/Saigon. Prospective design CP-01 v2, revised after conditional Review 1.
This is an empirical benchmark/diagnostic study, not a new JEPA architecture
or a claim of priority. Historical V2.12 and its restrictions remain unchanged.

**Question.** In exact-rule adversarial search, do errors at decision-critical
opponent replies change root regret differently from signed, comparably sized
scalar corrections elsewhere? Value and search diagnostics are secondary.

**Candidate contribution.** A reproducible audit of complete legal two-ply
forks on same-size, late-game Connect Four 6x7 and Reversi6 positions. All
models are graded by the same independently checked terminal-solved utilities.
The audit connects reply preservation, root-action regret and selective scalar
repairs in one checkpoint, retaining nonmatches and failures. Re-encoding and
full reference substitution provide separate privileged diagnostics. The
claim is about the measured finite population and these interventions; it is
not identification of information discarded by a representation.

**Why this may be useful.** Factual latent error averages over a different
population and scale than the opponent's minimum. One missed refutation can
change an action even when average error is small. The useful result could be
positive, null, negative, or a documented failure of the proposed diagnostic.
No JEPA ranking or statistical significance is required for completion.

**Closest work and boundary.** The [source crosswalk](PRIOR_WORK.md) establishes
that latent game planning, decision-relevant models, action discrimination,
counterfactual forks, fixed-operator interventions and prediction/control
dissociation all have precedents. Our proposed distinction is the combination
of adversarial minimum-sensitive reply sets, complete common-utility forks,
and within-checkpoint location-matched repairs. This is a candidate empirical
contribution requiring actual evidence, not an established theoretical novelty.

**Design.** Five equal-data/equal-update arms: multi-step JEPA, H1-only JEPA,
value-only latent rollout, decoded-state rollout, and exact-state direct-leaf.
H2 primary inference, H4 separately costed sensitivity; shared dense 198/32/65
representation on the training board sizes. The corrected V2.12 objective is
a starting implementation, with behavior-outcome supervision distinguished
from minimax references. Size transfer and a new ranking loss are deferred.
Chess inclusion is decided on readiness/cost before Review 3, never on a
favorable outcome. No engine score is interchangeable with solved regret.

**Primary estimand.** For each game and corpus, within multi-step JEPA, mean
`regret(noncritical scalar repair) - regret(critical scalar repair)` over
checkpoint/root pairs with a deterministic matched pair. Criticality depends
only on the reference table. Matching uses a predeclared absolute-error caliper
and branch type, with the same residual sign, never the action's post-repair improvement. The conditional
population and match coverage are inseparable reported results. This is a
location-sensitivity diagnostic, not a deployable repair or unconfounded
estimate of a latent mechanism. A zero-match or unresolved seed makes the equal-seed primary estimate missing.
Secondary all-root critical repairs and the scheduled repair-policy contrast
retain every root; unknown units receive conservative bounds. Known nonmatches
receive no repair under that policy, not a fabricated matched effect. Minimax
repairs mix prediction/readout error with behavior-target mismatch.

**Evidence needed.** Valid objective derivatives, legal/reproducible corpus,
independent reference checks, complete provenance and resume hooks, a bounded
development pilot, synthetic uncertainty validation and Review 3 freeze all
precede final execution. Two game-specific primary intervals control familywise
error; seeds and episode/root clusters remain paired. Independent training
corpora are analyzed separately. Counts, budgets and estimator implementation
are fixed at Review 3 using development feasibility, not final scores.

**Stop/fallback.** No affordable reference yield, matched population, learning,
or uncertainty calibration means a declared narrower feasibility report; it
does not authorize endless sweeps or a completed mechanism claim. See
[protocol](protocol.yaml), [issues](issues.csv), and [decisions](decisions.md).
