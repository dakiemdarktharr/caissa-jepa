# V2 fork-relative geometry: second-pass novelty assessment

Date: 2026-09-29. Status: prospective mechanism assessment; no positive
CAISSA-JEPA result is established by this review. Only this document was edited
for the review. Read alongside `V2_PREDICTIVE_RESEARCH.md`.

## Decision

**Worth a small controlled mechanism experiment; not currently defensible as a
unique method.** Relational distillation already matches teacher/student latent
relations. Very close 2026 JEPA papers explicitly address latent displacement,
pairwise geometry and counterfactual branch separation. A contribution could
be the carefully measured value of legally grounded sibling-reply supervision
for bounded adversarial planning, if it survives strong controls and replication.
The proposed loss by itself does not establish that contribution.

The review used five Exa queries requesting ten results each: relational
distillation; action-conditioned contrastive/counterfactual models; bisimulation;
relative transition geometry; and a targeted search resolving recent JEPA
papers to primary sources. The total is **50 requested result slots**, not 50
independent papers or full readings. Eight primary works were retained below.
Full-text extracts covering specified methods were inspected; no claim of
complete systematic coverage or independent reproduction is made. Recent arXiv
results are author-reported preprints, not validation of our proposed design.

## Nearest primary prior art

| Work | Mechanism inspected | Overlap and remaining distinction |
| --- | --- | --- |
| Park et al., **Relational Knowledge Distillation**, CVPR 2019. [Official paper](https://openaccess.thecvf.com/content_CVPR_2019/papers/Park_Relational_Knowledge_Distillation_CVPR_2019_paper.pdf) | Full-text method and experiment extracts. General teacher/student relational potentials; normalized pairwise Euclidean distances and triplet angles. Tests on retrieval, classification and few-shot learning, including self-distillation. | Matching relations among predicted and EMA-target embeddings is within this established family. Choosing legal siblings changes the sampling structure and application, not the basic relational-distillation principle. |
| Tung and Mori, **Similarity-Preserving Knowledge Distillation**, ICCV 2019. [Official paper](https://openaccess.thecvf.com/content_ICCV_2019/papers/Tung_Similarity-Preserving_Knowledge_Distillation_ICCV_2019_paper.pdf) | Official abstract and full-text extracts. Student preserves pairwise activation similarities of a teacher; it need not reproduce the teacher coordinates. | A pairwise cosine/Gram alternative is especially close. Neither replacing teacher by EMA nor applying it to predicted branches is sufficient to claim a newly invented geometry objective. |
| Zhang et al., **Learning Invariant Representations for Reinforcement Learning without Reconstruction (DBC)**, ICLR 2021. [Original paper](https://arxiv.org/abs/2006.10742) | Full-text introduction/method extracts. Learns latent distances reflecting reward/dynamics behavioral similarity, with control and visual-distractor experiments. | Control-relevant latent geometry and value preservation are established aims. Bisimulation involves recursive behavioral structure; merely matching sibling latent differences is not a bisimulation metric or proof of minimax value sufficiency. |
| Zheng et al., **TACO: Temporal Latent Action-Driven Contrastive Loss for Visual Reinforcement Learning**, NeurIPS 2023. [Proceedings paper](https://papers.neurips.cc/paper_files/paper/2023/file/96d00450ed65531ffe2996daed487536-Paper-Conference.pdf) | Full-text introduction/method extracts. Joint state/action representation learning using contrastive dependence between current-state/action-sequence representations and future-state representations; online/offline visual-control studies. | Action-sensitive temporal distinctions are not unique to noncontrastive JEPA. A temporal contrastive control may separate generic discrimination gains from our chosen latent-matching form. Their sufficiency assumptions are not imported into minimax games. |
| Zhang et al., **Delta-JEPA: Learning Action-Sensitive World Models via Latent Difference Decoding**, June 2026 preprint. [Original text](https://arxiv.org/html/2606.31232v1) | Full-text method extracts, equations1–5. Predicts future latents and reconstructs executed actions from consecutive latent displacement, rather than concatenated endpoints. Four visual continuous-control tasks; action sensitivity is an explicit objective. | Strong overlap with claims about useful latent differences and distinguishable action consequences. It decodes the executed action; the proposed candidate matches relations between two legal reply successors from one root. This difference needs evidence, not a priority claim. |
| Hu, Zheng and Wang, **SCALE: State-Calibrated Latent Embeddings for JEPA Planning in the Right Geometry**, August 2026 preprint. [Original text](https://arxiv.org/html/2608.16287) | Full-text sections3–6. Correlates pairwise latent-distance profiles with distances in standardized task-relevant simulator states. Compares with a latent-to-state regression control across tasks, planners and compute tiers. | Especially close to shaping geometry for planning. Uses privileged state geometry and goal-distance MPC, rather than EMA sibling targets and a learned value head in minimax. Decodability and geometry must be evaluated separately, but SCALE's goal-distance argument does not automatically apply to our value-head planner. |
| Boylan and Hokamp, **No Gaussian Required: Contrastive Inverse Dynamics for JEPA World Models**, August 2026 preprint. [Original text](https://arxiv.org/html/2608.17542) | Full-text abstract/method extracts. AC-MTM keeps forward latent prediction and adds a training-only inverse-action discrimination head with in-batch action alternatives; it states conditions for its anti-collapse mechanism and reports matched planning comparisons. | Action discrimination can preserve transition information without our sibling loss. A cheap inverse-action head is a relevant later control. Different actions need not have distinct strategic values; inverse-action identifiability is not equivalent to decision sufficiency. |
| Zeng, Ren and Song, **PhyLatent: Learning Dynamics-Relevant Representations for JEPA World Models**, August 2026 preprint. [Original text](https://arxiv.org/html/2608.05720) | Full-text sections3–5, especially equations19–24. Counterfactual action sequences are formed by batch permutation plus noise. A hinge term separates their predicted latents from detached factual predictions using an action-distance margin. Other terms include physical grounding and future alignment. Planning improvements are not uniform across all reported tasks. | **Closest counterfactual-branch overlap.** Our exact legal siblings have real simulator successor targets, rather than an action-distance-based repulsion margin. This could avoid separating behaviorally equivalent branches, but the target encoder can still discard crucial distinctions. Any claim of first counterfactual JEPA or first branch-separation objective is unsupported. |

## Mathematical audit of the proposed difference loss

Fix a legal root/own-action pair `(s,a)` with K legal opponent replies. For
reply b, let `u_b` be the predicted successor latent and `t_b` its detached
target-encoder latent. Define `e_b = u_b - t_b` and
`e_bar = (1/K) sum_b e_b`. The candidate is

`L_pair = (1 / choose(K,2)) sum_{b<c} ||(u_b-u_c) - (t_b-t_c)||^2`.

For K>=2, elementary expansion gives

`sum_{b<c} ||e_b-e_c||^2 = K * sum_b ||e_b-e_bar||^2`,

so

`L_pair = [2/(K-1)] * sum_b ||e_b-e_bar||^2`.

This is **exactly centered pointwise residual MSE up to scale** for uniform
all-pair weighting. It changes emphasis by removing the group's mean residual;
it does not supply an independent kind of target information. The same identity
holds if u/t denote the normalized embeddings actually used inside the loss.
Implementing it in O(Kd) rather than explicit O(K^2 d) pairs is possible, and a
unit test should verify equality of losses and gradients.

Consequences:

- Pair-only loss cannot penalize a common shift of every prediction in a group.
  Retain pointwise anchoring or demonstrate that the value head is unaffected.
- Pair-only loss does not prevent collapse when all target latents coincide.
  EMA is not a mathematical guarantee of noncollapse or strategic sufficiency.
- Adding a uniform pair loss to pointwise MSE principally reweights within-group
  errors versus group-mean error. Report that interpretation; do not market a
  new source of relational information.
- Nonuniform reply-pair weights yield a graph-Laplacian quadratic of prediction
  residuals. If weights use teacher value gaps, they introduce supervised
  decision information; the value-ranking baseline must receive it too.
- Gram/cosine matching differs from displacement matching but is invariant to
  a common orthogonal transformation. Distance matching additionally ignores
  translation. A fixed value head can distinguish these coordinate changes;
  relation preservation alone does not ensure correct values.

These are derivations for the proposed objective, not conclusions attributed
to the cited experimental papers.

## Mechanism worth testing

The narrow hypothesis is: **conditioning the residual regularizer on legal
sibling reply groups reduces mistakes on strategically different responses
more than the same loss applied to unrelated states, with all supervised data
and compute held fixed.** This is a testable grouping hypothesis. It is more
precise than claiming all action differences should be separated.

Enumerate or seed-sample replies using exact rules from training roots only.
Keep correct role/perspective alignment, especially when a transition terminates
before the second ply. A group with fewer than two supported replies has zero
pair loss and contributes to an explicit masked-group count. Normalize at the
root-group level so games with more legal moves do not silently dominate.

Do not use arbitrary numerical distances between categorical board actions as
a strategic separation margin. Two moves can be different coordinates yet have
the same optimal outcome. Conversely, small board changes can reverse a forced
win. Exact teacher values are useful diagnostics but are a separate supervision
source if included in training.

## Required prospective controls

| Control | Purpose |
| --- | --- |
| Pointwise recurrent JEPA, same forks | Isolate sibling residual weighting from additional transition coverage. |
| Centered residual MSE, analytically matched coefficient | Verify that any all-pair implementation gives the predicted equivalent result; differences indicate code/sampling/numerical issues. This is an equivalence check, not an independent baseline. |
| Random groups/pairs matched by game, phase and group size | Test whether legal sibling grouping matters beyond generic regularization. All states remain in the same training split. |
| Non-JEPA recurrent value dynamics | Determine whether future-value supervision alone explains the gain. Identical root/branch labels and successor exposures. |
| Direct value-difference/ranking auxiliary | Test whether the mechanism is simply improved decision ordering. Supply identical teacher value-gap information if the candidate uses it. |
| Decoded dynamics | Test latent targets against explicit successor-state prediction under the same exposure and optimization budget. |
| PhyLatent-inspired branch repulsion or inverse-action auxiliary | A useful second-stage closest-prior-art control if the candidate beats simpler baselines; label as a small adaptation, not a full reproduction. |

Match architecture outside the tested mechanism, seed, train roots, branch
sampling, policy/value supervision, checkpoint selection opportunity and total
training exposure. Measure actual forward/backward time; added pair processing
must not be hidden behind equal epoch counts. Report equal-update and
compute-matched results separately. Do not add dummy computation solely to
weaken a cheaper baseline; let it use its budget productively.

Diagnostics should include pointwise and group-centered latent errors, target
rank/covariance, counterfactual value error, sibling action-order inversions and
root minimax regret. Stratify by exact teacher value-gap and legal branch count,
with counts and uncertainty. The primary downstream metric remains frozen
before selection. A reduction in latent-distance error alone is insufficient.

## Acceptance and stop conditions

Proceed beyond a small pilot only if improvement is repeatable across seeds and
non-ceiling held-out roots, survives the strongest matched non-JEPA control,
and is not explained by extra labels or compute. Keep every attempted variant
in the development ledger. A tuning-selected improvement still requires a
locked independent evaluation before a superiority claim.

Stop presenting fork geometry as a distinct mechanism if random grouping works
equally well, if value ranking explains the result, or if gains disappear under
compute matching. If exact centered-MSE equivalence explains the entire change,
describe it honestly as groupwise residual weighting. Prior-art overlap remains
material even if the adaptation works. No absence-of-search-result argument can
establish uniqueness.

Search accounting for this second pass: five `web_search_exa` calls with
`numResults=10`, totalling 50 requested result slots. Source fetches are not added
to this accounting. No paid setup, dataset download or source-code edit occurred.
