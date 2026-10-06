# V2.12 diagnostic runtime observation inventory — draft 01

Status: unaccepted diagnostic proposal. It is not a runtime-attestation design,
release protocol, receipt field, or gate-evidence artifact.

## Purpose and boundary

The current offline candidate can preserve a bounded record of what a diagnostic
probe observes about runtime components. A path, version, device/inode pair, or
post-startup file hash is evidence about an observation. It does not prove which
bytes the interpreter, loader, standard library, or native dependencies actually
executed or mapped. A self-computed SHA-256 over the inventory provides
serialization integrity only; it is not an independent trust anchor or signature.

The v01 format therefore fixes `immutable_execution_boundary` to `false` and
`trust_anchor_sha256` to `null`. Each component may be `observed_unverified` or
`unavailable`; the overall status is `partial` when at least one observation is
present and `unavailable` otherwise. No status named `verified` is representable.
The inventory is capped at 65,536 canonical UTF-8 JSON bytes and its digest covers
the canonical fields other than the digest itself. The monotonic capture value
orders a local observation; it does not provide trusted time.

Diagnostic component `value` objects may hold observed version, path,
device/inode, hashes, or measurement details, together with a source description.
They remain claims from the diagnostic context. The schema does not require or
collect any host values and cannot promote these claims to proof.

## Independent review and current evidence

The approved read-only V03 review concluded that offline code cannot truthfully
attest executed runtime bytes without a trusted immutable execution boundary or
equivalent independent measurement. It found that the release token binds a
caller-supplied project source manifest but not the interpreter, loader, standard
library, or native runtime. The inventory candidate is kept separate from those
release and receipt paths.

Existing host research is limited to the recorded sandbox/user context: sampled
filesystem verity measurements were unavailable, no authenticated signed
RootImage trust route was demonstrated, and user-manager access was unavailable
in that context. These observations do not establish the state of a different
host/user manager. No runtime inventory was collected from a service in this
milestone.

## Implementation and validation boundary

`two_player/v212_runtime_observation_v01.py` and its standard-library tests
implement schema construction, canonical encoding/parsing, duplicate-key and
non-finite rejection, byte limits, and fail-closed diagnostic labels. These are
synthetic schema tests only. The module is not imported by the bootstrap,
controller, request adapter, service, release token, or receipt publisher.

No service, OOM test, inference, root generation, score, outcome, simulation,
training, or match was run or accessed. No runtime, request, model, or research
gate advanced. A future attestation proposal still needs an independently
reviewed trust mechanism and an execution-bound measurement path before this
diagnostic format could be considered for any gate evidence.
