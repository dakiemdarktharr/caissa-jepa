# Counterplay primary-source crosswalk

Checked 2026-10-25, Asia/Saigon. Targeted scope check, not a systematic review.
Read the abstracts and the sections named below directly on primary hosts.
No published performance number is reproduced as a local measurement.
Firecrawl retrieval failed for insufficient credits; direct web retrieval
succeeded. Three discovery queries (critical replies/world models,
adversarial counterfactual JEPA, latent opponent replies) also identified
PhyLatent. No absence-of-prior-work claim follows from this bounded search.

| Primary source and inspection | Supported overlap | Consequence for CP-01 |
| --- | --- | --- |
| Schrittwieser et al., [MuZero](https://arxiv.org/abs/1911.08265), abstract | Learned models support game planning | Latent adversarial planning is established; no new general planner claim |
| Grimm et al., [Value Equivalence](https://proceedings.neurips.cc/paper/2020/hash/3bb585ea00014b0e3ebe4c6dd165a358-Abstract.html), abstract | Models can prioritize quantities used by value-based planning | Decision preservation is not a new principle |
| Qiu et al., [AD-WM v1](https://arxiv.org/html/2609.30264v1), abstract and III-E | Predictor action recovery; candidate-bank ranking and elite regrets; diagnostic costs use each model's own encoder | Do not claim action discrimination or elite regret as new; use common reference utility and legal opponent minima |
| Subramanian, [Counterfactual Action Evaluation v1](https://arxiv.org/html/2610.02860v1), abstract and 4.2 | Exact simulator-state forks trace action changes through observations, embeddings and predictions | Forks and bottleneck auditing have precedent; symbolic full states remove the rendering layer but do not prove latent information loss |
| Zhu et al., [Dual-Frontier v2](https://arxiv.org/html/2609.26293v2), abstract and A.1 | Oracle replacement holds operator, actions, budget and seed law fixed; passive attribution has limits | Hold the tree/operator fixed for repair contrasts; do not add intervention effects as independent causal percentages |
| Cheung and He, [One-Step Prediction Fidelity v1](https://arxiv.org/html/2610.19375v1), abstract and 3.3 | Frozen-decoder fidelity/planning dissociation; matched continued-training control | Negative MSE/planning correlation alone is insufficient novelty; no uncalibrated latent-error leaderboard |
| Zeng, Ren and Song, [PhyLatent](https://arxiv.org/abs/2608.05720), abstract only | Physical grounding and counterfactual branch separation address task-relevant representation failures | Generic branch separation or anti-collapse arguments do not distinguish this study; full-text methods remain a Review 3/4 citation check if compared in detail |

The proposed adversarial repair comparison is an inference from this crosswalk,
not a source's endorsement or an established first. Review 1 must reject or
narrow a claim that these differences do not support. Before final manuscript
readiness, refresh the nearest-work comparison and inspect detailed methods
for every detailed comparison actually retained in the paper.
