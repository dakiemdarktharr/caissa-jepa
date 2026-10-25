# V2.12 request/response schema-bound audit draft 01

Status: read-only source audit; no request/response v02 schema or byte cap is
selected. This audit does not authorize adapter integration, inference,
training, pilot execution, or a resource-gate change.

## Finding

The existing transport ceiling (`MAX_IPC_BYTES = 65_536`) is not yet
replaceable by a defensible smaller request or response limit. The source has
useful candidate structure, but it does not define closed field domains or
maximum encodings for every field. Setting a smaller cap now would be an
assumption rather than a bound derived from a versioned schema.

## Source facts

`two_player/v212_request_adapter_v02.py` currently writes a 14-field request:
`variant`, `target_ply`, `root_seed`, `root_state_sha256`, `board`, `player`,
`arm`, `model_seed`, `request_started`, `planner_deadline`, `node_cap`,
`rss_cap_bytes`, `expected_cgroup_path`, and `expected_memory_max`. It
serializes with `json.dumps(..., separators=(",", ":"))`, but accepts caller
parameters and runtime values beyond a closed schema. In particular, the two
deadlines are floating-point monotonic seconds; several positive integer
limits have no protocol-level maximum; `target_ply` and cgroup path length have
no declared bound. The worker calls unbounded `sys.stdin.read()` and then
parses JSON without schema, duplicate-key, or canonical-byte validation.

The successful worker reply contains an action, completed depth, stop reason,
eight search counters, peak sampled RSS, floating-point search wall seconds,
worker cgroup path, and worker memory maximum. The error path emits
`{"worker_error": <exception class name>}`. There is no closed response
schema, explicit response cap below the transport ceiling, or bound on the
worker-error string. The existing `read_response()` is byte-bounded and
rejects duplicate keys/non-finite JSON values, but defaults to the generic
65,536-byte limit and returns parsed JSON without exact-byte digest, schema
validation, or canonical re-encoding.

The adapter source contains useful finite candidates: four variant names, six
arm names, at most 64 board cells, board values in `{-1,0,1}`, player in
`{-1,+1}`, and action IDs in `[0,64]`. The request adapter defaults to 10,000
nodes, a 5-second planner deadline, a 6-second response deadline, a 1.5 GiB
RSS cap, and a 1.5 GiB expected `memory.max`; it accepts overrides. The
separate no-training `v212_pilot` instead defaults to 500,000 nodes, 8 seconds,
and a 1.5 GiB RSS cap. These implementation constants are not normative
schema bounds.

## Compute/resource profile reconciliation (static audit, 2026-10-06)

The current source and approved/draft protocols contain four distinct profiles:

| Boundary | Node visits | Planner/wall deadline | RSS or cgroup memory | Status |
| --- | ---: | ---: | ---: | --- |
| V2.12 v04 method | 500,000 | 2.0 s per move | Not a service limit | Provisional method cap; rule-only Reversi8 p90 was 6.037 s on 16 roots, so this gate failed before learned-model calls |
| `two_player/v212_pilot.py` | 500,000 | 8.0 s | RSS 1.5 GiB | Separate random-weight, no-training instrumentation candidate |
| `two_player/v212_request_adapter_v02.py` | 10,000 | Planner 5.0 s; response 6.0 s | RSS cap and `memory.max` both 1.5 GiB | Separate unintegrated request-adapter candidate; its defaults do not revise v04 |
| Armed synthetic service profile | Not a model/search budget | `RuntimeMaxUSec=8s` | `MemoryMax=128 MiB`, `MemoryHigh=96 MiB`, swap 0 | Reviewed supervision fixture only; its live evidence is no-inference |

The request adapter's 10,000-node cap is 50 times smaller than v04's 500,000
cap. Its 1.5 GiB expected service limit is 12 times the synthetic service
profile's 128 MiB `MemoryMax`. The adapter's default therefore cannot run under
that armed-service profile as written: its preflight rejects a different
`memory.max`, and changing the expected value alone would not demonstrate that
random-weight setup/search fits within 128 MiB. The 8-second service runtime
also starts after activation and does not substitute for the adapter's
caller-observed 6-second response deadline. The schema proposal's `node_cap`
maximum of 10,000 and 5-second planner interval describe that request-adapter
candidate, not the v04 method cap; its int64 RSS and `expected_memory_max`
domains are wire-representation bounds, not approved resource requests.

No profile is selected or reconciled here. Reconciliation requires a new,
versioned no-outcome protocol that names the estimand and arm set, pins the
same reachable root schedule and order for every arm, records model setup,
search, response and receipt costs separately, and evaluates resource headroom
under a separately accepted supervision profile. The existing Reversi8
negative result must remain visible. No request, root, model, score or outcome
was run or accessed for this static audit; no adapter, inference, pilot,
training, service or OOM gate changed.

## Consequences for a future v02 contract

Before calculating byte caps, a separately reviewed schema must close at least
these choices:

1. Freeze exact request/response key sets, schema identifiers, nonce and
   digest encodings, and whether worker failures are typed response variants
   or solely process/receipt outcomes. Bound every string, including the
   worker cgroup identity and any diagnostic code.
2. Decide the legal range/encoding of `target_ply`, seeds, service memory,
   node/RSS caps, and monotonic deadlines. To satisfy the amendment's
   integer-only canonical JSON rule, replace the current floating-point
   deadline and search-duration fields with specified integer units (for
   example, monotonic nanoseconds) and explicit signed-64-bit ranges, or
   version the canonical type rule with a justified finite-float contract.
3. Bind board length to a variant enum and define whether the transport carries
   all board cells or a smaller authenticated root identifier. The current
   maximum board contributes at most 64 one-digit cell values plus JSON
   delimiters, but this alone does not bound the rest of the request.
4. Derive separate request and response worst-case canonical UTF-8 byte counts
   from those frozen field/range constraints, including all fixed keys,
   schema/nonce/hash strings, separators, and maximum escaped string lengths.
   Set each cap to that exact maximum or a documented margin; prove both sides
   enforce the cap on exact bytes before parse, even if the backing stream/file
   grows concurrently.

No numerical sub-cap is proposed by this audit. The next useful design step is
to decide the versioned field/range contract and integer time representation,
then calculate independent request and response bounds and obtain review
before implementation. Until then, 65,536 remains only the generic transport
hard ceiling, not a justified protocol limit. The byte-digest/runtime amendment
and existing adapter design remain proposals; no method or research gate
changed.

## Evidence inspected

- `two_player/v212_worker_ipc.py`: generic request/response cap and current
  bounded file-backed response read.
- `two_player/v212_request_adapter_v02.py`: concrete candidate payload,
  response fields, current float deadlines, and unbounded stdin read.
- `two_player/v212_pilot.py`: candidate variant/arm enums and defaults, which
  are not yet protocol-level maxima.
- `docs/V212_REQUEST_RUNTIME_BINDING_AMENDMENT_DRAFT_01.md`: proposed exact
  byte-digest/canonicalization contract and open cap decision.
- `docs/V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md`: worker/caller boundary
  and failure/reconciliation requirements.
- `METHOD_SPEC_V212.md`, `two_player/v212_pilot.py`,
  `two_player/v212_request_adapter_v02.py`, and
  `two_player/v212_armed_protocol_v01.py`: distinct method, harness, request,
  and synthetic-service budgets compared above.
- `docs/V212_REQUEST_RESPONSE_SCHEMA_V02_PROPOSAL_DRAFT_01.md`: unreviewed
  wire-bound proposal whose 10,000-node and 5-second maxima mirror the request
  adapter candidate; those bounds do not reconcile its resource profile with
  the method or armed-service fixture.

No request was constructed or sent; no adapter, worker, service, inference,
game state, score, or outcome was run or read. This is a static source audit.
