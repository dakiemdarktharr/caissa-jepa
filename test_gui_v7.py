"""Headless GUI/controller parity test for the exact chess state machine."""

import os
import tempfile
import threading
import json
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from fen_dataset_tool import FenDatasetBuilder
from main import boardwidget, monitorwidget, trainworker, vitriengine


GM_PGN = '''[Event "GUI train sample"]
[White "Alpha"]
[Black "Beta"]
[WhiteTitle "GM"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0
'''


class GuiParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_controller_applies_the_same_state_transitions_as_engine(self):
        with tempfile.TemporaryDirectory() as temporary:
            board = boardwidget(project_dir=Path(temporary))
            board.dang_chon_mau = False
            board.player_color = "white"
            board.engine_color = "black"
            engine = vitriengine(board.tao_snapshot_engine(), 0.02)
            for ply in range(12):
                legal_moves = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
                move = legal_moves[(ply * 7) % len(legal_moves)]
                is_engine_move = engine.turn == board.engine_color
                applied = board.move_piece(
                    move[0], move[1], is_engine_move, move[2], None
                )
                self.assertTrue(applied)
                engine.thuc_hien_nuoc_di(move)
                self.assertEqual(board.board, engine.board)
                self.assertEqual(board.turn, engine.turn)
                self.assertEqual(board.castling_rights, engine.castling_rights)
                self.assertEqual(board.en_passant_target, engine.en_passant_target)
                self.assertEqual(board.halfmove_clock, engine.halfmove_clock)
            board.clock_timer.stop()

    def test_gui_trainworker_uses_v7_dataset_and_emits_progress(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "games.pgn"
            source.write_text(GM_PGN, encoding="utf-8")
            dataset = root / "fen_dataset"
            builder = FenDatasetBuilder(
                dataset,
                target_bytes=1024 * 1024,
                shard_bytes=32 * 1024,
                allowed_titles={"GM"},
                only_gm_actions=False,
            )
            builder.ingest_path(source, {"name": "gui-test"})
            builder.close("COMPLETE")

            progress = []
            results = []
            worker = trainworker(
                str(root / "chess_data/chess_engine.db"),
                str(root / "chess_data/caissa_a_jepa_v7.npz"),
                threading.Event(),
                str(dataset),
                1,
                batch_size=2,
                latent_size=16,
            )
            worker.tien_do.connect(progress.append)
            worker.ket_qua.connect(results.append)
            worker.chay()

            self.assertTrue(progress)
            self.assertEqual(len(results), 1)
            self.assertNotIn("error", results[0])
            self.assertTrue((root / "chess_data/caissa_a_jepa_v7.npz").exists())
            report = json.loads(
                (root / "chess_data/caissa_a_jepa_v7.training.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["status"], "COMPLETE")
            self.assertEqual(report["architecture"], "adversarial-jepa")

            board = boardwidget(project_dir=root)
            monitor = monitorwidget(board)
            monitor.nhan_train(progress[-1])
            self.assertEqual(monitor.checkpoint_steps, report["trained_steps"])
            monitor.close()
            board.clock_timer.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
