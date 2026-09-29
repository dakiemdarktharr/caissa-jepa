# Pinned third-party Reversi rules reference: proposed acquisition and audit

2026-09-29. **Plan only.** Public source text was inspected; no library files
were downloaded to the workspace, installed or executed. No research dataset,
checkpoint, partial experiment output or protected split was opened. The
reference has not yet passed our differential tests.

## Qualification and license

Candidate: [y-tetsu/reversi](https://github.com/y-tetsu/reversi), immutable commit
`60b386dd16fb9d753e50736443a600cae24a5170`.

The [license at that commit](https://raw.githubusercontent.com/y-tetsu/reversi/60b386dd16fb9d753e50736443a600cae24a5170/LICENSE)
is MIT, copyright 2019 y-tetsu. It permits copying, modification and distribution
subject to retaining the copyright and permission notice in copies or substantial
portions. Preserve the complete original LICENSE with any acquired source and
identify upstream attribution in the audit report. There is no license acceptance
click, account or paid service proposed here. This source-code license does not
establish rights to unrelated datasets, assets or trained models.

The pinned [board implementation](https://raw.githubusercontent.com/y-tetsu/reversi/60b386dd16fb9d753e50736443a600cae24a5170/reversi/board.py)
supports even sizes 4 through 26 and exposes `PyListBoard` and `PyBitBoard`.
`PyListBoard` supplies legal placements, flippable coordinates, mutation, board
export and counts; it can initialize directly from black/white bitmasks. It is
a plausible independent implementation for the project's 6x6 rules variant,
not an independently validated perfect player or strength baseline.

Important qualification: `PyListBoard.put_disc` writes a disc even when no
flippable discs were found. Therefore only moves returned by the upstream legal
move function may be executed. Its mutation method alone is not a legality
validator. Invalid coordinates also need an explicit wrapper check.

The pinned [game loop](https://raw.githubusercontent.com/y-tetsu/reversi/60b386dd16fb9d753e50736443a600cae24a5170/reversi/game.py)
skips a player without legal moves, ends when neither player can move, and judges
the outcome by disc counts. The board API itself does not implement a pass
action or expose a complete game-state terminal method. Those orchestration
rules must be explicit in our adapter and distinguished from upstream calls.

## Exact-source acquisition, separate from the current training package

Before any comparison, acquire only these original files from the pinned raw
URLs: `LICENSE`, `reversi/color.py`, `reversi/disc.py`, `reversi/board.py`; retain
`reversi/game.py` as the inspected pass/terminal reference if redistributed.
Do not install the package, invoke setup/build hooks, acquire assets or clone
unnecessary history. This is a future authorized development step, not work
performed by this plan.

Create a manifest with repository URL, commit, original relative path, immutable
raw URL, exact byte size, SHA-256 of **raw bytes**, acquisition timestamp and
license path/hash. Record original Git blob identifiers if obtained from the
pinned tree, as an additional check. Do not calculate these hashes from browser
or Exa text: that extraction can alter whitespace. No raw-byte hashes are
claimed in this document. Freeze the manifest before running comparisons;
verify every hash before each run and reject missing or changed files.

Keep acquired originals byte-for-byte unchanged. Any loader/conversion wrapper
is project-owned, stored separately and hashed separately. If source is later
published, include its license and provenance rather than describing copied
upstream code as our implementation. The current V2.5 source inventory remains
unchanged; this audit must have its own version and receipt.

## Minimal isolated loading protocol

The [package initializer](https://raw.githubusercontent.com/y-tetsu/reversi/60b386dd16fb9d753e50736443a600cae24a5170/reversi/__init__.py)
imports GUI/application, strategy and other modules. The
[Cython initializer](https://raw.githubusercontent.com/y-tetsu/reversi/60b386dd16fb9d753e50736443a600cae24a5170/reversi/cy/__init__.py)
imports `pyximport` and calls its installation hook before checking its fallback
environment flag. Setting that flag alone does not provide a dependency-free
load. Do not execute either initializer.

Proposed loader: in a short-lived isolated Python subprocess, create a private
`reversi` namespace and load the exact `color.py`, `disc.py` and `board.py` bytes
with standard import machinery. Supply documented sentinel modules for
`reversi.cy` and `reversi.BitBoardMethods`, which `board.py` imports but whose
methods `PyListBoard` does not use. The Cython sentinel exposes only
`IMPORTED=False`; all unexpected attribute requests on either sentinel fail.
Instantiate **only** `PyListBoard`. Do not invoke `Board`, `BitBoard` or
`PyBitBoard`, replace rule methods, extract/rewrite their AST, or copy our own
rule implementation into the namespace.

This intentionally adapts import wiring, not rule logic. Record that limitation
and the sentinel inventory. Test that actual legal moves/flips/transitions never
touch a sentinel; if they do, stop and inspect the required original dependency
instead of supplying substitute game logic. Reject unexpected `sys.modules`
preloads and prove the loaded classes originate from the pinned file. Disable
bytecode writes and keep the namespace confined to the subprocess.

## Conversion, pass and terminal contract

Freeze these conventions before differential testing:

- Project board storage has 36 row-major entries. Upstream `(x,y)` corresponds
  to project board index `6*y+x`, but project action ID is **`8*y+x`**.
  IDs in padded columns/rows are invalid; `64` is reserved for forced pass.
- Project `+1` is upstream black and `-1` is white. Empty is zero. Construct
  bitmasks using bit `35-(6*y+x)`; reject overlapping masks, holes or green
  discs. Round-trip every initialized board through `get_board_info` before use.
- Ask upstream legal placements for both colors. If the moving color has
  placements, expose those actions. If only the other color has placements,
  expose pass `64`; passing preserves the board and changes player sign.
  If both sets are empty, expose no actions and declare terminal.
- Terminal utility is the sign of black count minus white count in absolute
  `+1` perspective. A player-relative label multiplies by the current player.
  Never confuse “current player cannot move” with termination.
- For a placement, check membership in the **upstream** legal set before calling
  `put_disc`, then export the complete board. Obtain reference flip coordinates
  from `get_flippable_discs`; do not derive them using the project adapter.

## Prospective acceptance and evidence limits

Start with synthetic initial, boundary/corner, forced-pass, mutual-no-move,
full-board win/loss/draw and role-swap cases. Include a terminal board with empty
cells. Verify inverse conversions, both players' legal sets, every legal action's
complete successor board, flip sets, player change and terminal utility. Test
invalid project actions in the wrapper, without deliberately executing an illegal
upstream mutation. Check upstream count fields against exported boards.

Next use a fixed, declared set of reference-generated legal trajectories and
exhaust every legal alternative at each sampled state. Freeze seeds and a finite
state/time budget before running; include required pass/terminal coverage or
report the missing coverage. Do not generate reference transitions by calling the
implementation under test. Preserve every mismatch with source hashes and a
minimal reproducible state; never silently discard failures or tune conversion
conventions until they pass.

Acceptance requires zero disagreements on the declared comparisons, verified
source identity, explicit per-category counts and no unintended imports. This
supports rule compatibility on tested states. It does not prove all reachable
states, validate existing oracle labels, establish engine strength or confirm
JEPA benefits. An independent minimax-label check would additionally require a
separately reviewed solver driven entirely by the upstream transition interface.

## Frozen first differential-audit schedule

Before implementation/execution, declare the first finite audit as follows.
Acquire only the five pinned originals above into ignored
`chess_data/external-y-tetsu-60b386d`, preserving raw bytes and MIT notice. Bind
the acquisition manifest to exact SHA-256 and Git blob SHA-1 identities from
the pinned GitHub tree; reject existing output paths and mismatching bytes.
An aggregate public source receipt may contain hashes, sizes and original URLs,
but not republish assets or conflate this source-code license with dataset rights.

Test both size4 and size6. Per size, generate100 complete legal trajectories
using only upstream-derived rules and NumPy SeedSequence[2601,size,trajectory],
trajectory indices0..99. Choose uniformly from the reference legal actions in
sorted project-action order, including forced pass. Stop only at reference
terminal;100 plies is a hard safety limit and a violation fails the audit.
At every visited state, compare both players' legal sets, terminal utility,
counts and every legal successor/flip set against the project adapter. For
each reference placement, initialize a fresh original board and check legal
membership before mutation. A disagreement is preserved and fails acceptance;
no trajectories or branches may be discarded/reseeded.

Add deterministic synthetic fixtures for both sizes: initial state; empty corner
with flippable horizontal/vertical/diagonal lines; full win/loss/draw; terminal
with empty cells; and forced pass (all black except white index1 and empty
index2, white to move). Include sign-negated/player-swapped counterparts and
reject padded/out-of-range/occupied/nonflipping actions in the wrapper. Fixtures
test rule contracts and are not claimed to be reachable empirical positions.
Require at least one forced pass, terminal-with-empty and corner capture per
size in the combined fixture/trajectory audit, and report fixture and trajectory
counts separately so fixture coverage cannot masquerade as sampled coverage.

The audit reads no research datasets, checkpoints or model outputs and performs
no fitting, search or oracle-label replacement. Limit to120s and256MB output;
run after the active V2.5 grid finishes to avoid competing with its CPU budget.
Save source/wrapper/project-rule hashes, seed protocol, all counters, elapsed
time and a new immutable success/failure receipt. Independent review precedes
using a pass to strengthen the benchmark's rules-compatibility statement.
