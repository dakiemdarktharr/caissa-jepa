"""Smoke/regression tests không cần pytest."""

import math
import sys
import tempfile
import threading
import types
from pathlib import Path

try:
    import PySide6  # noqa: F401
except ImportError:
    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, name):
            return _Dummy()

        def __call__(self, *args, **kwargs):
            return _Dummy()

    class _Signal(_Dummy):
        def __init__(self, *args, **kwargs):
            self._callbacks = []

        def connect(self, *args, **kwargs):
            if args:
                self._callbacks.append(args[0])

        def emit(self, *args, **kwargs):
            for callback in self._callbacks:
                callback(*args, **kwargs)

    def _slot(*args, **kwargs):
        def decorator(function):
            return function

        return decorator

    qt_core = types.ModuleType("PySide6.QtCore")
    qt_gui = types.ModuleType("PySide6.QtGui")
    qt_svg = types.ModuleType("PySide6.QtSvg")
    qt_widgets = types.ModuleType("PySide6.QtWidgets")

    for name in ("QObject", "QRect", "QRectF", "QThread", "QTimer"):
        setattr(qt_core, name, _Dummy)

    qt_core.Qt = _Dummy()
    qt_core.Signal = _Signal
    qt_core.Slot = _slot

    for name in ("QColor", "QFont", "QPainter", "QPen"):
        setattr(qt_gui, name, _Dummy)

    qt_svg.QSvgRenderer = _Dummy

    for name in (
        "QApplication",
        "QFileDialog",
        "QInputDialog",
        "QMainWindow",
        "QWidget",
    ):
        setattr(qt_widgets, name, _Dummy)

    sys.modules.update({
        "PySide6": types.ModuleType("PySide6"),
        "PySide6.QtCore": qt_core,
        "PySide6.QtGui": qt_gui,
        "PySide6.QtSvg": qt_svg,
        "PySide6.QtWidgets": qt_widgets,
    })

from main import (
    caissajepa,
    caissamcts,
    chessdatabase,
    engineworker,
    importworker,
    json_thanh_snapshot,
    key_thanh_text,
    move_thanh_text,
    pgnparser,
    text_thanh_move,
    vitriengine,
)


def perft(engine, depth):
    if depth == 0:
        return 1

    nodes = 0

    for move in engine.lay_tat_ca_nuoc_di_hop_le(engine.turn):
        undo = engine.thuc_hien_nuoc_di(move)
        nodes += perft(engine, depth - 1)
        engine.hoan_tac_nuoc_di(undo)

    return nodes


def uci_set(engine):
    return {
        move_thanh_text(move)
        for move in engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
    }


def test_rules_and_hash(parser):
    engine = vitriengine(parser.tao_snapshot_ban_dau(), 0.05)
    assert [perft(engine, depth) for depth in (1, 2, 3)] == [20, 400, 8902]
    original = (
        engine.board.copy(),
        engine.turn,
        engine.castling_rights.copy(),
        engine.en_passant_target,
        engine.zobrist_hash,
    )

    for move in engine.lay_tat_ca_nuoc_di_hop_le(engine.turn):
        undo = engine.thuc_hien_nuoc_di(move)
        assert engine.zobrist_hash == engine.tinh_zobrist_hash()
        engine.hoan_tac_nuoc_di(undo)
        assert (
            engine.board,
            engine.turn,
            engine.castling_rights,
            engine.en_passant_target,
            engine.zobrist_hash,
        ) == original

    castle = vitriengine(
        parser.fen_thanh_snapshot("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"),
        0.05,
    )
    assert {"e1g1", "e1c1"}.issubset(uci_set(castle))

    castle_blocked = vitriengine(
        parser.fen_thanh_snapshot("4kr2/8/8/8/8/8/8/R3K2R w KQ - 0 1"),
        0.05,
    )
    assert "e1g1" not in uci_set(castle_blocked)

    en_passant = vitriengine(
        parser.fen_thanh_snapshot("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"),
        0.05,
    )
    assert "e5d6" in uci_set(en_passant)

    exposed_king = vitriengine(
        parser.fen_thanh_snapshot("8/8/8/r4pPK/8/8/8/4k3 w - f6 0 1"),
        0.05,
    )
    assert "g5f6" not in uci_set(exposed_king)

    promotion = vitriengine(
        parser.fen_thanh_snapshot("4k3/P7/8/8/8/8/8/4K3 w - - 0 1"),
        0.05,
    )
    assert {"a7a8q", "a7a8r", "a7a8b", "a7a8n"}.issubset(
        uci_set(promotion)
    )

    mate = vitriengine(
        parser.fen_thanh_snapshot("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"),
        0.05,
    )
    assert not uci_set(mate) and mate.is_king_in_check("black")

    stalemate = vitriengine(
        parser.fen_thanh_snapshot("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
        0.05,
    )
    assert not uci_set(stalemate) and not stalemate.is_king_in_check("black")

    # Alpha-beta and MCTS must agree on non-move terminal draws.  This
    # regression caught the previous case where MCTS sent K-vs-K to the
    # learned value head despite alpha-beta returning a draw.
    insufficient = vitriengine(
        parser.fen_thanh_snapshot("7k/8/8/8/8/8/8/4K3 w - - 0 1"),
        0.05,
    )
    insufficient_moves = insufficient.lay_tat_ca_nuoc_di_hop_le(
        insufficient.turn
    )
    assert insufficient.is_draw_search()
    assert caissamcts(
        parser.fen_thanh_snapshot("7k/8/8/8/8/8/8/4K3 w - - 0 1"),
        None,
        0.05,
    ).terminal_value(insufficient, insufficient_moves) == 0.0

    mate_in_one = vitriengine(
        parser.fen_thanh_snapshot("7k/8/5KQ1/8/8/8/8/8 w - - 0 1"),
        0.20,
    ).tim_nuoc_di_tot_nhat()
    assert move_thanh_text(mate_in_one["move"]) == "g6g7"
    assert mate_in_one["score_white"] > 900

    free_queen = vitriengine(
        parser.fen_thanh_snapshot("4k3/8/8/8/3q4/8/3Q4/4K3 w - - 0 1"),
        0.20,
    ).tim_nuoc_di_tot_nhat()
    assert move_thanh_text(free_queen["move"]) == "d2d4"
    assert free_queen["time"] < 0.35


def test_parser_database_and_model(parser):
    pgn = '''[Event "Test"]
[White "Alpha"]
[Black "Beta"]
[WhiteTitle "GM"]
[Result "1-0"]

1. e4 {main} e5 $1 2. Nf3 (2. Bc4) Nc6 3. Bb5 a6 1-0
'''
    game = parser.parse_game(pgn)
    assert len(game["records"]) == 6
    assert game["records"][0]["move_text"] == "e2e4"

    with tempfile.TemporaryDirectory() as temp_dir:
        database = chessdatabase(Path(temp_dir) / "test.db")
        import_path = Path(temp_dir) / "gm_test.pgn"
        import_path.write_text(
            pgn
            + '''
[Event "GM loses"]
[White "Gamma"]
[Black "Delta"]
[WhiteTitle "GM"]
[Result "0-1"]

1. d4 d5 2. c4 e6 0-1
''',
            encoding="utf-8",
        )
        import_stop = threading.Event()
        importer = importworker(
            [str(import_path)],
            str(database.database_path),
            import_stop,
        )
        import_results = []
        importer.ket_qua.connect(import_results.append)
        importer.chay()
        assert import_results[0]["imported"] == 1
        assert import_results[0]["skipped"] == 1

        with database.ket_noi() as connection:
            gm_sides = connection.execute(
                "SELECT DISTINCT side FROM contributions WHERE source_type='GM'"
            ).fetchall()

        assert [row["side"] for row in gm_sides] == ["white"]
        imported_sample_count = database.dem_model_samples()

        game_id, is_new = database.luu_game({
            "created_at": "2026-01-01",
            "source": "PLAYED",
            "source_hash": "test-hash",
            "player_color": "black",
            "engine_color": "white",
            "winner_color": "white",
            "result": "1-0",
            "reason": "test",
            "move_count": 1,
            "moves": game["records"][:1],
            "positions": [game["records"][0]["position_json"]],
        })
        assert is_new
        record = game["records"][0]
        database.them_contributions(game_id, [{
            "position_key": record["position_key"],
            "move_text": record["move_text"],
            "side": "white",
            "source_type": "PERSONAL",
            "outcome": 1.0,
            "weight": 0.02,
            "move_number": 1,
            "is_opening": True,
        }])
        database.them_model_samples(game_id, [{
            "position_key": record["position_key"],
            "position_json": record["position_json"],
            "move_text": record["move_text"],
            "next_position_json": record["next_position_json"],
            "target": 1.0,
            "source_type": "PERSONAL",
        }])
        database.rebuild_opening_book()
        assert database.dem_model_samples() == imported_sample_count + 1
        assert database.xoa_game(game_id)
        assert database.dem_model_samples() == imported_sample_count
        assert database.dem_history() == 0

        # Imported game + derived rows must be one transaction.  A malformed
        # sample must not leave a duplicate-blocking games row behind.
        try:
            database.luu_game_bundle({
                "source": "GM_PGN",
                "source_hash": "atomic-import-test",
                "result": "1-0",
            }, [], [{}])
            assert False, "Expected malformed bundled sample to fail"
        except KeyError:
            pass
        with database.ket_noi() as connection:
            incomplete = connection.execute(
                "SELECT COUNT(*) AS count FROM games WHERE source_hash = ?",
                ("atomic-import-test",),
            ).fetchone()["count"]
        assert incomplete == 0

        model_path = Path(temp_dir) / "caissa_jepa.npz"
        model = caissajepa(model_path, True)
        position = json_thanh_snapshot(record["position_json"])
        next_position = json_thanh_snapshot(record["next_position_json"])
        engine = vitriengine(position, 0.02)
        legal = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
        move = text_thanh_move(record["move_text"], position["turn"])
        negative_move = next(item for item in legal if item != move)
        engine.thuc_hien_nuoc_di(negative_move)
        negative = {
            "board": engine.board.copy(),
            "turn": engine.turn,
            "castling_rights": engine.castling_rights.copy(),
            "en_passant_target": engine.en_passant_target,
            "halfmove_clock": engine.halfmove_clock,
            "position_counts": {},
        }
        metrics = model.train_batch([{
            "position": position,
            "move": move,
            "next_position": next_position,
            "future2": next_position,
            "future4": next_position,
            "negative": negative,
            "target": 1.0,
        }], 0.001)
        assert all(math.isfinite(float(value)) for value in metrics.values())
        model.save()
        loaded = caissajepa(model_path, False)
        assert loaded.trained_steps == 1
        _, priors, entropy = loaded.score_legal_moves(position, legal)
        assert abs(sum(priors) - 1.0) < 1e-5 and math.isfinite(entropy)
        mcts = caissamcts(position, loaded, 0.05).tim_nuoc_di()
        assert mcts["move"] in legal and mcts["simulations"] > 0

        worker = engineworker(
            position,
            0.12,
            7,
            threading.Event(),
            str(model_path),
            move,
        )
        outputs = []
        worker.ket_qua.connect(outputs.append)
        worker.chay()
        assert outputs[0]["move"] in legal
        assert outputs[0]["source"] == "CAISSA_JEPA_MCTS_ALPHA"


def main():
    parser = pgnparser()
    test_rules_and_hash(parser)
    test_parser_database_and_model(parser)
    print("ALL CORE TESTS PASSED")


if __name__ == "__main__":
    main()
