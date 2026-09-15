# MARS-JEPA Chess: Research Identity

## Canonical name

**MARS-JEPA Chess**

**MARS-JEPA: Multi-Horizon Action-Conditioned Response-Aware State Prediction
for Resource-Bounded Zero-Sum Chess**

## Acronym

- **M**ulti-horizon prediction: H1/H2/H4.
- **A**ction-conditioned latent prediction.
- **R**esponse-aware modelling of the opponent reply.
- **S**tate prediction in latent space.

## Scope

The current research target is a chess-specific JEPA system evaluated on
deterministic two-player zero-sum chess. Chess is the controlled testbed. The
project must not claim a generic architecture for all two-player games until
the same abstraction is implemented and evaluated on additional games.

## Intended contribution

The falsifiable hypothesis is that action-conditioned, opponent-response-aware
multi-horizon latent prediction can improve resource-bounded chess planning
over matched single-horizon and no-response controls.

The paper must separately evaluate representation quality, policy/value quality,
and complete search strength under matched data, parameters, search, and
compute budgets.

## Compatibility

`CAISSA-JEPA` remains a legacy package, executable, installer, and storage
identifier until a verified migration is complete. New research-facing
documentation, experiment manifests, result tables, and paper materials must
use `MARS-JEPA Chess`.

## Claims not allowed yet

- No generic two-player-game claim.
- No superiority claim over Stockfish without a pinned independent referee and
  a confirmatory protocol.
- No claim of Q1 readiness or acceptance probability from prototype tests.
