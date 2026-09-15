# MARS-JEPA Chess: Research Identity

**MARS-JEPA: Multi-Horizon Action-Conditioned Response-Aware State Prediction for Resource-Bounded Zero-Sum Chess**

- M: multi-horizon prediction, currently H1/H2/H4.
- A: action-conditioned latent prediction.
- R: response-aware modelling of the opponent reply.
- S: future-state prediction in latent space.

Chess is the controlled deterministic, two-player, zero-sum testbed. Generic
transfer to other games requires another implemented and evaluated domain.

The intended contribution is a falsifiable hypothesis: response-aware,
action-conditioned multi-horizon latent prediction can improve resource-bounded
chess planning over matched single-horizon and no-response controls. Separate
representation, policy/value, and full-search measurements are mandatory.

The inference aggregation is a behavioral policy-weighted expectation. The
policy-induced response distribution is uncalibrated; it is not a worst-case
adversarial model. H4 is an observed-trajectory auxiliary loss. Missing future
targets are masked and no counterfactual game outcomes are fabricated.

CAISSA-JEPA remains a legacy package, module, executable, installer, checkpoint
filename and storage identifier until a separately verified migration. New
research documentation, experiment manifests and paper materials use
MARS-JEPA Chess. Existing checkpoint loading does not establish compatibility
with a newly audited dataset or objective/protocol version.

No superiority claim over Stockfish is allowed without an independent pinned
referee and a completed confirmatory protocol. No Q1 readiness or acceptance
probability follows from prototype tests. Negative findings must be reported.
