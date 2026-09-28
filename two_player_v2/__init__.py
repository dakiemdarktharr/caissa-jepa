"""Versioned v2 research. Frozen v1 modules remain available for reproduction."""
from two_player.games import BoardGame

METHOD_VERSION='caissa-two-player-v2.0'
GAMES_V2={
    'connect4-4x5':BoardGame('connect4-4x5',4,5,4,gravity=True),
    'reversi6':BoardGame('reversi6',6,6,0,reversi=True),
}
