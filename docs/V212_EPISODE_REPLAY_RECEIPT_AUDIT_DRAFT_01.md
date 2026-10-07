# V2.12 episode replay receipt — draft 01

**Status: synthetic in-memory content receipt only.** This draft records a
deterministic receipt helper built over the existing exact-rule trajectory
auditor. It does not amend the method or the accepted profile preregistration,
generate/select episodes, identify source files, authorize schedule use,
profiling, inference, or training. The six-arm graph freeze remains **NO** and
the ≤5% compute gate remains **untested and unpassed**.

## Receipt contents

`two_player/v212_episode_replay_receipt.py` accepts one episode mapping with
exactly `game`, `episode_id`, `split`, `states`, `actions`, and absolute
terminal `outcome`. It calls the current whole-episode exact-rule auditor,
which verifies every transition, player alternation, and the final terminal
outcome before any receipt is returned. The canonical episode-payload digest
binds the declared adapter/rules identity and the complete ordered state/action
record. The receipt also lists every derived source-window identity and its
existing canonical window-payload digest. Its own digest covers all receipt
fields except itself. A validator rebuilds the receipt and compares it with
the supplied mapping.

The helper is deliberately in-memory. It does **not** hash raw source-file
bytes, establish file provenance or split ownership, fingerprint the loaded
rules implementation, sign/authenticate the receipt, or prove who supplied the
episode. It also inherits the current auditor's duplicate-canonical-window
rejection policy. Do not describe this as source-file-bound provenance or as a
corpus audit.

## Evidence and next boundary

Three synthetic fixture tests check complete replay binding, mutation
rejection, illegal-transition rejection, and strict field handling. The
focused receipt plus trajectory-audit suites pass 10/10 with the temporary
NumPy 2.5.3 dependency path under Python 3.14.7; this is not the locked Python
3.11.9 / NumPy 2.4.6 runtime. No production/synthetic research corpus was
loaded or generated, and no roots, profiles, inference, scores, outcomes, or
training were accessed or run.

The schedule manifest and paired batch boundary do not consume or verify these
receipts yet. A separately reviewed schedule/trainer boundary must require an
episode receipt registry, prove each selected window payload belongs to its
exact audited episode receipt, check actual masks against the schedule, and
prevent scheduled work from bypassing the 64-window/32-per-game adapter. The
receipt alone does not satisfy D03 replay, provenance, graph-freeze, or compute
parity gates. Preserve existing negative results and novelty risks.
