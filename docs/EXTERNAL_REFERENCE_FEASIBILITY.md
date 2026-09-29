# External rules reference feasibility

Read-only primary-source check, 2026-09-29, while the V2.3 training diagnostic
was running. No package installation, execution, dataset acquisition, terms
acceptance, account creation or external communication occurred.

The existing bitboard reference is independently implemented inside this
project. It must not be described as an external engine or third-party
replication. OpenSpiel is one possible later external rules reference, with a
specific compatibility limit:

- Its [Connect Four source](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/games/connect_four/connect_four.cc)
  exposes rows, columns and x_in_row parameters. A 4-by-5 four-in-a-row reference
  is therefore plausible, subject to an actual version-pinned compatibility
  test. The column action convention and bottom-up row layout require an explicit
  mapping to this project's padded-cell actions and board layout.
- Its [Othello implementation](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/games/othello/othello.cc)
  declares no game parameters, and its [header](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/games/othello/othello.h)
  fixes an 8-by-8 board. The inspected implementation is not an unmodified
  reference for the present 6-by-6 Reversi benchmark. Do not quietly compare
  different board sizes or call a local modification an untouched reference.
- Official [Windows documentation](https://github.com/google-deepmind/open_spiel/blob/master/docs/windows.md)
  describes binary wheels for Python3.11–3.13 and marks Windows support
  experimental. This is documented availability, not validation on this machine.
- The repository's [license source](https://github.com/google-deepmind/open_spiel/blob/master/LICENSE)
  identifies Apache2.0. This source observation is not a dataset license grant
  or permission to redistribute unrelated game records.

These URLs point at mutable master as inspected; no release, commit or wheel
hash has yet been selected, downloaded or used. Before employing a reference,
freeze its exact version/hash and configuration, inspect original license and
notices, and test action/coordinate/player/terminal/pass mappings on complete
legal trajectories. This note does not alter current source identities or
retroactively turn existing checks into external validation. An external
Reversi6 reference remains unresolved.
