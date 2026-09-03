"""Headless GUI/controller parity test for the exact chess state machine."""

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from main import boardwidget, vitriengine


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
