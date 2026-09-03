import hashlib
import json
import math
import random
import re
import sqlite3
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

try:
    import numpy as np
except ImportError:
    np = None

from PySide6.QtCore import (
    QObject,
    Qt,
    QRect,
    QRectF,
    QThread,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QWidget,
)


APP_BUILD = "CAISSA-JEPA-v7"


class het_thoi_gian_search(Exception):
    pass


class vitriengine:
    zobrist_piece = None
    zobrist_turn = None
    zobrist_castling = None
    zobrist_en_passant = None

    def __init__(
        self,
        snapshot,
        gioi_han_giay=5.0,
        stop_event=None,
        progress_callback=None,
    ):
        self.board = snapshot["board"].copy()
        self.turn = snapshot["turn"]
        self.castling_rights = snapshot["castling_rights"].copy()
        self.en_passant_target = snapshot["en_passant_target"]
        self.halfmove_clock = snapshot.get("halfmove_clock", 0)
        self.position_counts = snapshot.get("position_counts", {}).copy()

        self.gioi_han_giay = max(0.02, float(gioi_han_giay))
        self.stop_event = stop_event
        self.progress_callback = progress_callback
        self.thoi_gian_bat_dau = 0.0
        self.thoi_gian_ket_thuc = 0.0
        self.thoi_gian_phat_tien_do = 0.0
        self.search_root_color = self.turn
        self.live_score_white = 0.0
        self.live_best_move = None

        self.so_node = 0
        self.so_qnode = 0
        self.depth_hoan_thanh = 0
        self.pv_table = {}
        self.pv_tot_nhat = []
        self.transposition_table = {}
        self.tt_max_entries = 150000
        self.tt_hits = 0
        self.beta_cutoffs = 0
        self.killer_moves = {}
        self.history_heuristic = {}

        self.MATE_SCORE = 100000
        self.INFINITY = 200000

        self.piece_value = {
            "P": 100,
            "N": 320,
            "B": 330,
            "R": 500,
            "Q": 900,
            "K": 0,
        }

        self.khoi_tao_zobrist()
        self.zobrist_hash = self.tinh_zobrist_hash()

    @classmethod
    def khoi_tao_zobrist(cls):
        if cls.zobrist_piece is not None:
            return

        random_generator = random.Random(20260805)
        pieces = "PNBRQKpnbrqk"
        cls.zobrist_piece = {
            piece: [random_generator.getrandbits(64) for _ in range(64)]
            for piece in pieces
        }
        cls.zobrist_turn = random_generator.getrandbits(64)
        cls.zobrist_castling = {
            key: random_generator.getrandbits(64)
            for key in (
                "white_kingside",
                "white_queenside",
                "black_kingside",
                "black_queenside",
            )
        }
        cls.zobrist_en_passant = [
            random_generator.getrandbits(64)
            for _ in range(8)
        ]

    def hash_thanh_phan_trang_thai(
        self,
        turn,
        castling_rights,
        en_passant_target,
    ):
        hash_value = 0

        if turn == "black":
            hash_value ^= self.zobrist_turn

        for key, is_available in castling_rights.items():
            if is_available:
                hash_value ^= self.zobrist_castling[key]

        if en_passant_target is not None:
            hash_value ^= self.zobrist_en_passant[en_passant_target % 8]

        return hash_value

    def tinh_zobrist_hash(self):
        hash_value = 0

        for index, piece in enumerate(self.board):
            if piece != ".":
                hash_value ^= self.zobrist_piece[piece][index]

        hash_value ^= self.hash_thanh_phan_trang_thai(
            self.turn,
            self.castling_rights,
            self.en_passant_target,
        )

        return hash_value

    def mau_quan_co(self, piece):
        if piece == ".":
            return None

        if piece.isupper():
            return "white"

        return "black"

    def mau_doi_thu(self, color):
        if color == "white":
            return "black"

        return "white"

    def tim_vi_tri_vua(self, color):
        if color == "white":
            king_piece = "K"
        else:
            king_piece = "k"

        for index, piece in enumerate(self.board):
            if piece == king_piece:
                return index

        return None

    def is_square_attacked(self, square_index, attacker_color):
        row = square_index // 8
        col = square_index % 8

        if attacker_color == "white":
            pawn_piece = "P"
            pawn_row = row + 1
        else:
            pawn_piece = "p"
            pawn_row = row - 1

        if 0 <= pawn_row <= 7:
            for pawn_col in (col - 1, col + 1):
                if 0 <= pawn_col <= 7:
                    pawn_index = pawn_row * 8 + pawn_col

                    if self.board[pawn_index] == pawn_piece:
                        return True

        knight_piece = "N" if attacker_color == "white" else "n"
        knight_offsets = (
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1),
        )

        for row_step, col_step in knight_offsets:
            test_row = row + row_step
            test_col = col + col_step

            if 0 <= test_row <= 7 and 0 <= test_col <= 7:
                test_index = test_row * 8 + test_col

                if self.board[test_index] == knight_piece:
                    return True

        bishop_piece = "B" if attacker_color == "white" else "b"
        rook_piece = "R" if attacker_color == "white" else "r"
        queen_piece = "Q" if attacker_color == "white" else "q"

        for row_step, col_step in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            test_row = row + row_step
            test_col = col + col_step

            while 0 <= test_row <= 7 and 0 <= test_col <= 7:
                test_piece = self.board[test_row * 8 + test_col]

                if test_piece != ".":
                    if test_piece in (bishop_piece, queen_piece):
                        return True
                    break

                test_row += row_step
                test_col += col_step

        for row_step, col_step in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            test_row = row + row_step
            test_col = col + col_step

            while 0 <= test_row <= 7 and 0 <= test_col <= 7:
                test_piece = self.board[test_row * 8 + test_col]

                if test_piece != ".":
                    if test_piece in (rook_piece, queen_piece):
                        return True
                    break

                test_row += row_step
                test_col += col_step

        king_piece = "K" if attacker_color == "white" else "k"

        for row_step in (-1, 0, 1):
            for col_step in (-1, 0, 1):
                if row_step == 0 and col_step == 0:
                    continue

                test_row = row + row_step
                test_col = col + col_step

                if 0 <= test_row <= 7 and 0 <= test_col <= 7:
                    test_index = test_row * 8 + test_col

                    if self.board[test_index] == king_piece:
                        return True

        return False

    def is_king_in_check(self, color):
        king_index = self.tim_vi_tri_vua(color)

        if king_index is None:
            return False

        return self.is_square_attacked(
            king_index,
            self.mau_doi_thu(color),
        )

    def tao_nuoc_phong_cap(self, from_index, to_index, color):
        if color == "white":
            promotion_pieces = ("Q", "R", "B", "N")
        else:
            promotion_pieces = ("q", "r", "b", "n")

        return [
            (from_index, to_index, piece)
            for piece in promotion_pieces
        ]

    def tao_cac_nuoc_di_pseudo(self, color):
        moves = []

        for from_index, piece in enumerate(self.board):
            if self.mau_quan_co(piece) != color:
                continue

            row = from_index // 8
            col = from_index % 8

            if piece in ("P", "p"):
                if color == "white":
                    row_step = -1
                    start_row = 6
                    promotion_row = 0
                else:
                    row_step = 1
                    start_row = 1
                    promotion_row = 7

                next_row = row + row_step

                if 0 <= next_row <= 7:
                    to_index = next_row * 8 + col

                    if self.board[to_index] == ".":
                        if next_row == promotion_row:
                            moves.extend(
                                self.tao_nuoc_phong_cap(
                                    from_index,
                                    to_index,
                                    color,
                                )
                            )
                        else:
                            moves.append((from_index, to_index, None))

                            if row == start_row:
                                double_row = row + row_step * 2
                                double_index = double_row * 8 + col

                                if self.board[double_index] == ".":
                                    moves.append(
                                        (from_index, double_index, None)
                                    )

                    for col_step in (-1, 1):
                        capture_col = col + col_step

                        if capture_col < 0 or capture_col > 7:
                            continue

                        capture_index = next_row * 8 + capture_col
                        captured_piece = self.board[capture_index]
                        captured_color = self.mau_quan_co(captured_piece)

                        if captured_color == self.mau_doi_thu(color):
                            if captured_piece in ("K", "k"):
                                continue

                            if next_row == promotion_row:
                                moves.extend(
                                    self.tao_nuoc_phong_cap(
                                        from_index,
                                        capture_index,
                                        color,
                                    )
                                )
                            else:
                                moves.append(
                                    (from_index, capture_index, None)
                                )

                        elif capture_index == self.en_passant_target:
                            captured_pawn_index = capture_index - row_step * 8
                            expected_pawn = "p" if color == "white" else "P"

                            if self.board[captured_pawn_index] == expected_pawn:
                                moves.append(
                                    (from_index, capture_index, None)
                                )

                continue

            if piece in ("N", "n"):
                offsets = (
                    (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                    (1, -2), (1, 2), (2, -1), (2, 1),
                )

                for row_step, col_step in offsets:
                    to_row = row + row_step
                    to_col = col + col_step

                    if 0 <= to_row <= 7 and 0 <= to_col <= 7:
                        to_index = to_row * 8 + to_col
                        to_piece = self.board[to_index]

                        if self.mau_quan_co(to_piece) == color:
                            continue
                        if to_piece in ("K", "k"):
                            continue

                        moves.append((from_index, to_index, None))

                continue

            if piece in ("B", "b"):
                directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
            elif piece in ("R", "r"):
                directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
            elif piece in ("Q", "q"):
                directions = (
                    (-1, -1), (-1, 1), (1, -1), (1, 1),
                    (-1, 0), (1, 0), (0, -1), (0, 1),
                )
            else:
                directions = None

            if directions is not None:
                for row_step, col_step in directions:
                    to_row = row + row_step
                    to_col = col + col_step

                    while 0 <= to_row <= 7 and 0 <= to_col <= 7:
                        to_index = to_row * 8 + to_col
                        to_piece = self.board[to_index]
                        to_color = self.mau_quan_co(to_piece)

                        if to_color == color:
                            break
                        if to_piece in ("K", "k"):
                            break

                        moves.append((from_index, to_index, None))

                        if to_piece != ".":
                            break

                        to_row += row_step
                        to_col += col_step

                continue

            if piece in ("K", "k"):
                for row_step in (-1, 0, 1):
                    for col_step in (-1, 0, 1):
                        if row_step == 0 and col_step == 0:
                            continue

                        to_row = row + row_step
                        to_col = col + col_step

                        if 0 <= to_row <= 7 and 0 <= to_col <= 7:
                            to_index = to_row * 8 + to_col
                            to_piece = self.board[to_index]

                            if self.mau_quan_co(to_piece) == color:
                                continue
                            if to_piece in ("K", "k"):
                                continue

                            moves.append((from_index, to_index, None))

                if color == "white" and from_index == 60:
                    if self.castling_rights["white_kingside"]:
                        if self.board[61] == "." and self.board[62] == ".":
                            if self.board[63] == "R":
                                if not self.is_square_attacked(60, "black"):
                                    if not self.is_square_attacked(61, "black"):
                                        if not self.is_square_attacked(62, "black"):
                                            moves.append((60, 62, None))

                    if self.castling_rights["white_queenside"]:
                        if self.board[57] == ".":
                            if self.board[58] == "." and self.board[59] == ".":
                                if self.board[56] == "R":
                                    if not self.is_square_attacked(60, "black"):
                                        if not self.is_square_attacked(59, "black"):
                                            if not self.is_square_attacked(58, "black"):
                                                moves.append((60, 58, None))

                if color == "black" and from_index == 4:
                    if self.castling_rights["black_kingside"]:
                        if self.board[5] == "." and self.board[6] == ".":
                            if self.board[7] == "r":
                                if not self.is_square_attacked(4, "white"):
                                    if not self.is_square_attacked(5, "white"):
                                        if not self.is_square_attacked(6, "white"):
                                            moves.append((4, 6, None))

                    if self.castling_rights["black_queenside"]:
                        if self.board[1] == ".":
                            if self.board[2] == "." and self.board[3] == ".":
                                if self.board[0] == "r":
                                    if not self.is_square_attacked(4, "white"):
                                        if not self.is_square_attacked(3, "white"):
                                            if not self.is_square_attacked(2, "white"):
                                                moves.append((4, 2, None))

        return moves

    def en_passant_co_hieu_luc(self):
        if self.en_passant_target is None:
            return "-"

        target = self.en_passant_target
        row = target // 8
        col = target % 8

        if self.turn == "white":
            pawn_row = row + 1
            pawn_piece = "P"
        else:
            pawn_row = row - 1
            pawn_piece = "p"

        for pawn_col in (col - 1, col + 1):
            if 0 <= pawn_row <= 7 and 0 <= pawn_col <= 7:
                pawn_index = pawn_row * 8 + pawn_col

                if self.board[pawn_index] == pawn_piece:
                    return str(target)

        return "-"

    def tao_key_position(self):
        castling_key = ""

        if self.castling_rights["white_kingside"]:
            castling_key += "K"
        if self.castling_rights["white_queenside"]:
            castling_key += "Q"
        if self.castling_rights["black_kingside"]:
            castling_key += "k"
        if self.castling_rights["black_queenside"]:
            castling_key += "q"

        if castling_key == "":
            castling_key = "-"

        return (
            "".join(self.board),
            self.turn,
            castling_key,
            self.en_passant_co_hieu_luc(),
        )

    def cap_nhat_quyen_nhap_thanh(self, from_index, capture_index, moving_piece, captured_piece):
        if moving_piece == "K":
            self.castling_rights["white_kingside"] = False
            self.castling_rights["white_queenside"] = False
        elif moving_piece == "k":
            self.castling_rights["black_kingside"] = False
            self.castling_rights["black_queenside"] = False
        elif moving_piece == "R":
            if from_index == 63:
                self.castling_rights["white_kingside"] = False
            elif from_index == 56:
                self.castling_rights["white_queenside"] = False
        elif moving_piece == "r":
            if from_index == 7:
                self.castling_rights["black_kingside"] = False
            elif from_index == 0:
                self.castling_rights["black_queenside"] = False

        if captured_piece == "R":
            if capture_index == 63:
                self.castling_rights["white_kingside"] = False
            elif capture_index == 56:
                self.castling_rights["white_queenside"] = False
        elif captured_piece == "r":
            if capture_index == 7:
                self.castling_rights["black_kingside"] = False
            elif capture_index == 0:
                self.castling_rights["black_queenside"] = False

    def thuc_hien_nuoc_di(self, move):
        from_index, to_index, promotion_piece = move
        moving_piece = self.board[from_index]
        captured_piece = self.board[to_index]
        capture_index = to_index

        affected_indexes = {from_index, to_index}

        is_en_passant = False

        if moving_piece in ("P", "p"):
            if to_index == self.en_passant_target:
                if captured_piece == ".":
                    is_en_passant = True

                    if moving_piece == "P":
                        capture_index = to_index + 8
                    else:
                        capture_index = to_index - 8

                    captured_piece = self.board[capture_index]
                    affected_indexes.add(capture_index)

        is_castling = moving_piece in ("K", "k") and abs(to_index - from_index) == 2
        rook_from = None
        rook_to = None

        if is_castling:
            if to_index > from_index:
                rook_from = from_index + 3
                rook_to = from_index + 1
            else:
                rook_from = from_index - 4
                rook_to = from_index - 1

            affected_indexes.add(rook_from)
            affected_indexes.add(rook_to)

        undo_info = {
            "old_squares": {
                index: self.board[index]
                for index in affected_indexes
            },
            "castling_rights": self.castling_rights.copy(),
            "en_passant_target": self.en_passant_target,
            "halfmove_clock": self.halfmove_clock,
            "turn": self.turn,
            "zobrist_hash": self.zobrist_hash,
            "new_position_key": None,
        }

        self.board[from_index] = "."

        if is_en_passant:
            self.board[capture_index] = "."

        if is_castling:
            rook_piece = self.board[rook_from]
            self.board[rook_from] = "."
            self.board[rook_to] = rook_piece

        if promotion_piece is not None:
            self.board[to_index] = promotion_piece
        else:
            self.board[to_index] = moving_piece

        self.cap_nhat_quyen_nhap_thanh(
            from_index,
            capture_index,
            moving_piece,
            captured_piece,
        )

        self.en_passant_target = None

        if moving_piece in ("P", "p"):
            if abs(to_index - from_index) == 16:
                self.en_passant_target = (from_index + to_index) // 2

        if moving_piece in ("P", "p") or captured_piece != ".":
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        self.turn = self.mau_doi_thu(self.turn)

        new_key = self.tao_key_position()
        undo_info["new_position_key"] = new_key
        self.position_counts[new_key] = self.position_counts.get(new_key, 0) + 1

        new_hash = undo_info["zobrist_hash"]
        new_hash ^= self.hash_thanh_phan_trang_thai(
            undo_info["turn"],
            undo_info["castling_rights"],
            undo_info["en_passant_target"],
        )

        for index, old_piece in undo_info["old_squares"].items():
            if old_piece != ".":
                new_hash ^= self.zobrist_piece[old_piece][index]

            new_piece = self.board[index]

            if new_piece != ".":
                new_hash ^= self.zobrist_piece[new_piece][index]

        new_hash ^= self.hash_thanh_phan_trang_thai(
            self.turn,
            self.castling_rights,
            self.en_passant_target,
        )
        self.zobrist_hash = new_hash

        return undo_info

    def hoan_tac_nuoc_di(self, undo_info):
        new_key = undo_info["new_position_key"]

        if new_key is not None:
            new_count = self.position_counts.get(new_key, 0) - 1

            if new_count <= 0:
                self.position_counts.pop(new_key, None)
            else:
                self.position_counts[new_key] = new_count

        for index, piece in undo_info["old_squares"].items():
            self.board[index] = piece

        self.castling_rights = undo_info["castling_rights"]
        self.en_passant_target = undo_info["en_passant_target"]
        self.halfmove_clock = undo_info["halfmove_clock"]
        self.turn = undo_info["turn"]
        self.zobrist_hash = undo_info["zobrist_hash"]

    def lay_tat_ca_nuoc_di_hop_le(self, color=None):
        if color is None:
            color = self.turn

        legal_moves = []

        for move in self.tao_cac_nuoc_di_pseudo(color):
            undo_info = self.thuc_hien_nuoc_di(move)
            king_in_check = self.is_king_in_check(color)
            self.hoan_tac_nuoc_di(undo_info)

            if king_in_check == False:
                legal_moves.append(move)

        return legal_moves

    def is_nuoc_an_quan(self, move):
        from_index, to_index, promotion_piece = move
        moving_piece = self.board[from_index]

        if self.board[to_index] != ".":
            return True

        if moving_piece in ("P", "p"):
            if to_index == self.en_passant_target:
                if from_index % 8 != to_index % 8:
                    return True

        return promotion_piece is not None

    def is_nuoc_yen_tinh(self, move):
        return self.is_nuoc_an_quan(move) == False and move[2] is None

    def is_nuoc_chieu(self, move):
        undo_info = self.thuc_hien_nuoc_di(move)

        try:
            return self.is_king_in_check(self.turn)
        finally:
            self.hoan_tac_nuoc_di(undo_info)

    def diem_sap_xep_nuoc_di(
        self,
        move,
        pv_move=None,
        tt_move=None,
        ply=0,
    ):
        from_index, to_index, promotion_piece = move
        moving_piece = self.board[from_index]
        captured_piece = self.board[to_index]
        score = 0

        if move == tt_move:
            score += 2000000

        if move == pv_move:
            score += 1500000

        if captured_piece != ".":
            score += 10000
            score += self.piece_value[captured_piece.upper()] * 10
            score -= self.piece_value[moving_piece.upper()]
        elif self.is_nuoc_an_quan(move):
            score += 10000 + self.piece_value["P"] * 10

        if promotion_piece is not None:
            score += 8000 + self.piece_value[promotion_piece.upper()]

        if moving_piece in ("K", "k"):
            if abs(to_index - from_index) == 2:
                score += 300

        if self.is_nuoc_yen_tinh(move):
            killer_list = self.killer_moves.get(ply, [])

            if len(killer_list) > 0 and move == killer_list[0]:
                score += 6500
            elif len(killer_list) > 1 and move == killer_list[1]:
                score += 5500

            history_key = (moving_piece, from_index, to_index)
            score += min(
                4500,
                self.history_heuristic.get(history_key, 0),
            )

            if ply <= 2 and self.is_nuoc_chieu(move):
                score += 7000

        return score

    def sap_xep_nuoc_di(
        self,
        moves,
        pv_move=None,
        tt_move=None,
        ply=0,
    ):
        return sorted(
            moves,
            key=lambda move: self.diem_sap_xep_nuoc_di(
                move,
                pv_move,
                tt_move,
                ply,
            ),
            reverse=True,
        )

    def cap_nhat_killer_history(self, move, depth, ply):
        if self.is_nuoc_yen_tinh(move) == False:
            return

        killer_list = self.killer_moves.setdefault(ply, [])

        if move not in killer_list:
            killer_list.insert(0, move)
            del killer_list[2:]

        moving_piece = self.board[move[0]]
        history_key = (moving_piece, move[0], move[1])
        self.history_heuristic[history_key] = (
            self.history_heuristic.get(history_key, 0)
            + depth * depth
        )

    def score_vao_tt(self, score, ply):
        if score >= self.MATE_SCORE - 1000:
            return score + ply
        if score <= -self.MATE_SCORE + 1000:
            return score - ply

        return score

    def score_tu_tt(self, score, ply):
        if score >= self.MATE_SCORE - 1000:
            return score - ply
        if score <= -self.MATE_SCORE + 1000:
            return score + ply

        return score

    def luu_transposition(self, depth, score, flag, best_move, ply):
        current_key = self.tao_key_position()

        if self.position_counts.get(current_key, 0) > 1:
            return

        if len(self.transposition_table) >= self.tt_max_entries:
            self.transposition_table.clear()

        old_entry = self.transposition_table.get(self.zobrist_hash)

        if old_entry is None or depth >= old_entry["depth"]:
            self.transposition_table[self.zobrist_hash] = {
                "depth": depth,
                "score": self.score_vao_tt(score, ply),
                "flag": flag,
                "best_move": best_move,
            }

    def diem_vi_tri_piece(self, piece, index, endgame):
        row = index // 8
        col = index % 8

        if piece.isupper():
            relative_rank = 7 - row
        else:
            relative_rank = row

        center_distance = abs(3.5 - row) + abs(3.5 - col)
        piece_type = piece.upper()

        if piece_type == "P":
            score = relative_rank * 7

            if col in (3, 4):
                score += 6

            return score

        if piece_type == "N":
            score = int(30 - center_distance * 8)

            if row in (0, 7) or col in (0, 7):
                score -= 15

            return score

        if piece_type == "B":
            return int(18 - center_distance * 4)

        if piece_type == "R":
            if relative_rank == 6:
                return 20

            return 0

        if piece_type == "Q":
            return int(8 - center_distance * 2)

        if piece_type == "K":
            if endgame:
                return int(28 - center_distance * 7)

            score = int(center_distance * 5)

            if index in (62, 58, 6, 2):
                score += 25

            return score

        return 0

    def tinh_cau_truc_tot(self, color):
        pawn_piece = "P" if color == "white" else "p"
        opponent_pawn = "p" if color == "white" else "P"
        pawn_indexes = [
            index
            for index, piece in enumerate(self.board)
            if piece == pawn_piece
        ]

        pawn_files = [0] * 8

        for index in pawn_indexes:
            pawn_files[index % 8] += 1

        score = 0

        for count in pawn_files:
            if count > 1:
                score -= (count - 1) * 15

        for index in pawn_indexes:
            row = index // 8
            col = index % 8

            left_empty = col == 0 or pawn_files[col - 1] == 0
            right_empty = col == 7 or pawn_files[col + 1] == 0

            if left_empty and right_empty:
                score -= 12

            is_passed = True

            for opponent_index, piece in enumerate(self.board):
                if piece != opponent_pawn:
                    continue

                opponent_row = opponent_index // 8
                opponent_col = opponent_index % 8

                if abs(opponent_col - col) > 1:
                    continue

                if color == "white" and opponent_row < row:
                    is_passed = False
                    break

                if color == "black" and opponent_row > row:
                    is_passed = False
                    break

            if is_passed:
                if color == "white":
                    relative_rank = 7 - row
                else:
                    relative_rank = row

                score += relative_rank * 10

        return score

    def tinh_rook_file(self, color):
        rook_piece = "R" if color == "white" else "r"
        own_pawn = "P" if color == "white" else "p"
        opponent_pawn = "p" if color == "white" else "P"
        score = 0

        for index, piece in enumerate(self.board):
            if piece != rook_piece:
                continue

            col = index % 8
            has_own_pawn = False
            has_opponent_pawn = False

            for row in range(8):
                file_piece = self.board[row * 8 + col]

                if file_piece == own_pawn:
                    has_own_pawn = True
                elif file_piece == opponent_pawn:
                    has_opponent_pawn = True

            if has_own_pawn == False:
                if has_opponent_pawn:
                    score += 8
                else:
                    score += 15

        return score

    def tinh_an_toan_vua(self, color):
        king_index = self.tim_vi_tri_vua(color)

        if king_index is None:
            return -10000

        king_row = king_index // 8
        king_col = king_index % 8
        pawn_piece = "P" if color == "white" else "p"
        row_step = -1 if color == "white" else 1
        shield_row = king_row + row_step
        score = 0

        if 0 <= shield_row <= 7:
            for col in (king_col - 1, king_col, king_col + 1):
                if 0 <= col <= 7:
                    if self.board[shield_row * 8 + col] == pawn_piece:
                        score += 10

        return score

    def tinh_evaluation(self):
        non_pawn_material = 0

        for piece in self.board:
            if piece.upper() in ("N", "B", "R", "Q"):
                non_pawn_material += self.piece_value[piece.upper()]

        endgame = non_pawn_material <= 2600
        score = 0
        white_bishops = 0
        black_bishops = 0

        for index, piece in enumerate(self.board):
            if piece == ".":
                continue

            piece_score = self.piece_value[piece.upper()]
            piece_score += self.diem_vi_tri_piece(piece, index, endgame)

            if piece.isupper():
                score += piece_score
            else:
                score -= piece_score

            if piece == "B":
                white_bishops += 1
            elif piece == "b":
                black_bishops += 1

        if white_bishops >= 2:
            score += 25
        if black_bishops >= 2:
            score -= 25

        score += self.tinh_cau_truc_tot("white")
        score -= self.tinh_cau_truc_tot("black")
        score += self.tinh_rook_file("white")
        score -= self.tinh_rook_file("black")

        if endgame == False:
            score += self.tinh_an_toan_vua("white")
            score -= self.tinh_an_toan_vua("black")

        if self.turn == "white":
            score += 8
        else:
            score -= 8

        return score

    def tinh_evaluation_theo_luot(self):
        score = self.tinh_evaluation()

        if self.turn == "white":
            return score

        return -score

    def kiem_tra_dung_search(self):
        if self.stop_event is not None:
            if self.stop_event.is_set():
                raise het_thoi_gian_search()

        if self.so_node % 128 == 0:
            self.phat_tien_do_search()

            if time.perf_counter() >= self.thoi_gian_ket_thuc:
                raise het_thoi_gian_search()

    def phat_tien_do_search(self, force=False):
        if self.progress_callback is None:
            return

        current_time = time.perf_counter()

        if force == False:
            if current_time - self.thoi_gian_phat_tien_do < 0.20:
                return

        self.thoi_gian_phat_tien_do = current_time
        elapsed = max(0.0, current_time - self.thoi_gian_bat_dau)

        if elapsed > 0:
            nps = int(self.so_node / elapsed)
        else:
            nps = 0

        progress = {
            "stage": "ALPHA_BETA",
            "depth": self.depth_hoan_thanh,
            "nodes": self.so_node,
            "qnodes": self.so_qnode,
            "time": round(elapsed, 3),
            "time_limit": round(self.gioi_han_giay, 3),
            "nps": nps,
            "tt_hits": self.tt_hits,
            "tt_size": len(self.transposition_table),
            "beta_cutoffs": self.beta_cutoffs,
            "score_white": round(self.live_score_white, 2),
            "move": self.live_best_move,
            "pv": self.pv_tot_nhat[:12],
        }

        try:
            self.progress_callback(progress)
        except Exception:
            pass

    def is_draw_search(self):
        key = self.tao_key_position()

        if self.position_counts.get(key, 0) >= 3:
            return True

        if self.is_thieu_quan_search():
            return True

        return False

    def is_thieu_quan_search(self):
        non_king_pieces = []

        for index, piece in enumerate(self.board):
            if piece == "." or piece in ("K", "k"):
                continue

            non_king_pieces.append((index, piece))

        if len(non_king_pieces) == 0:
            return True

        if len(non_king_pieces) == 1:
            return non_king_pieces[0][1] in ("B", "b", "N", "n")

        if len(non_king_pieces) == 2:
            first_index, first_piece = non_king_pieces[0]
            second_index, second_piece = non_king_pieces[1]

            if first_piece in ("B", "b") and second_piece in ("B", "b"):
                if self.mau_quan_co(first_piece) != self.mau_quan_co(second_piece):
                    first_square_color = (
                        (first_index // 8) + (first_index % 8)
                    ) % 2
                    second_square_color = (
                        (second_index // 8) + (second_index % 8)
                    ) % 2

                    return first_square_color == second_square_color

        return False

    def quiescence(self, alpha, beta, ply, q_depth=0):
        self.so_node += 1
        self.so_qnode += 1
        self.kiem_tra_dung_search()

        if self.is_draw_search():
            return 0

        in_check = self.is_king_in_check(self.turn)
        all_moves = self.lay_tat_ca_nuoc_di_hop_le(self.turn)

        if len(all_moves) == 0:
            if in_check:
                return -self.MATE_SCORE + ply

            return 0

        if q_depth >= 8:
            return self.tinh_evaluation_theo_luot()

        if in_check:
            moves = all_moves
        else:
            stand_pat = self.tinh_evaluation_theo_luot()

            if stand_pat >= beta:
                return beta

            if stand_pat > alpha:
                alpha = stand_pat

            moves = [
                move
                for move in all_moves
                if self.is_nuoc_an_quan(move)
            ]

            if len(moves) == 0:
                return alpha

        moves = self.sap_xep_nuoc_di(moves, ply=ply)

        for move in moves:
            undo_info = self.thuc_hien_nuoc_di(move)

            try:
                score = -self.quiescence(
                    -beta,
                    -alpha,
                    ply + 1,
                    q_depth + 1,
                )
            finally:
                self.hoan_tac_nuoc_di(undo_info)

            if score >= beta:
                return beta

            if score > alpha:
                alpha = score

        return alpha

    def negamax(self, depth, alpha, beta, ply):
        self.so_node += 1
        self.kiem_tra_dung_search()
        self.pv_table[ply] = []
        alpha_original = alpha

        if self.is_draw_search():
            return 0

        if depth <= 0:
            return self.quiescence(alpha, beta, ply)

        current_key = self.tao_key_position()
        can_use_tt = self.position_counts.get(current_key, 0) <= 1
        tt_entry = self.transposition_table.get(self.zobrist_hash)
        tt_move = None

        if tt_entry is not None:
            tt_move = tt_entry["best_move"]

            if can_use_tt and tt_entry["depth"] >= depth:
                self.tt_hits += 1
                tt_score = self.score_tu_tt(tt_entry["score"], ply)

                if tt_entry["flag"] == "EXACT":
                    return tt_score
                if tt_entry["flag"] == "LOWER":
                    alpha = max(alpha, tt_score)
                elif tt_entry["flag"] == "UPPER":
                    beta = min(beta, tt_score)

                if alpha >= beta:
                    return tt_score

        moves = self.lay_tat_ca_nuoc_di_hop_le(self.turn)

        if len(moves) == 0:
            if self.is_king_in_check(self.turn):
                mate_score = -self.MATE_SCORE + ply
                self.luu_transposition(
                    depth,
                    mate_score,
                    "EXACT",
                    None,
                    ply,
                )
                return mate_score

            self.luu_transposition(depth, 0, "EXACT", None, ply)
            return 0

        pv_move = None

        if ply < len(self.pv_tot_nhat):
            pv_move = self.pv_tot_nhat[ply]

        moves = self.sap_xep_nuoc_di(
            moves,
            pv_move,
            tt_move,
            ply,
        )
        best_move = None

        for move in moves:
            undo_info = self.thuc_hien_nuoc_di(move)

            try:
                score = -self.negamax(
                    depth - 1,
                    -beta,
                    -alpha,
                    ply + 1,
                )
            finally:
                self.hoan_tac_nuoc_di(undo_info)

            if score > alpha:
                alpha = score
                best_move = move
                self.pv_table[ply] = [move] + self.pv_table.get(
                    ply + 1,
                    [],
                )

            if score >= beta:
                self.beta_cutoffs += 1
                self.cap_nhat_killer_history(move, depth, ply)
                self.luu_transposition(
                    depth,
                    score,
                    "LOWER",
                    move,
                    ply,
                )
                return score

        if alpha > alpha_original:
            flag = "EXACT"
        else:
            flag = "UPPER"

        self.luu_transposition(
            depth,
            alpha,
            flag,
            best_move,
            ply,
        )

        return alpha

    def tim_nuoc_di_tot_nhat(self, preferred_move=None):
        self.thoi_gian_bat_dau = time.perf_counter()
        self.thoi_gian_ket_thuc = (
            self.thoi_gian_bat_dau + self.gioi_han_giay
        )

        root_color = self.turn
        self.search_root_color = root_color
        self.live_score_white = 0.0
        self.live_best_move = None
        root_moves = self.lay_tat_ca_nuoc_di_hop_le(root_color)

        if len(root_moves) == 0:
            elapsed_time = time.perf_counter() - self.thoi_gian_bat_dau
            return {
                "move": None,
                "score_white": 0.0,
                "depth": 0,
                "nodes": self.so_node,
                "qnodes": self.so_qnode,
                "time": elapsed_time,
                "nps": 0,
                "tt_hits": self.tt_hits,
                "tt_size": len(self.transposition_table),
                "beta_cutoffs": self.beta_cutoffs,
                "pv": [],
            }

        root_moves = self.sap_xep_nuoc_di(root_moves, preferred_move)

        if preferred_move in root_moves:
            best_move = preferred_move
        else:
            best_move = root_moves[0]
        best_score = self.tinh_evaluation_theo_luot()
        best_pv = [best_move]

        for depth in range(1, 65):
            local_best_move = None
            local_best_score = -self.INFINITY
            local_best_pv = []
            alpha = -self.INFINITY
            beta = self.INFINITY

            pv_move = best_move
            ordered_moves = self.sap_xep_nuoc_di(root_moves, pv_move)

            try:
                for move in ordered_moves:
                    self.kiem_tra_dung_search()
                    undo_info = self.thuc_hien_nuoc_di(move)

                    try:
                        score = -self.negamax(
                            depth - 1,
                            -beta,
                            -alpha,
                            1,
                        )
                    finally:
                        self.hoan_tac_nuoc_di(undo_info)

                    if score > local_best_score:
                        local_best_score = score
                        local_best_move = move
                        local_best_pv = [move] + self.pv_table.get(1, [])

                    if score > alpha:
                        alpha = score

            except het_thoi_gian_search:
                break

            if local_best_move is None:
                break

            best_move = local_best_move
            best_score = local_best_score
            best_pv = local_best_pv
            self.pv_tot_nhat = best_pv
            self.depth_hoan_thanh = depth

            if root_color == "white":
                self.live_score_white = best_score / 100.0
            else:
                self.live_score_white = -best_score / 100.0

            self.live_best_move = best_move
            self.luu_transposition(
                depth,
                best_score,
                "EXACT",
                best_move,
                0,
            )
            self.phat_tien_do_search(force=True)

            if abs(best_score) >= self.MATE_SCORE - 100:
                break

        if root_color == "white":
            score_white = best_score / 100.0
        else:
            score_white = -best_score / 100.0

        elapsed_time = time.perf_counter() - self.thoi_gian_bat_dau

        if elapsed_time > 0:
            nps = int(self.so_node / elapsed_time)
        else:
            nps = 0

        return {
            "move": best_move,
            "score_white": round(score_white, 2),
            "depth": self.depth_hoan_thanh,
            "nodes": self.so_node,
            "qnodes": self.so_qnode,
            "time": round(elapsed_time, 3),
            "nps": nps,
            "tt_hits": self.tt_hits,
            "tt_size": len(self.transposition_table),
            "beta_cutoffs": self.beta_cutoffs,
            "pv": best_pv,
        }


def index_thanh_o(index):
    file_text = chr(ord("a") + index % 8)
    rank_text = str(8 - index // 8)
    return file_text + rank_text


def o_thanh_index(square_text):
    if len(square_text) != 2:
        return None

    col = ord(square_text[0].lower()) - ord("a")

    try:
        row = 8 - int(square_text[1])
    except ValueError:
        return None

    if 0 <= row <= 7 and 0 <= col <= 7:
        return row * 8 + col

    return None


def move_thanh_text(move):
    if move is None:
        return ""

    from_index, to_index, promotion_piece = move
    move_text = index_thanh_o(from_index) + index_thanh_o(to_index)

    if promotion_piece is not None:
        move_text += promotion_piece.lower()

    return move_text


def text_thanh_move(move_text, color=None):
    move_text = move_text.strip().lower()

    if len(move_text) not in (4, 5):
        return None

    from_index = o_thanh_index(move_text[:2])
    to_index = o_thanh_index(move_text[2:4])

    if from_index is None or to_index is None:
        return None

    promotion_piece = None

    if len(move_text) == 5:
        promotion_piece = move_text[4]

        if promotion_piece not in "qrbn":
            return None

        if color == "white":
            promotion_piece = promotion_piece.upper()

    return from_index, to_index, promotion_piece


def key_thanh_text(position_key):
    return json.dumps(
        position_key,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def snapshot_thanh_json(snapshot):
    clean_snapshot = {
        "board": "".join(snapshot["board"]),
        "turn": snapshot["turn"],
        "castling_rights": snapshot["castling_rights"],
        "en_passant_target": snapshot["en_passant_target"],
        "halfmove_clock": snapshot.get("halfmove_clock", 0),
    }

    return json.dumps(
        clean_snapshot,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def json_thanh_snapshot(snapshot_json):
    data = json.loads(snapshot_json)

    return {
        "board": list(data["board"]),
        "turn": data["turn"],
        "castling_rights": data["castling_rights"],
        "en_passant_target": data.get("en_passant_target"),
        "halfmove_clock": data.get("halfmove_clock", 0),
        "position_counts": {},
    }


class chessdatabase:
    def __init__(self, database_path=None):
        if database_path is None:
            data_dir = Path(__file__).resolve().parent / "chess_data"
            data_dir.mkdir(parents=True, exist_ok=True)
            database_path = data_dir / "chess_engine.db"

        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.tao_database()

    @contextmanager
    def ket_noi(self):
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def tao_database(self):
        with self.ket_noi() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    source_hash TEXT NOT NULL UNIQUE,
                    player_color TEXT,
                    engine_color TEXT,
                    winner_color TEXT,
                    result TEXT NOT NULL,
                    reason TEXT,
                    move_count INTEGER NOT NULL DEFAULT 0,
                    moves_json TEXT NOT NULL DEFAULT '[]',
                    evals_json TEXT NOT NULL DEFAULT '[]',
                    positions_json TEXT NOT NULL DEFAULT '[]',
                    white_time_ms REAL,
                    black_time_ms REAL,
                    headers_json TEXT NOT NULL DEFAULT '{}',
                    pgn_text TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    position_key TEXT NOT NULL,
                    move_text TEXT NOT NULL,
                    side TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    outcome REAL NOT NULL,
                    weight REAL NOT NULL,
                    move_number INTEGER NOT NULL,
                    is_opening INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
                    UNIQUE(game_id, position_key, move_text)
                );

                CREATE TABLE IF NOT EXISTS opening_book (
                    position_key TEXT NOT NULL,
                    move_text TEXT NOT NULL,
                    side TEXT NOT NULL,
                    gm_count INTEGER NOT NULL,
                    personal_count INTEGER NOT NULL,
                    wins INTEGER NOT NULL,
                    draws INTEGER NOT NULL,
                    losses INTEGER NOT NULL,
                    weight REAL NOT NULL,
                    PRIMARY KEY(position_key, move_text, side)
                );

                CREATE TABLE IF NOT EXISTS corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    position_key TEXT NOT NULL,
                    old_move TEXT NOT NULL,
                    new_move TEXT NOT NULL,
                    eval_before REAL NOT NULL,
                    eval_after REAL NOT NULL,
                    eval_replacement REAL NOT NULL,
                    evaluation_drop REAL NOT NULL,
                    depth INTEGER NOT NULL,
                    search_time REAL NOT NULL,
                    similar_count INTEGER NOT NULL DEFAULT 1,
                    weight REAL NOT NULL DEFAULT 0.1,
                    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS model_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    position_key TEXT NOT NULL,
                    position_json TEXT NOT NULL,
                    move_text TEXT NOT NULL,
                    next_position_json TEXT NOT NULL,
                    future2_json TEXT,
                    future4_json TEXT,
                    target REAL NOT NULL,
                    source_type TEXT NOT NULL,
                    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
                    UNIQUE(game_id, position_key, move_text)
                );

                CREATE INDEX IF NOT EXISTS index_contribution_position
                ON contributions(position_key, side, is_opening);

                CREATE INDEX IF NOT EXISTS index_correction_position
                ON corrections(position_key);

                CREATE INDEX IF NOT EXISTS index_sample_source
                ON model_samples(source_type);
                """
            )

    def luu_game(self, game_data):
        with self.ket_noi() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO games (
                    created_at, source, source_hash,
                    player_color, engine_color, winner_color,
                    result, reason, move_count,
                    moves_json, evals_json, positions_json,
                    white_time_ms, black_time_ms,
                    headers_json, pgn_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    game_data.get("created_at", datetime.now().isoformat()),
                    game_data.get("source", "PLAYED"),
                    game_data["source_hash"],
                    game_data.get("player_color"),
                    game_data.get("engine_color"),
                    game_data.get("winner_color"),
                    game_data.get("result", "*"),
                    game_data.get("reason", ""),
                    game_data.get("move_count", 0),
                    json.dumps(game_data.get("moves", []), ensure_ascii=False),
                    json.dumps(game_data.get("evals", []), ensure_ascii=False),
                    json.dumps(game_data.get("positions", []), ensure_ascii=False),
                    game_data.get("white_time_ms"),
                    game_data.get("black_time_ms"),
                    json.dumps(game_data.get("headers", {}), ensure_ascii=False),
                    game_data.get("pgn_text", ""),
                ),
            )

            if cursor.rowcount > 0:
                return cursor.lastrowid, True

            old_row = connection.execute(
                "SELECT id FROM games WHERE source_hash = ?",
                (game_data["source_hash"],),
            ).fetchone()

            return old_row["id"], False

    def luu_game_bundle(
        self,
        game_data,
        contributions,
        samples,
    ):
        """Persist one imported game and all of its derived rows atomically."""
        with self.ket_noi() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO games (
                    created_at, source, source_hash,
                    player_color, engine_color, winner_color,
                    result, reason, move_count,
                    moves_json, evals_json, positions_json,
                    white_time_ms, black_time_ms,
                    headers_json, pgn_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    game_data.get("created_at", datetime.now().isoformat()),
                    game_data.get("source", "PLAYED"),
                    game_data["source_hash"],
                    game_data.get("player_color"),
                    game_data.get("engine_color"),
                    game_data.get("winner_color"),
                    game_data.get("result", "*"),
                    game_data.get("reason", ""),
                    game_data.get("move_count", 0),
                    json.dumps(game_data.get("moves", []), ensure_ascii=False),
                    json.dumps(game_data.get("evals", []), ensure_ascii=False),
                    json.dumps(game_data.get("positions", []), ensure_ascii=False),
                    game_data.get("white_time_ms"),
                    game_data.get("black_time_ms"),
                    json.dumps(game_data.get("headers", {}), ensure_ascii=False),
                    game_data.get("pgn_text", ""),
                ),
            )
            if cursor.rowcount == 0:
                row = connection.execute(
                    "SELECT id FROM games WHERE source_hash = ?",
                    (game_data["source_hash"],),
                ).fetchone()
                return row["id"], False

            game_id = cursor.lastrowid
            if contributions:
                connection.executemany(
                    """
                    INSERT OR IGNORE INTO contributions (
                        game_id, position_key, move_text, side,
                        source_type, outcome, weight,
                        move_number, is_opening
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            game_id, item["position_key"], item["move_text"],
                            item["side"], item["source_type"], item["outcome"],
                            item["weight"], item["move_number"],
                            int(item.get("is_opening", False)),
                        )
                        for item in contributions
                    ],
                )
            if samples:
                connection.executemany(
                    """
                    INSERT OR IGNORE INTO model_samples (
                        game_id, position_key, position_json, move_text,
                        next_position_json, future2_json, future4_json,
                        target, source_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            game_id, item["position_key"], item["position_json"],
                            item["move_text"], item["next_position_json"],
                            item.get("future2_json"), item.get("future4_json"),
                            item.get("target", 1.0), item.get("source_type", "GM"),
                        )
                        for item in samples
                    ],
                )
            return game_id, True

    def them_contributions(self, game_id, contributions):
        if len(contributions) == 0:
            return

        rows = [
            (
                game_id,
                item["position_key"],
                item["move_text"],
                item["side"],
                item["source_type"],
                item["outcome"],
                item["weight"],
                item["move_number"],
                int(item.get("is_opening", False)),
            )
            for item in contributions
        ]

        with self.ket_noi() as connection:
            connection.executemany(
                """
                INSERT OR IGNORE INTO contributions (
                    game_id, position_key, move_text, side,
                    source_type, outcome, weight,
                    move_number, is_opening
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def them_model_samples(self, game_id, samples):
        if len(samples) == 0:
            return

        rows = [
            (
                game_id,
                item["position_key"],
                item["position_json"],
                item["move_text"],
                item["next_position_json"],
                item.get("future2_json"),
                item.get("future4_json"),
                item.get("target", 1.0),
                item.get("source_type", "GM"),
            )
            for item in samples
        ]

        with self.ket_noi() as connection:
            connection.executemany(
                """
                INSERT OR IGNORE INTO model_samples (
                    game_id, position_key, position_json, move_text,
                    next_position_json, future2_json, future4_json,
                    target, source_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def them_correction(self, correction):
        with self.ket_noi() as connection:
            connection.execute(
                """
                INSERT INTO corrections (
                    game_id, position_key, old_move, new_move,
                    eval_before, eval_after, eval_replacement,
                    evaluation_drop, depth, search_time,
                    similar_count, weight
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    correction["game_id"],
                    correction["position_key"],
                    correction["old_move"],
                    correction["new_move"],
                    correction["eval_before"],
                    correction["eval_after"],
                    correction["eval_replacement"],
                    correction["evaluation_drop"],
                    correction["depth"],
                    correction["search_time"],
                    correction.get("similar_count", 1),
                    correction.get("weight", 0.1),
                ),
            )

    def rebuild_opening_book(self):
        with self.ket_noi() as connection:
            connection.execute("DELETE FROM opening_book")
            connection.execute(
                """
                INSERT INTO opening_book (
                    position_key, move_text, side,
                    gm_count, personal_count,
                    wins, draws, losses, weight
                )
                SELECT
                    position_key,
                    move_text,
                    side,
                    SUM(CASE WHEN source_type = 'GM' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN source_type = 'PERSONAL' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN outcome > 0.5 THEN 1 ELSE 0 END),
                    SUM(CASE WHEN outcome BETWEEN -0.5 AND 0.5 THEN 1 ELSE 0 END),
                    SUM(CASE WHEN outcome < -0.5 THEN 1 ELSE 0 END),
                    SUM(
                        CASE
                            WHEN source_type = 'GM' THEN weight * 5.0
                            ELSE weight
                        END
                    )
                FROM contributions
                WHERE is_opening = 1
                GROUP BY position_key, move_text, side
                """
            )

    def lay_book_moves(self, position_key, side):
        with self.ket_noi() as connection:
            rows = connection.execute(
                """
                SELECT * FROM opening_book
                WHERE position_key = ? AND side = ?
                ORDER BY weight DESC, wins DESC, gm_count DESC
                """,
                (position_key, side),
            ).fetchall()

        return [dict(row) for row in rows]

    def lay_correction(self, position_key):
        with self.ket_noi() as connection:
            row = connection.execute(
                """
                SELECT * FROM corrections
                WHERE position_key = ?
                ORDER BY weight * similar_count DESC, id DESC
                LIMIT 1
                """,
                (position_key,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def lay_history(self, limit=8, offset=0):
        with self.ket_noi() as connection:
            rows = connection.execute(
                """
                SELECT * FROM games
                WHERE source = 'PLAYED'
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

        return [dict(row) for row in rows]

    def dem_history(self):
        with self.ket_noi() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM games WHERE source = 'PLAYED'"
            ).fetchone()

        return row["count"]

    def lay_game_detail(self, game_id):
        with self.ket_noi() as connection:
            game = connection.execute(
                "SELECT * FROM games WHERE id = ?",
                (game_id,),
            ).fetchone()

            if game is None:
                return None

            corrections = connection.execute(
                "SELECT * FROM corrections WHERE game_id = ? ORDER BY id",
                (game_id,),
            ).fetchall()
            contributions = connection.execute(
                """
                SELECT * FROM contributions
                WHERE game_id = ? ORDER BY move_number
                """,
                (game_id,),
            ).fetchall()

        result = dict(game)
        result["corrections"] = [dict(row) for row in corrections]
        result["contributions"] = [dict(row) for row in contributions]
        return result

    def xoa_game(self, game_id):
        with self.ket_noi() as connection:
            cursor = connection.execute(
                "DELETE FROM games WHERE id = ? AND source = 'PLAYED'",
                (game_id,),
            )
            was_deleted = cursor.rowcount > 0

        if was_deleted:
            self.rebuild_opening_book()

        return was_deleted

    def xoa_import_loi(self, game_id):
        with self.ket_noi() as connection:
            connection.execute(
                "DELETE FROM games WHERE id = ? AND source = 'GM_PGN'",
                (game_id,),
            )

    def dem_model_samples(self):
        with self.ket_noi() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM model_samples"
            ).fetchone()

        return row["count"]

    def thong_ke_model_samples(self):
        with self.ket_noi() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS count,
                    COALESCE(MAX(id), 0) AS max_id
                FROM model_samples
                """
            ).fetchone()

        return int(row["count"]), int(row["max_id"])

    def lay_model_samples(self, limit, offset=0):
        with self.ket_noi() as connection:
            rows = connection.execute(
                """
                SELECT * FROM model_samples
                ORDER BY id
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

        return [dict(row) for row in rows]

    def lay_model_samples_sau_id(
        self,
        connection,
        limit,
        last_id=0,
        maximum_id=None,
    ):
        if maximum_id is None:
            maximum_id = 9_223_372_036_854_775_807

        rows = connection.execute(
            """
            SELECT
                id,
                position_json,
                move_text,
                next_position_json,
                future2_json,
                future4_json,
                target
            FROM model_samples
            WHERE id > ? AND id <= ?
            ORDER BY id
            LIMIT ?
            """,
            (last_id, maximum_id, limit),
        ).fetchall()

        return [dict(row) for row in rows]

    def lay_id_model_truoc_offset(self, connection, offset):
        if offset <= 0:
            return 0

        row = connection.execute(
            """
            SELECT id
            FROM model_samples
            ORDER BY id
            LIMIT 1 OFFSET ?
            """,
            (offset - 1,),
        ).fetchone()

        if row is None:
            return 0

        return int(row["id"])


class pgnparser:
    def tao_snapshot_ban_dau(self):
        return {
            "board": list(
                "rnbqkbnr"
                "pppppppp"
                "........"
                "........"
                "........"
                "........"
                "PPPPPPPP"
                "RNBQKBNR"
            ),
            "turn": "white",
            "castling_rights": {
                "white_kingside": True,
                "white_queenside": True,
                "black_kingside": True,
                "black_queenside": True,
            },
            "en_passant_target": None,
            "halfmove_clock": 0,
            "position_counts": {},
        }

    def fen_thanh_snapshot(self, fen_text):
        parts = fen_text.strip().split()

        if len(parts) < 4:
            raise ValueError("FEN thiếu trường")

        board = []
        ranks = parts[0].split("/")

        if len(ranks) != 8:
            raise ValueError("FEN không đủ 8 hàng")

        for rank_text in ranks:
            for character in rank_text:
                if character.isdigit():
                    board.extend(["."] * int(character))
                elif character in "PNBRQKpnbrqk":
                    board.append(character)
                else:
                    raise ValueError("FEN có ký tự quân không hợp lệ")

        if len(board) != 64:
            raise ValueError("FEN không đủ 64 ô")

        turn = "white" if parts[1] == "w" else "black"
        castling_text = parts[2]
        en_passant_target = None

        if parts[3] != "-":
            en_passant_target = o_thanh_index(parts[3])

        try:
            halfmove_clock = int(parts[4]) if len(parts) > 4 else 0
        except ValueError:
            halfmove_clock = 0

        return {
            "board": board,
            "turn": turn,
            "castling_rights": {
                "white_kingside": "K" in castling_text,
                "white_queenside": "Q" in castling_text,
                "black_kingside": "k" in castling_text,
                "black_queenside": "q" in castling_text,
            },
            "en_passant_target": en_passant_target,
            "halfmove_clock": halfmove_clock,
            "position_counts": {},
        }

    def snapshot_thanh_fen(self, snapshot):
        rank_texts = []

        for row in range(8):
            empty_count = 0
            rank_text = ""

            for col in range(8):
                piece = snapshot["board"][row * 8 + col]

                if piece == ".":
                    empty_count += 1
                else:
                    if empty_count > 0:
                        rank_text += str(empty_count)
                        empty_count = 0

                    rank_text += piece

            if empty_count > 0:
                rank_text += str(empty_count)

            rank_texts.append(rank_text)

        castling_text = ""
        rights = snapshot["castling_rights"]

        if rights["white_kingside"]:
            castling_text += "K"
        if rights["white_queenside"]:
            castling_text += "Q"
        if rights["black_kingside"]:
            castling_text += "k"
        if rights["black_queenside"]:
            castling_text += "q"

        if castling_text == "":
            castling_text = "-"

        if snapshot["en_passant_target"] is None:
            en_passant_text = "-"
        else:
            en_passant_text = index_thanh_o(snapshot["en_passant_target"])

        turn_text = "w" if snapshot["turn"] == "white" else "b"

        return " ".join(
            (
                "/".join(rank_texts),
                turn_text,
                castling_text,
                en_passant_text,
                str(snapshot.get("halfmove_clock", 0)),
                "1",
            )
        )

    def tach_cac_game(self, pgn_text):
        pgn_text = pgn_text.replace("\ufeff", "")
        starts = [
            match.start()
            for match in re.finditer(r"(?m)^\s*\[Event\s+\"", pgn_text)
        ]

        if len(starts) == 0:
            if pgn_text.strip():
                return [pgn_text]

            return []

        games = []

        for index, start in enumerate(starts):
            if index + 1 < len(starts):
                end = starts[index + 1]
            else:
                end = len(pgn_text)

            game_text = pgn_text[start:end].strip()

            if game_text:
                games.append(game_text)

        return games

    def doc_headers(self, game_text):
        headers = {}

        for key, value in re.findall(
            r'^\s*\[([^\s]+)\s+\"((?:\\.|[^\"])*)\"\]\s*$',
            game_text,
            flags=re.MULTILINE,
        ):
            headers[key] = value.replace('\\"', '"')

        return headers

    def bo_variation(self, move_text):
        result = []
        depth = 0

        for character in move_text:
            if character == "(":
                depth += 1
                continue
            if character == ")":
                depth = max(0, depth - 1)
                continue
            if depth == 0:
                result.append(character)

        return "".join(result)

    def lay_tokens(self, game_text):
        move_text = re.sub(r"(?m)^\s*\[[^\]]+\]\s*$", " ", game_text)
        move_text = re.sub(r"\{.*?\}", " ", move_text, flags=re.DOTALL)
        move_text = re.sub(r"(?m);[^\n\r]*", " ", move_text)
        move_text = re.sub(r"(?m)^\s*%[^\n\r]*", " ", move_text)
        move_text = self.bo_variation(move_text)
        move_text = re.sub(r"\$\d+", " ", move_text)
        move_text = re.sub(r"\d+\.(?:\.\.)?", " ", move_text)
        move_text = move_text.replace("...", " ")

        return [
            token.strip()
            for token in move_text.split()
            if token.strip()
        ]

    def chuan_hoa_san(self, san_text):
        san_text = san_text.strip()
        san_text = san_text.replace("0-0-0", "O-O-O")
        san_text = san_text.replace("0-0", "O-O")
        san_text = re.sub(r"e\.?p\.?$", "", san_text, flags=re.IGNORECASE)
        san_text = re.sub(r"[!?]+$", "", san_text)
        san_text = re.sub(r"[+#]+$", "", san_text)
        return san_text

    def tao_san(self, engine, move, legal_moves=None, them_check=True):
        if legal_moves is None:
            legal_moves = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)

        from_index, to_index, promotion_piece = move
        moving_piece = engine.board[from_index]
        piece_type = moving_piece.upper()
        is_capture = engine.board[to_index] != "."

        if moving_piece in ("P", "p"):
            if to_index == engine.en_passant_target:
                if from_index % 8 != to_index % 8:
                    is_capture = True

        if piece_type == "K" and abs(to_index - from_index) == 2:
            if to_index > from_index:
                san_text = "O-O"
            else:
                san_text = "O-O-O"
        else:
            san_text = ""

            if piece_type == "P":
                if is_capture:
                    san_text += index_thanh_o(from_index)[0]
            else:
                san_text += piece_type
                same_moves = []

                for other_move in legal_moves:
                    if other_move == move or other_move[1] != to_index:
                        continue

                    other_piece = engine.board[other_move[0]]

                    if other_piece.upper() == piece_type:
                        same_moves.append(other_move)

                if same_moves:
                    same_file = any(
                        other_move[0] % 8 == from_index % 8
                        for other_move in same_moves
                    )
                    same_rank = any(
                        other_move[0] // 8 == from_index // 8
                        for other_move in same_moves
                    )

                    if same_file == False:
                        san_text += index_thanh_o(from_index)[0]
                    elif same_rank == False:
                        san_text += index_thanh_o(from_index)[1]
                    else:
                        san_text += index_thanh_o(from_index)

            if is_capture:
                san_text += "x"

            san_text += index_thanh_o(to_index)

            if promotion_piece is not None:
                san_text += "=" + promotion_piece.upper()

        if them_check:
            undo_info = engine.thuc_hien_nuoc_di(move)

            try:
                if engine.is_king_in_check(engine.turn):
                    opponent_moves = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)

                    if len(opponent_moves) == 0:
                        san_text += "#"
                    else:
                        san_text += "+"
            finally:
                engine.hoan_tac_nuoc_di(undo_info)

        return san_text

    def tim_move_tu_token(self, engine, token):
        legal_moves = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
        uci_move = text_thanh_move(token, engine.turn)

        if uci_move in legal_moves:
            return uci_move, self.tao_san(
                engine,
                uci_move,
                legal_moves,
                False,
            )

        target_san = self.chuan_hoa_san(token)
        matches = []

        for move in legal_moves:
            generated_san = self.tao_san(
                engine,
                move,
                legal_moves,
                False,
            )

            if self.chuan_hoa_san(generated_san) == target_san:
                matches.append((move, generated_san))

        if len(matches) != 1:
            raise ValueError(f"Không xác định được nước: {token}")

        return matches[0]

    def la_opening(self, snapshot, ply):
        if ply >= 24:
            return False

        board = snapshot["board"]

        if "Q" not in board or "q" not in board:
            return False

        non_pawn_material = sum(
            1
            for piece in board
            if piece.upper() in ("N", "B", "R", "Q")
        )

        return non_pawn_material >= 10

    def parse_game(self, game_text):
        headers = self.doc_headers(game_text)

        if headers.get("SetUp") == "1" and headers.get("FEN"):
            snapshot = self.fen_thanh_snapshot(headers["FEN"])
        else:
            snapshot = self.tao_snapshot_ban_dau()

        engine = vitriengine(snapshot, 0.02)
        engine.position_counts[engine.tao_key_position()] = 1
        records = []
        result_token = headers.get("Result", "*")

        for token in self.lay_tokens(game_text):
            if token in ("1-0", "0-1", "1/2-1/2", "*"):
                result_token = token
                continue

            before_snapshot = {
                "board": engine.board.copy(),
                "turn": engine.turn,
                "castling_rights": engine.castling_rights.copy(),
                "en_passant_target": engine.en_passant_target,
                "halfmove_clock": engine.halfmove_clock,
                "position_counts": {},
            }
            position_key = key_thanh_text(engine.tao_key_position())
            move, san_text = self.tim_move_tu_token(engine, token)
            side = engine.turn
            engine.thuc_hien_nuoc_di(move)
            after_snapshot = {
                "board": engine.board.copy(),
                "turn": engine.turn,
                "castling_rights": engine.castling_rights.copy(),
                "en_passant_target": engine.en_passant_target,
                "halfmove_clock": engine.halfmove_clock,
                "position_counts": {},
            }
            records.append({
                "ply": len(records),
                "side": side,
                "position_key": position_key,
                "position_json": snapshot_thanh_json(before_snapshot),
                "move": move,
                "move_text": move_thanh_text(move),
                "san": san_text,
                "next_position_json": snapshot_thanh_json(after_snapshot),
                "is_opening": self.la_opening(before_snapshot, len(records)),
            })

        return {
            "headers": headers,
            "result": result_token,
            "records": records,
            "pgn_text": game_text,
        }


class caissajepa:
    piece_order = "PNBRQKpnbrqk"
    input_size = 64 * 12 + 1 + 4 + 8
    action_size = 64 + 64 + 5
    latent_size = 64
    trainable_parameter_names = (
        "encoder_w",
        "encoder_b",
        "predictor_w1",
        "predictor_b1",
        "predictor_w2",
        "predictor_b2",
        "predictor_w4",
        "predictor_b4",
        "value_w",
        "value_b",
    )

    def __init__(self, model_path, create_if_missing=True):
        if np is None:
            raise RuntimeError("Cần cài NumPy để dùng CAISSA-JEPA")

        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.trained_steps = 0
        self.adam_step_count = 0
        self.adam_m = {}
        self.adam_v = {}
        self.resume_epoch = 0
        self.resume_offset = 0
        self.resume_total_samples = 0
        self.resume_last_sample_id = 0
        self.resume_dataset_max_id = 0
        self.last_effective_rank = 0.0

        if self.model_path.exists():
            self.load()
        elif create_if_missing:
            self.khoi_tao_weights()
        else:
            raise FileNotFoundError(self.model_path)

    def khoi_tao_weights(self):
        rng = np.random.default_rng(20260805)
        encoder_scale = math.sqrt(2.0 / self.input_size)
        predictor_scale = math.sqrt(
            2.0 / (self.latent_size + self.action_size)
        )
        self.encoder_w = (
            rng.standard_normal((self.input_size, self.latent_size))
            * encoder_scale
        ).astype(np.float32)
        self.encoder_b = np.zeros(self.latent_size, dtype=np.float32)
        self.target_w = self.encoder_w.copy()
        self.target_b = self.encoder_b.copy()

        for horizon in (1, 2, 4):
            setattr(
                self,
                f"predictor_w{horizon}",
                (
                    rng.standard_normal(
                        (
                            self.latent_size + self.action_size,
                            self.latent_size,
                        )
                    ) * predictor_scale
                ).astype(np.float32),
            )
            setattr(
                self,
                f"predictor_b{horizon}",
                np.zeros(self.latent_size, dtype=np.float32),
            )

        self.value_w = (
            rng.standard_normal((self.latent_size, 1))
            * math.sqrt(2.0 / self.latent_size)
        ).astype(np.float32)
        self.value_b = np.zeros(1, dtype=np.float32)

    def load(self):
        with np.load(self.model_path, allow_pickle=False) as data:
            for name in (
                "encoder_w",
                "encoder_b",
                "target_w",
                "target_b",
                "predictor_w1",
                "predictor_b1",
                "predictor_w2",
                "predictor_b2",
                "predictor_w4",
                "predictor_b4",
                "value_w",
                "value_b",
            ):
                setattr(self, name, data[name].astype(np.float32))

            if "trained_steps" in data:
                self.trained_steps = int(data["trained_steps"][0])

            if "adam_step_count" in data:
                self.adam_step_count = int(data["adam_step_count"][0])

            if "resume_epoch" in data:
                self.resume_epoch = int(data["resume_epoch"][0])

            if "resume_offset" in data:
                self.resume_offset = int(data["resume_offset"][0])

            if "resume_total_samples" in data:
                self.resume_total_samples = int(
                    data["resume_total_samples"][0]
                )

            if "resume_last_sample_id" in data:
                self.resume_last_sample_id = int(
                    data["resume_last_sample_id"][0]
                )

            if "resume_dataset_max_id" in data:
                self.resume_dataset_max_id = int(
                    data["resume_dataset_max_id"][0]
                )

            for name in self.trainable_parameter_names:
                m_key = "adam_m_" + name
                v_key = "adam_v_" + name

                if m_key in data and v_key in data:
                    self.adam_m[name] = data[m_key].astype(np.float32)
                    self.adam_v[name] = data[v_key].astype(np.float32)

    def save(self):
        temp_path = self.model_path.with_suffix(".tmp.npz")
        save_data = {
            "encoder_w": self.encoder_w,
            "encoder_b": self.encoder_b,
            "target_w": self.target_w,
            "target_b": self.target_b,
            "predictor_w1": self.predictor_w1,
            "predictor_b1": self.predictor_b1,
            "predictor_w2": self.predictor_w2,
            "predictor_b2": self.predictor_b2,
            "predictor_w4": self.predictor_w4,
            "predictor_b4": self.predictor_b4,
            "value_w": self.value_w,
            "value_b": self.value_b,
            "trained_steps": np.array(
                [self.trained_steps],
                dtype=np.int64,
            ),
            "adam_step_count": np.array(
                [self.adam_step_count],
                dtype=np.int64,
            ),
            "resume_epoch": np.array([self.resume_epoch], dtype=np.int64),
            "resume_offset": np.array(
                [self.resume_offset],
                dtype=np.int64,
            ),
            "resume_total_samples": np.array(
                [self.resume_total_samples],
                dtype=np.int64,
            ),
            "resume_last_sample_id": np.array(
                [self.resume_last_sample_id],
                dtype=np.int64,
            ),
            "resume_dataset_max_id": np.array(
                [self.resume_dataset_max_id],
                dtype=np.int64,
            ),
            "model_version": np.array([3], dtype=np.int64),
        }

        for name in self.trainable_parameter_names:
            if name in self.adam_m and name in self.adam_v:
                save_data["adam_m_" + name] = self.adam_m[name]
                save_data["adam_v_" + name] = self.adam_v[name]

        np.savez_compressed(temp_path, **save_data)
        temp_path.replace(self.model_path)

    def ma_hoa_snapshot(self, snapshot):
        vector = np.zeros(self.input_size, dtype=np.float32)
        piece_map = {
            piece: index
            for index, piece in enumerate(self.piece_order)
        }

        for square_index, piece in enumerate(snapshot["board"]):
            if piece == ".":
                continue

            feature_index = piece_map[piece] * 64 + square_index
            vector[feature_index] = 1.0

        offset = 64 * 12
        vector[offset] = 1.0 if snapshot["turn"] == "white" else -1.0
        offset += 1

        for key in (
            "white_kingside",
            "white_queenside",
            "black_kingside",
            "black_queenside",
        ):
            vector[offset] = float(snapshot["castling_rights"].get(key, False))
            offset += 1

        en_passant_target = snapshot.get("en_passant_target")

        if en_passant_target is not None:
            vector[offset + en_passant_target % 8] = 1.0

        return vector

    def ma_hoa_action(self, move):
        vector = np.zeros(self.action_size, dtype=np.float32)
        from_index, to_index, promotion_piece = move
        vector[from_index] = 1.0
        vector[64 + to_index] = 1.0
        promotion_map = {
            "Q": 0,
            "R": 1,
            "B": 2,
            "N": 3,
            None: 4,
        }
        promotion_key = None

        if promotion_piece is not None:
            promotion_key = promotion_piece.upper()

        vector[128 + promotion_map[promotion_key]] = 1.0
        return vector

    def encode(self, input_batch, target=False):
        if target:
            return np.tanh(input_batch @ self.target_w + self.target_b)

        return np.tanh(input_batch @ self.encoder_w + self.encoder_b)

    def predict(self, latent_batch, action_batch, horizon=1):
        combined = np.concatenate((latent_batch, action_batch), axis=1)
        weight = getattr(self, f"predictor_w{horizon}")
        bias = getattr(self, f"predictor_b{horizon}")
        return np.tanh(combined @ weight + bias)

    def cosine_batch(self, first, second):
        numerator = np.sum(first * second, axis=1)
        first_norm = np.linalg.norm(first, axis=1) + 1e-8
        second_norm = np.linalg.norm(second, axis=1) + 1e-8
        return numerator / (first_norm * second_norm)

    def value(self, latent_batch):
        return np.tanh(latent_batch @ self.value_w + self.value_b)

    def danh_gia_snapshot(self, snapshot):
        input_vector = self.ma_hoa_snapshot(snapshot)[None, :]
        latent = self.encode(input_vector)
        return float(self.value(latent)[0, 0])

    def score_legal_moves(self, snapshot, legal_moves):
        if len(legal_moves) == 0:
            return [], [], 1.0

        state_vector = self.ma_hoa_snapshot(snapshot)[None, :]
        latent = self.encode(state_vector)
        action_batch = np.stack([
            self.ma_hoa_action(move)
            for move in legal_moves
        ])
        latent_batch = np.repeat(latent, len(legal_moves), axis=0)
        predicted = self.predict(latent_batch, action_batch, 1)
        next_vectors = []
        engine = vitriengine(snapshot, 0.02)

        for move in legal_moves:
            undo_info = engine.thuc_hien_nuoc_di(move)
            next_snapshot = {
                "board": engine.board.copy(),
                "turn": engine.turn,
                "castling_rights": engine.castling_rights.copy(),
                "en_passant_target": engine.en_passant_target,
                "halfmove_clock": engine.halfmove_clock,
                "position_counts": {},
            }
            next_vectors.append(self.ma_hoa_snapshot(next_snapshot))
            engine.hoan_tac_nuoc_di(undo_info)

        next_batch = np.stack(next_vectors)
        target_latent = self.encode(next_batch, target=True)
        online_next_latent = self.encode(next_batch)
        similarity = self.cosine_batch(predicted, target_latent)
        opponent_value = self.value(online_next_latent)[:, 0]
        raw_scores = similarity * 0.70 - opponent_value * 0.30
        stable_scores = raw_scores - np.max(raw_scores)
        priors = np.exp(stable_scores / 0.18)
        priors = priors / (np.sum(priors) + 1e-8)
        entropy = -float(np.sum(priors * np.log(priors + 1e-8)))

        if len(priors) > 1:
            entropy /= math.log(len(priors))

        return raw_scores.tolist(), priors.tolist(), entropy

    def cosine_gradient(self, predicted, target):
        predicted_norm = np.linalg.norm(predicted, axis=1, keepdims=True) + 1e-8
        target_norm = np.linalg.norm(target, axis=1, keepdims=True) + 1e-8
        cosine = np.sum(predicted * target, axis=1, keepdims=True) / (
            predicted_norm * target_norm
        )
        gradient = target / (predicted_norm * target_norm)
        gradient -= cosine * predicted / (predicted_norm ** 2)
        return gradient, cosine[:, 0]

    def adam_update(self, gradients, learning_rate):
        self.adam_step_count += 1
        beta1 = 0.9
        beta2 = 0.999
        epsilon = 1e-8

        for name, gradient in gradients.items():
            gradient = np.clip(gradient, -1.0, 1.0).astype(np.float32)

            if name not in self.adam_m:
                self.adam_m[name] = np.zeros_like(gradient)
                self.adam_v[name] = np.zeros_like(gradient)

            self.adam_m[name] = (
                beta1 * self.adam_m[name]
                + (1.0 - beta1) * gradient
            )
            self.adam_v[name] = (
                beta2 * self.adam_v[name]
                + (1.0 - beta2) * gradient * gradient
            )
            m_hat = self.adam_m[name] / (
                1.0 - beta1 ** self.adam_step_count
            )
            v_hat = self.adam_v[name] / (
                1.0 - beta2 ** self.adam_step_count
            )
            parameter = getattr(self, name)
            parameter -= learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)

    def train_batch(self, samples, learning_rate=0.001):
        batch_size = len(samples)

        if batch_size == 0:
            return None

        state_batch = np.stack([
            self.ma_hoa_snapshot(item["position"])
            for item in samples
        ])
        action_batch = np.stack([
            self.ma_hoa_action(item["move"])
            for item in samples
        ])
        next_batch = np.stack([
            self.ma_hoa_snapshot(item["next_position"])
            for item in samples
        ])
        future2_batch = np.stack([
            self.ma_hoa_snapshot(item["future2"])
            for item in samples
        ])
        future4_batch = np.stack([
            self.ma_hoa_snapshot(item["future4"])
            for item in samples
        ])
        negative_batch = np.stack([
            self.ma_hoa_snapshot(item["negative"])
            for item in samples
        ])
        target_value = np.array(
            [item.get("target", 1.0) for item in samples],
            dtype=np.float32,
        )[:, None]

        latent = self.encode(state_batch)
        next_latent = self.encode(next_batch)
        target1 = self.encode(next_batch, target=True)
        target2 = self.encode(future2_batch, target=True)
        target4 = self.encode(future4_batch, target=True)
        negative_target = self.encode(negative_batch, target=True)
        combined = np.concatenate((latent, action_batch), axis=1)
        horizon_data = (
            (1, target1, 1.0),
            (2, target2, 0.50),
            (4, target4, 0.25),
        )
        gradients = {}
        latent_gradient = np.zeros_like(latent)
        latent_loss = 0.0
        horizon_losses = {}
        predicted1 = None
        predicted1_gradient = None

        for horizon, target_latent, horizon_weight in horizon_data:
            weight_name = f"predictor_w{horizon}"
            bias_name = f"predictor_b{horizon}"
            predictor_w = getattr(self, weight_name)
            predicted = np.tanh(
                combined @ predictor_w + getattr(self, bias_name)
            )
            error = predicted - target_latent
            horizon_loss = float(np.mean(error * error))
            horizon_losses[horizon] = horizon_loss
            latent_loss += horizon_weight * horizon_loss
            predicted_gradient = (
                2.0 * horizon_weight * error
                / (batch_size * self.latent_size)
            )

            if horizon == 1:
                predicted1 = predicted
                predicted1_gradient = predicted_gradient

            pre_gradient = predicted_gradient * (1.0 - predicted * predicted)
            gradients[weight_name] = combined.T @ pre_gradient
            gradients[bias_name] = np.sum(pre_gradient, axis=0)
            latent_gradient += pre_gradient @ predictor_w[
                :self.latent_size
            ].T

        positive_gradient, positive_cosine = self.cosine_gradient(
            predicted1,
            target1,
        )
        negative_gradient, negative_cosine = self.cosine_gradient(
            predicted1,
            negative_target,
        )
        margin = 0.15
        rank_values = margin - positive_cosine + negative_cosine
        active_rank = (rank_values > 0).astype(np.float32)[:, None]
        ranking_loss = float(np.mean(np.maximum(0.0, rank_values)))
        ranking_accuracy = float(np.mean(rank_values <= 0.0))
        positive_cosine_mean = float(np.mean(positive_cosine))
        negative_cosine_mean = float(np.mean(negative_cosine))
        cosine_gap = positive_cosine_mean - negative_cosine_mean
        rank_gradient = (
            (-positive_gradient + negative_gradient)
            * active_rank
            * 0.20
            / batch_size
        )
        rank_pre_gradient = rank_gradient * (
            1.0 - predicted1 * predicted1
        )
        gradients["predictor_w1"] += combined.T @ rank_pre_gradient
        gradients["predictor_b1"] += np.sum(rank_pre_gradient, axis=0)
        latent_gradient += rank_pre_gradient @ self.predictor_w1[
            :self.latent_size
        ].T

        current_value = self.value(latent)
        next_value = self.value(next_latent)
        current_error = current_value - target_value
        next_error = next_value + target_value
        value_loss = float(
            np.mean(current_error * current_error)
            + np.mean(next_error * next_error)
        )
        current_value_gradient = (
            2.0 * current_error / batch_size
            * (1.0 - current_value * current_value)
        )
        next_value_gradient = (
            2.0 * next_error / batch_size
            * (1.0 - next_value * next_value)
        )
        gradients["value_w"] = (
            latent.T @ current_value_gradient
            + next_latent.T @ next_value_gradient
        )
        gradients["value_b"] = np.sum(
            current_value_gradient + next_value_gradient,
            axis=0,
        )
        latent_gradient += current_value_gradient @ self.value_w.T
        next_latent_gradient = next_value_gradient @ self.value_w.T

        variance = np.var(latent, axis=0)
        low_variance = variance < 0.05
        variance_loss = float(np.mean(np.maximum(0.0, 0.05 - variance)))

        if np.any(low_variance):
            centered = latent - np.mean(latent, axis=0, keepdims=True)
            variance_gradient = np.zeros_like(latent)
            variance_gradient[:, low_variance] = (
                -2.0
                * centered[:, low_variance]
                / (batch_size * self.latent_size)
            )
            latent_gradient += variance_gradient * 0.05

        latent_std = np.std(latent, axis=0)
        latent_std_mean = float(np.mean(latent_std))
        latent_std_min = float(np.min(latent_std))
        active_dimensions = int(np.sum(variance >= 0.05))
        effective_rank = self.last_effective_rank

        if self.trained_steps % 25 == 0 and batch_size >= 2:
            centered_latent = latent - np.mean(latent, axis=0, keepdims=True)
            singular_values = np.linalg.svd(
                centered_latent,
                compute_uv=False,
            )
            singular_energy = singular_values * singular_values
            energy_total = float(np.sum(singular_energy))

            if energy_total > 1e-12:
                probability = singular_energy / energy_total
                effective_rank = float(np.exp(
                    -np.sum(probability * np.log(probability + 1e-12))
                ))
            else:
                effective_rank = 0.0
            self.last_effective_rank = effective_rank

        latent_pre_gradient = latent_gradient * (1.0 - latent * latent)
        next_pre_gradient = next_latent_gradient * (
            1.0 - next_latent * next_latent
        )
        gradients["encoder_w"] = (
            state_batch.T @ latent_pre_gradient
            + next_batch.T @ next_pre_gradient
        )
        gradients["encoder_b"] = np.sum(
            latent_pre_gradient + next_pre_gradient,
            axis=0,
        )
        gradient_norm = math.sqrt(sum(
            float(np.sum(gradient * gradient))
            for gradient in gradients.values()
        ))
        self.adam_update(gradients, learning_rate)

        target_decay = 0.995
        self.target_w = (
            target_decay * self.target_w
            + (1.0 - target_decay) * self.encoder_w
        )
        self.target_b = (
            target_decay * self.target_b
            + (1.0 - target_decay) * self.encoder_b
        )
        self.trained_steps += 1

        return {
            "loss": latent_loss + value_loss + ranking_loss + variance_loss,
            "latent_loss": latent_loss,
            "latent_loss_h1": horizon_losses.get(1, 0.0),
            "latent_loss_h2": horizon_losses.get(2, 0.0),
            "latent_loss_h4": horizon_losses.get(4, 0.0),
            "value_loss": value_loss,
            "ranking_loss": ranking_loss,
            "variance_loss": variance_loss,
            "positive_cosine": positive_cosine_mean,
            "negative_cosine": negative_cosine_mean,
            "cosine_gap": cosine_gap,
            "ranking_accuracy": ranking_accuracy,
            "latent_std_mean": latent_std_mean,
            "latent_std_min": latent_std_min,
            "active_dimensions": active_dimensions,
            "effective_rank": effective_rank,
            "gradient_norm": gradient_norm,
        }


class traincancelled(KeyboardInterrupt):
    pass


class trainworker(QObject):
    """Run the v7 FEN trainer inside the GUI-owned QThread."""

    tien_do = Signal(object)
    ket_qua = Signal(object)
    hoan_tat = Signal()

    def __init__(
        self,
        database_path,
        model_path,
        stop_event,
        dataset_path,
        epochs,
        batch_size=64,
        latent_size=96,
        allow_dataset_change=False,
    ):
        super().__init__()
        self.database_path = database_path
        self.model_path = Path(model_path)
        self.stop_event = stop_event
        self.dataset_path = Path(dataset_path)
        self.epochs = int(epochs)
        self.batch_size = int(batch_size)
        self.latent_size = int(latent_size)
        self.allow_dataset_change = bool(allow_dataset_change)
        self.last_report = {}

    def _gui_progress(self, report):
        if self.stop_event.is_set():
            raise traincancelled()
        self.last_report = report.copy()
        starting_epoch = int(report.get("starting_epoch", 0))
        requested_epochs = max(1, int(report.get("requested_epochs", self.epochs)))
        current_epoch = int(report.get("current_epoch", starting_epoch + 1))
        phase = report.get("phase", "starting")
        if phase == "complete":
            completed_units = requested_epochs
        else:
            epoch_index = max(0, current_epoch - starting_epoch - 1)
            phase_fraction = {"starting": 0.0, "train": 0.45, "validation": 0.85}.get(phase, 0.5)
            completed_units = min(requested_epochs, epoch_index + phase_fraction)
        overall_total = requested_epochs * 1000
        overall_processed = int(round(overall_total * completed_units / requested_epochs))
        latest_metrics = report.get("latest_metrics", {})
        if "loss" not in latest_metrics and isinstance(latest_metrics.get("train"), dict):
            latest_metrics = latest_metrics["train"]
        payload = {
            "epoch": current_epoch,
            "epochs": starting_epoch + requested_epochs,
            "phase": phase,
            "processed": report.get("current_batch", 0),
            "total": report.get("current_batch", 0),
            "overall_processed": overall_processed,
            "overall_total": overall_total,
            "progress_percent": 100.0 * completed_units / requested_epochs,
            "trained_steps": report.get("trained_steps", 0),
            "valid_samples": 0,
            "skipped_samples": 0,
            "rows_per_second": None,
            "metrics": latest_metrics,
            "wall_time": time.time(),
        }
        self.tien_do.emit(payload)

    @Slot()
    def chay(self):
        try:
            if np is None:
                raise RuntimeError("Chưa cài NumPy")
            manifest_path = self.dataset_path / "dataset_manifest.json"
            if not manifest_path.exists():
                raise RuntimeError("Chưa có FEN dataset; hãy chạy crawler trước")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("status") not in ("TARGET_REACHED", "COMPLETE"):
                raise RuntimeError(
                    "Dataset chưa hoàn tất: " + str(manifest.get("status", "UNKNOWN"))
                )

            from argparse import Namespace
            from train_caissa_v7 import train as train_v7

            arguments = Namespace(
                dataset=str(self.dataset_path),
                model=str(self.model_path),
                epochs=self.epochs,
                batch_size=self.batch_size,
                learning_rate=5e-4,
                latent_size=self.latent_size,
                architecture="adversarial-jepa",
                seed=20260903,
                validation_percent=10,
                max_train_batches=0,
                max_validation_batches=0,
                allow_dataset_change=self.allow_dataset_change,
                resume=self.model_path.exists(),
                progress_interval=0.5,
            )
            train_v7(arguments, progress_callback=self._gui_progress)
            report_path = self.model_path.with_suffix(".training.json")
            if report_path.exists():
                self.last_report = json.loads(report_path.read_text(encoding="utf-8"))
            self.ket_qua.emit({
                "cancelled": False,
                "trained_steps": self.last_report.get("trained_steps", 0),
                "metrics": self.last_report.get("latest_metrics", {}),
                "model_path": str(self.model_path),
            })
        except traincancelled:
            self.ket_qua.emit({
                "cancelled": True,
                "trained_steps": self.last_report.get("trained_steps", 0),
                "metrics": self.last_report.get("latest_metrics", {}),
                "model_path": str(self.model_path),
            })
        except Exception as error:
            self.ket_qua.emit({
                "error": str(error),
                "trained_steps": self.last_report.get("trained_steps", 0),
                "model_path": str(self.model_path),
            })
        finally:
            self.hoan_tat.emit()


class mctsnode:
    def __init__(self, move=None, prior=1.0):
        self.move = move
        self.prior = float(prior)
        self.visits = 0
        self.value_sum = 0.0
        self.children = {}
        self.expanded = False

    def mean_value(self):
        if self.visits == 0:
            return 0.0

        return self.value_sum / self.visits


class caissamcts:
    def __init__(
        self,
        snapshot,
        model,
        gioi_han_giay,
        stop_event=None,
        preferred_move=None,
        progress_callback=None,
    ):
        self.snapshot = snapshot
        self.model = model
        self.gioi_han_giay = max(0.02, gioi_han_giay)
        self.stop_event = stop_event
        self.preferred_move = preferred_move
        self.progress_callback = progress_callback
        self.root_color = snapshot["turn"]
        self.root = mctsnode()
        self.simulations = 0
        self.end_time = 0.0
        self.start_time = 0.0
        self.last_progress_time = 0.0

    def het_thoi_gian(self):
        if self.stop_event is not None and self.stop_event.is_set():
            return True

        return time.perf_counter() >= self.end_time

    def terminal_value(self, engine, legal_moves):
        # MCTS must share the same draw adjudication as alpha-beta.  Without
        # this check a K-vs-K or threefold-repetition node is sent to the
        # learned value head while negamax correctly returns a draw.
        if engine.is_draw_search():
            return 0.0

        if len(legal_moves) > 0:
            return None

        if engine.is_king_in_check(engine.turn):
            winner = engine.mau_doi_thu(engine.turn)

            if winner == self.root_color:
                return 1.0

            return -1.0

        return 0.0

    def expand(self, node, engine, legal_moves):
        snapshot = {
            "board": engine.board.copy(),
            "turn": engine.turn,
            "castling_rights": engine.castling_rights.copy(),
            "en_passant_target": engine.en_passant_target,
            "halfmove_clock": engine.halfmove_clock,
            "position_counts": engine.position_counts.copy(),
        }
        _, priors, _ = self.model.score_legal_moves(snapshot, legal_moves)

        for move, prior in zip(legal_moves, priors):
            if node is self.root and move == self.preferred_move:
                prior *= 1.75

            node.children[move] = mctsnode(move, prior)

        total_prior = sum(child.prior for child in node.children.values())

        if total_prior > 0:
            for child in node.children.values():
                child.prior /= total_prior

        node.expanded = True

    def select_child(self, node, turn):
        best_child = None
        best_score = -float("inf")
        parent_sqrt = math.sqrt(max(1, node.visits))

        for child in node.children.values():
            q_value = child.mean_value()

            if turn != self.root_color:
                q_value = -q_value

            exploration = (
                1.35
                * child.prior
                * parent_sqrt
                / (1 + child.visits)
            )
            score = q_value + exploration

            if score > best_score:
                best_score = score
                best_child = child

        return best_child

    def run_simulation(self):
        engine = vitriengine(self.snapshot, 0.02)
        node = self.root
        path = [node]

        while node.expanded and node.children:
            child = self.select_child(node, engine.turn)

            if child is None:
                break

            engine.thuc_hien_nuoc_di(child.move)
            node = child
            path.append(node)

        legal_moves = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
        root_value = self.terminal_value(engine, legal_moves)

        if root_value is None:
            if node.expanded == False:
                self.expand(node, engine, legal_moves)

            leaf_snapshot = {
                "board": engine.board.copy(),
                "turn": engine.turn,
                "castling_rights": engine.castling_rights.copy(),
                "en_passant_target": engine.en_passant_target,
                "halfmove_clock": engine.halfmove_clock,
                "position_counts": engine.position_counts.copy(),
            }
            leaf_value = self.model.danh_gia_snapshot(leaf_snapshot)

            if engine.turn == self.root_color:
                root_value = leaf_value
            else:
                root_value = -leaf_value

        for path_node in path:
            path_node.visits += 1
            path_node.value_sum += root_value

        self.simulations += 1

    def phat_tien_do(self, force=False):
        if self.progress_callback is None:
            return

        current_time = time.perf_counter()

        if force == False:
            if current_time - self.last_progress_time < 0.20:
                return

        self.last_progress_time = current_time
        total_visits = sum(
            child.visits
            for child in self.root.children.values()
        )
        move_stats = []

        for move, child in self.root.children.items():
            move_stats.append({
                "move": move,
                "visits": child.visits,
                "visit_share": child.visits / max(1, total_visits),
                "value": child.mean_value(),
                "prior": child.prior,
            })

        move_stats.sort(key=lambda item: item["visits"], reverse=True)
        elapsed = max(0.0, current_time - self.start_time)

        try:
            self.progress_callback({
                "stage": "MCTS",
                "simulations": self.simulations,
                "simulations_per_second": (
                    self.simulations / elapsed if elapsed > 0 else 0.0
                ),
                "time": round(elapsed, 3),
                "time_limit": round(self.gioi_han_giay, 3),
                "moves": move_stats[:8],
            })
        except Exception:
            pass

    def tim_nuoc_di(self):
        start_time = time.perf_counter()
        self.start_time = start_time
        self.end_time = start_time + self.gioi_han_giay

        while self.het_thoi_gian() == False:
            self.run_simulation()
            self.phat_tien_do()

        self.phat_tien_do(force=True)

        if len(self.root.children) == 0:
            return {
                "move": None,
                "simulations": self.simulations,
                "time": time.perf_counter() - start_time,
                "moves": [],
            }

        move_stats = []
        total_visits = sum(
            child.visits
            for child in self.root.children.values()
        )

        for move, child in self.root.children.items():
            move_stats.append({
                "move": move,
                "visits": child.visits,
                "visit_share": child.visits / max(1, total_visits),
                "value": child.mean_value(),
                "prior": child.prior,
            })

        move_stats.sort(key=lambda item: item["visits"], reverse=True)

        return {
            "move": move_stats[0]["move"],
            "simulations": self.simulations,
            "time": round(time.perf_counter() - start_time, 3),
            "moves": move_stats,
        }


class importworker(QObject):
    tien_do = Signal(object)
    ket_qua = Signal(object)
    hoan_tat = Signal()

    def __init__(self, file_paths, database_path, stop_event):
        super().__init__()
        self.file_paths = file_paths
        self.database_path = database_path
        self.stop_event = stop_event
        self.max_input_bytes = 4 * 1024 * 1024 * 1024

    def doc_tung_game(self, file_path):
        current_lines = []
        current_bytes = 0

        with open(file_path, "rb") as file:
            for raw_line in file:
                if self.stop_event.is_set():
                    break

                line = raw_line.decode("utf-8-sig", errors="replace")

                if line.lstrip().startswith('[Event "'):
                    if len(current_lines) > 0:
                        yield "".join(current_lines), current_bytes

                    current_lines = [line]
                    current_bytes = len(raw_line)
                    continue

                if len(current_lines) == 0:
                    continue

                current_lines.append(line)
                current_bytes += len(raw_line)

        if len(current_lines) > 0:
            yield "".join(current_lines), current_bytes

    def la_title_gm(self, title_text):
        titles = re.split(r"[^A-Za-z]+", title_text.upper())
        return "GM" in titles

    @Slot()
    def chay(self):
        parser = pgnparser()
        database = chessdatabase(self.database_path)
        stats = {
            "games_seen": 0,
            "imported": 0,
            "duplicates": 0,
            "skipped": 0,
            "errors": 0,
            "bytes_read": 0,
        }

        try:
            for file_path in self.file_paths:
                if self.stop_event.is_set():
                    break

                for game_text, game_bytes in self.doc_tung_game(file_path):
                    if self.stop_event.is_set():
                        break

                    if stats["bytes_read"] + game_bytes > self.max_input_bytes:
                        self.stop_event.set()
                        break

                    stats["bytes_read"] += game_bytes
                    stats["games_seen"] += 1
                    new_game_id = None

                    try:
                        headers = parser.doc_headers(game_text)
                        result = headers.get("Result", "*")

                        if result == "1-0":
                            winner_color = "white"
                            winner_title = headers.get("WhiteTitle", "")
                        elif result == "0-1":
                            winner_color = "black"
                            winner_title = headers.get("BlackTitle", "")
                        else:
                            stats["skipped"] += 1
                            continue

                        if self.la_title_gm(winner_title) == False:
                            stats["skipped"] += 1
                            continue

                        parsed_game = parser.parse_game(game_text)
                        records = parsed_game["records"]

                        if len(records) == 0:
                            stats["skipped"] += 1
                            continue

                        canonical_data = {
                            "white": headers.get("White", ""),
                            "black": headers.get("Black", ""),
                            "date": headers.get("Date", ""),
                            "round": headers.get("Round", ""),
                            "result": result,
                            "moves": [item["move_text"] for item in records],
                        }
                        source_hash = hashlib.sha256(
                            json.dumps(
                                canonical_data,
                                sort_keys=True,
                                ensure_ascii=False,
                            ).encode("utf-8")
                        ).hexdigest()
                        game_data = {
                            "created_at": datetime.now().isoformat(),
                            "source": "GM_PGN",
                            "source_hash": source_hash,
                            "engine_color": winner_color,
                            "winner_color": winner_color,
                            "result": result,
                            "reason": "GM PGN import",
                            "move_count": len(records),
                            "moves": [item["move_text"] for item in records],
                            "positions": [
                                item["position_json"]
                                for item in records
                            ],
                            "headers": headers,
                            "pgn_text": game_text,
                        }

                        winner_records = [
                            (index, item)
                            for index, item in enumerate(records)
                            if item["side"] == winner_color
                        ]
                        contributions = []
                        samples = []

                        for record_index, item in winner_records:
                            contributions.append({
                                "position_key": item["position_key"],
                                "move_text": item["move_text"],
                                "side": winner_color,
                                "source_type": "GM",
                                "outcome": 1.0,
                                "weight": 1.0,
                                "move_number": record_index + 1,
                                "is_opening": item["is_opening"],
                            })

                            if record_index + 1 < len(records):
                                future2_json = records[
                                    record_index + 1
                                ]["next_position_json"]
                            else:
                                future2_json = None

                            if record_index + 3 < len(records):
                                future4_json = records[
                                    record_index + 3
                                ]["next_position_json"]
                            else:
                                future4_json = None

                            samples.append({
                                "position_key": item["position_key"],
                                "position_json": item["position_json"],
                                "move_text": item["move_text"],
                                "next_position_json": item[
                                    "next_position_json"
                                ],
                                "future2_json": future2_json,
                                "future4_json": future4_json,
                                "target": 1.0,
                                "source_type": "GM",
                            })

                        game_id, is_new = database.luu_game_bundle(
                            game_data,
                            contributions,
                            samples,
                        )
                        if is_new == False:
                            stats["duplicates"] += 1
                            continue
                        new_game_id = game_id
                        stats["imported"] += 1

                    except Exception:
                        if new_game_id is not None:
                            database.xoa_import_loi(new_game_id)

                        stats["errors"] += 1

                    if stats["games_seen"] % 25 == 0:
                        self.tien_do.emit(stats.copy())

            database.rebuild_opening_book()
            stats["cancelled"] = self.stop_event.is_set()
            self.ket_qua.emit(stats)
        except Exception as error:
            stats["error"] = str(error)
            self.ket_qua.emit(stats)
        finally:
            self.hoan_tat.emit()


class learningworker(QObject):
    ket_qua = Signal(object)
    hoan_tat = Signal()

    def __init__(
        self,
        database_path,
        game_id,
        records,
        engine_color,
        stop_event,
    ):
        super().__init__()
        self.database_path = database_path
        self.game_id = game_id
        self.records = records
        self.engine_color = engine_color
        self.stop_event = stop_event
        self.max_seconds = 20.0

    def engine_eval(self, white_eval):
        value = float(white_eval)

        if self.engine_color == "white":
            return value

        return -value

    def tim_sai_lam(self):
        candidates = []

        for index, record in enumerate(self.records):
            if record.get("side") != self.engine_color:
                continue

            before_eval = 0.0

            if index > 0:
                before_eval = self.engine_eval(
                    self.records[index - 1].get("evaluation", 0.0)
                )

            after_eval = self.engine_eval(
                record.get("evaluation", 0.0)
            )
            evaluation_drop = before_eval - after_eval

            if evaluation_drop < 1.5:
                continue

            future_engine_evals = [
                self.engine_eval(item.get("evaluation", 0.0))
                for item in self.records[index + 1:index + 7]
                if item.get("side") == self.engine_color
            ]

            if future_engine_evals:
                recovered = max(future_engine_evals) > before_eval - 0.6

                if recovered:
                    continue

            candidates.append({
                "record": record,
                "before_eval": before_eval,
                "after_eval": after_eval,
                "drop": evaluation_drop,
            })

        candidates.sort(key=lambda item: item["drop"], reverse=True)
        return candidates[:3]

    @Slot()
    def chay(self):
        learned = 0
        started_at = time.perf_counter()

        try:
            database = chessdatabase(self.database_path)
            candidates = self.tim_sai_lam()

            for index, candidate in enumerate(candidates):
                if self.stop_event.is_set():
                    break

                elapsed = time.perf_counter() - started_at
                remaining = self.max_seconds - elapsed

                if remaining <= 0.05:
                    break

                per_move = min(7.0, remaining / (len(candidates) - index))
                record = candidate["record"]
                snapshot = json_thanh_snapshot(record["position_json"])
                engine = vitriengine(snapshot, per_move, self.stop_event)
                result = engine.tim_nuoc_di_tot_nhat()
                replacement = result.get("move")
                old_move = text_thanh_move(
                    record["move_text"],
                    self.engine_color,
                )

                if replacement is None or replacement == old_move:
                    continue

                replacement_eval = float(result.get("score_white", 0.0))

                if self.engine_color == "black":
                    replacement_eval = -replacement_eval

                if replacement_eval <= candidate["after_eval"] + 0.35:
                    continue

                database.them_correction({
                    "game_id": self.game_id,
                    "position_key": record["position_key"],
                    "old_move": record["move_text"],
                    "new_move": move_thanh_text(replacement),
                    "eval_before": candidate["before_eval"],
                    "eval_after": candidate["after_eval"],
                    "eval_replacement": replacement_eval,
                    "evaluation_drop": candidate["drop"],
                    "depth": result.get("depth", 0),
                    "search_time": result.get("time", per_move),
                    "similar_count": 1,
                    "weight": min(1.0, candidate["drop"] / 5.0),
                })
                learned += 1

            self.ket_qua.emit({
                "learned": learned,
                "candidates": len(candidates),
                "cancelled": self.stop_event.is_set(),
                "time": round(time.perf_counter() - started_at, 2),
            })
        except Exception as error:
            self.ket_qua.emit({"error": str(error), "learned": learned})
        finally:
            self.hoan_tat.emit()


class engineworker(QObject):
    tien_do = Signal(object)
    ket_qua = Signal(object)
    hoan_tat = Signal()

    def __init__(
        self,
        snapshot,
        gioi_han_giay,
        session_id,
        stop_event,
        model_path=None,
        preferred_move=None,
        adversarial_model_path=None,
    ):
        super().__init__()
        self.snapshot = snapshot
        self.gioi_han_giay = gioi_han_giay
        self.session_id = session_id
        self.stop_event = stop_event
        self.model_path = model_path
        self.preferred_move = preferred_move
        self.adversarial_model_path = adversarial_model_path

    def phat_tien_do(self, progress):
        data = progress.copy()
        data["session_id"] = self.session_id
        self.tien_do.emit(data)

    def chon_hybrid_move(self, alpha_result, mcts_result):
        alpha_move = alpha_result.get("move")
        score_white = alpha_result.get("score_white", 0.0)

        if abs(score_white) >= 8.0:
            return {
                "move": alpha_move,
                "reason": "ALPHA_TACTICAL_OVERRIDE",
                "hybrid_score": None,
                "mcts_item": None,
            }

        best_move = alpha_move
        best_score = -float("inf")
        best_item = None

        for item in mcts_result.get("moves", []):
            hybrid_score = 0.55 * item["visit_share"]
            hybrid_score += 0.25 * ((item["value"] + 1.0) / 2.0)
            hybrid_score += 0.20 * item["prior"]

            if item["move"] == alpha_move:
                hybrid_score += 0.15

            if item["move"] == self.preferred_move:
                hybrid_score += 0.10

            if hybrid_score > best_score:
                best_score = hybrid_score
                best_move = item["move"]
                best_item = item

        return {
            "move": best_move,
            "reason": (
                "ALPHA_AGREEMENT"
                if best_move == alpha_move
                else "HYBRID_MCTS_SELECTION"
            ),
            "hybrid_score": best_score,
            "mcts_item": best_item,
        }

    @Slot()
    def chay(self):
        try:
            started_at = time.perf_counter()
            mcts_result = None
            model = None
            model_kind = None

            # Prefer the opponent-conditioned v7 checkpoint when it exists.
            # A malformed experimental checkpoint must not prevent the stable
            # v6/alpha-beta fallback from making a legal move.
            if (
                self.adversarial_model_path is not None
                and Path(self.adversarial_model_path).exists()
            ):
                try:
                    from adversarial_jepa import AdversarialJEPA
                    candidate = AdversarialJEPA(
                        self.adversarial_model_path,
                        create_if_missing=False,
                    )
                    if candidate.trained_steps > 0:
                        model = candidate
                        model_kind = "A_JEPA_V7"
                except Exception as error:
                    self.phat_tien_do({
                        "stage": "MODEL_FALLBACK",
                        "detail": "A_JEPA_V7 load failed: " + str(error),
                    })

            if (
                model is None
                and self.model_path is not None
                and Path(self.model_path).exists()
                and np is not None
            ):
                candidate = caissajepa(self.model_path, False)
                if candidate.trained_steps > 0:
                    model = candidate
                    model_kind = "JEPA_V6"

            if model is not None and self.gioi_han_giay >= 0.08:
                mcts_budget = max(0.02, self.gioi_han_giay * 0.52)
                mcts_search = caissamcts(
                    self.snapshot,
                    model,
                    mcts_budget,
                    self.stop_event,
                    self.preferred_move,
                    self.phat_tien_do,
                )
                mcts_result = mcts_search.tim_nuoc_di()

            elapsed = time.perf_counter() - started_at
            remaining = max(0.02, self.gioi_han_giay - elapsed)
            engine = vitriengine(
                self.snapshot,
                remaining,
                self.stop_event,
                self.phat_tien_do,
            )
            result = engine.tim_nuoc_di_tot_nhat(self.preferred_move)

            if mcts_result is not None and not self.stop_event.is_set():
                alpha_summary = {
                    "move": result.get("move"),
                    "score_white": result.get("score_white"),
                    "depth": result.get("depth"),
                    "nodes": result.get("nodes"),
                    "pv": result.get("pv"),
                }
                decision = self.chon_hybrid_move(
                    result,
                    mcts_result,
                )
                result["move"] = decision["move"]
                result["source"] = "CAISSA_JEPA_MCTS_ALPHA"
                result["mcts_simulations"] = mcts_result["simulations"]
                result["mcts_moves"] = mcts_result["moves"][:8]
                result["model_kind"] = model_kind
                result["alpha_beta"] = alpha_summary
                result["mcts_move"] = mcts_result.get("move")
                result["selected_move"] = decision["move"]
                result["selection_reason"] = decision["reason"]
                result["selection_hybrid_score"] = decision["hybrid_score"]

                # The alpha-beta PV/evaluation describe alpha_move, not a
                # different move selected by the hybrid.  Force the GUI to
                # evaluate that move afresh instead of displaying a false
                # centipawn score as if it belonged to the selected move.
                if decision["move"] != alpha_summary["move"]:
                    result["score_white"] = None
                    result["pv"] = [decision["move"]]

                result["time"] = round(
                    time.perf_counter() - started_at,
                    3,
                )
            else:
                result["source"] = "ALPHA_BETA"
                result["model_kind"] = "NONE"

            result["session_id"] = self.session_id
            result["cancelled"] = self.stop_event.is_set()
            result["time_limit"] = round(self.gioi_han_giay, 3)
            self.ket_qua.emit(result)
        except Exception as error:
            self.ket_qua.emit({
                "session_id": self.session_id,
                "cancelled": self.stop_event.is_set(),
                "error": str(error),
                "move": None,
            })
        finally:
            self.hoan_tat.emit()


class boardwidget(QWidget):
    monitor_train = Signal(object)
    monitor_engine = Signal(object)
    monitor_state = Signal(object)

    def __init__(self, project_dir=None):
        super().__init__()
        self.setMinimumSize(760, 600)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

        self.piece_to_file = {
            "K": "white_king.svg",
            "Q": "white_queen.svg",
            "R": "white_rook.svg",
            "B": "white_bishop.svg",
            "N": "white_knight.svg",
            "P": "white_pawn.svg",
            "k": "black_king.svg",
            "q": "black_queen.svg",
            "r": "black_rook.svg",
            "b": "black_bishop.svg",
            "n": "black_knight.svg",
            "p": "black_pawn.svg",
        }
        self.piece_symbols = {
            "K": "♔", "Q": "♕", "R": "♖",
            "B": "♗", "N": "♘", "P": "♙",
            "k": "♚", "q": "♛", "r": "♜",
            "b": "♝", "n": "♞", "p": "♟",
        }

        self.project_dir = (
            Path(project_dir)
            if project_dir is not None
            else Path(__file__).resolve().parent
        )
        self.asset_dir = self.project_dir / "assets/chess_pieces"
        self.piece_renderers = {}

        for piece, filename in self.piece_to_file.items():
            file_path = self.asset_dir / filename
            renderer = QSvgRenderer(str(file_path))

            if renderer.isValid():
                self.piece_renderers[piece] = renderer

        self.database = chessdatabase()
        self.pgn_parser = pgnparser()

        self.engine_thread = None
        self.engine_worker = None
        self.engine_stop_event = None
        self.engine_dang_tim = False
        self.search_session_id = 0
        self.gioi_han_search = 5.0
        self.thong_ke_search = {}

        self.import_thread = None
        self.import_worker = None
        self.import_stop_event = None
        self.import_dang_chay = False
        self.import_status = ""

        self.model_path = self.project_dir / "chess_data/caissa_jepa.npz"
        self.adversarial_model_path = (
            self.project_dir / "chess_data/caissa_a_jepa_v7.npz"
        )
        self.train_thread = None
        self.train_worker = None
        self.train_stop_event = None
        self.train_dang_chay = False
        self.train_status = ""

        self.learning_thread = None
        self.learning_worker = None
        self.learning_stop_event = None
        self.learning_status = ""

        self.history_open = False
        self.history_detail = None
        self.history_page = 0
        self.history_rows = []
        self.history_row_rects = []
        self.history_delete_rects = []
        self.history_close_rect = QRectF()
        self.history_prev_rect = QRectF()
        self.history_next_rect = QRectF()
        self.history_back_rect = QRectF()
        self.history_detail_page = 0

        self.history_button_rect = QRectF()
        self.import_button_rect = QRectF()
        self.train_button_rect = QRectF()

        self.clock_timer = QTimer(self)
        self.clock_timer.setInterval(50)
        self.clock_timer.timeout.connect(self.cap_nhat_clock)
        self.clock_timer.start()

        self.khoi_dong_lai_game()

    def khoi_dong_lai_game(self):
        self.dung_search_engine()
        self.search_session_id += 1
        self.turn = "white"

        self.board = [
            "r", "n", "b", "q", "k", "b", "n", "r",
            "p", "p", "p", "p", "p", "p", "p", "p",
            ".", ".", ".", ".", ".", ".", ".", ".",
            ".", ".", ".", ".", ".", ".", ".", ".",
            ".", ".", ".", ".", ".", ".", ".", ".",
            ".", ".", ".", ".", ".", ".", ".", ".",
            "P", "P", "P", "P", "P", "P", "P", "P",
            "R", "N", "B", "Q", "K", "B", "N", "R",
        ]

        self.selected_index = None
        self.valid_move_index = []

        self.drag_start_index = None
        self.drag_piece = None
        self.is_dragging = False
        self.drag_mouse_x = 0
        self.drag_mouse_y = 0

        self.castling_rights = {
            "white_kingside": True,
            "white_queenside": True,
            "black_kingside": True,
            "black_queenside": True,
        }

        self.en_passant_target = None
        self.halfmove_clock = 0

        self.white_time_ms = 5 * 60 * 1000
        self.black_time_ms = 5 * 60 * 1000
        self.clock_increment_ms = 3000
        self.clock_dang_chay = False
        self.clock_moc_thoi_gian = None
        self.clock_last_tenths = {
            "white": 3000,
            "black": 3000,
        }
        self.clock_top_rect = QRectF()
        self.clock_bottom_rect = QRectF()

        self.position_counts = {}
        self.game_over = False
        self.game_result = None
        self.restart_button_rect = QRectF()
        self.thong_ke_search = {}
        self.thong_ke_time_management = {}
        self.game_started_at = datetime.now().isoformat()
        self.game_records = []
        self.game_da_luu = False
        self.current_game_id = None
        self.history_open = False
        self.history_detail = None

        self.player_color = None
        self.engine_color = None
        self.dang_chon_mau = True
        self.white_button_rect = QRectF()
        self.black_button_rect = QRectF()

        self.unsetCursor()

        self.ghi_nhan_position()
        self.evaluation_score = self.tinh_evaluation_position()
        self.cap_nhat_tieu_de()
        self.update()

    def tinhtoan_kich_co(self):
        left_space = 85
        right_space = 175
        width_bancochinh = self.width() - left_space - right_space
        height_bancochinh = self.height() - 80
        board_size = min(width_bancochinh, height_bancochinh)

        square_size = board_size // 8
        board_size = square_size * 8
        startx = left_space + (width_bancochinh - board_size) // 2
        starty = (self.height() - board_size) // 2

        return startx, starty, board_size, square_size

    def index_tu_o_hien_thi(self, display_row, display_col):
        if self.player_color == "black":
            board_row = 7 - display_row
            board_col = 7 - display_col
        else:
            board_row = display_row
            board_col = display_col

        return board_row * 8 + board_col

    def o_hien_thi_tu_index(self, index):
        board_row = index // 8
        board_col = index % 8

        if self.player_color == "black":
            return 7 - board_row, 7 - board_col

        return board_row, board_col

    #đổi vị trí piece
    def vi_tri_piece_từ_click_chuot(self, mouse_x, mouse_y):
        startx, starty, board_size, square_size = self.tinhtoan_kich_co()

        if mouse_x < startx:
            return None
        if mouse_y < starty:
            return None
        if mouse_x >= startx + board_size:
            return None
        if mouse_y >= starty + board_size:
            return None

        display_col = int((mouse_x - startx) // square_size)
        display_row = int((mouse_y - starty) // square_size)

        return self.index_tu_o_hien_thi(display_row, display_col)

    def mau_quan_co(self, piece):
        if piece == ".":
            return None

        if piece.isupper():
            return "white"

        return "black"

    def mau_doi_thu(self, color):
        if color == "white":
            return "black"

        return "white"

    def lay_clock_time(self, color):
        if color == "white":
            return self.white_time_ms

        return self.black_time_ms

    def dat_clock_time(self, color, time_ms):
        time_ms = max(0.0, float(time_ms))

        if color == "white":
            self.white_time_ms = time_ms
        else:
            self.black_time_ms = time_ms

    def doi_clock_thanh_text(self, time_ms):
        total_tenths = max(0, math.ceil(time_ms / 100.0))
        minutes = total_tenths // 600
        seconds = (total_tenths % 600) // 10
        tenths = total_tenths % 10

        return f"{minutes}:{seconds:02d}.{tenths}"

    def cap_nhat_khu_vuc_clock(self):
        if self.clock_top_rect.isNull() or self.clock_bottom_rect.isNull():
            self.update()
            return

        self.update(
            self.clock_top_rect.adjusted(-5, -5, 5, 5).toAlignedRect()
        )
        self.update(
            self.clock_bottom_rect.adjusted(-5, -5, 5, 5).toAlignedRect()
        )

    @Slot()
    def cap_nhat_clock(self):
        if self.clock_dang_chay == False:
            return
        if self.dang_chon_mau or self.game_over:
            return

        current_time = time.perf_counter()

        if self.clock_moc_thoi_gian is None:
            self.clock_moc_thoi_gian = current_time
            return

        elapsed_ms = (
            current_time - self.clock_moc_thoi_gian
        ) * 1000.0
        self.clock_moc_thoi_gian = current_time

        new_time_ms = self.lay_clock_time(self.turn) - elapsed_ms
        self.dat_clock_time(self.turn, new_time_ms)
        new_tenths = math.ceil(self.lay_clock_time(self.turn) / 100.0)

        if self.clock_last_tenths[self.turn] != new_tenths:
            self.clock_last_tenths[self.turn] = new_tenths
            self.cap_nhat_khu_vuc_clock()

        if self.lay_clock_time(self.turn) <= 0:
            color_het_gio = self.turn
            self.clock_dang_chay = False

            if color_het_gio == "white":
                self.ket_thuc_game("Đen thắng - Trắng hết giờ")
            else:
                self.ket_thuc_game("Trắng thắng - Đen hết giờ")

    def cong_increment_clock(self, color):
        new_time = self.lay_clock_time(color) + self.clock_increment_ms
        self.dat_clock_time(color, new_time)
        self.clock_last_tenths[color] = math.ceil(new_time / 100.0)

    def bat_dau_clock(self):
        self.clock_dang_chay = True
        self.clock_moc_thoi_gian = time.perf_counter()
        self.cap_nhat_khu_vuc_clock()

    def cap_nhat_tieu_de(self):
        if self.dang_chon_mau:
            self.window().setWindowTitle("chess - chọn màu")
            return

        if self.game_over:
            self.window().setWindowTitle(f"chess - {self.game_result}")
            return

        if self.turn == "white":
            turn_text = "trắng"
        else:
            turn_text = "đen"

        if self.engine_dang_tim:
            self.window().setWindowTitle(
                f"chess - {turn_text} - engine đang suy nghĩ"
            )
            return

        if self.is_king_in_check(self.turn):
            self.window().setWindowTitle(f"chess - {turn_text} - chiếu")
        else:
            self.window().setWindowTitle(f"chess - {turn_text}")

    def chon_mau_nguoi_choi(self, color):
        self.player_color = color
        self.engine_color = self.mau_doi_thu(color)
        self.dang_chon_mau = False
        self.white_button_rect = QRectF()
        self.black_button_rect = QRectF()
        self.bat_dau_clock()
        self.cap_nhat_tieu_de()
        self.update()
        self.monitor_state.emit({
            "event": "PLAYER_COLOR",
            "player_color": self.player_color,
            "engine_color": self.engine_color,
        })

        if self.turn == self.engine_color:
            QTimer.singleShot(250, self.bat_dau_search_engine)

    def engine_di_tam_thoi(self):
        self.bat_dau_search_engine()

    def tao_snapshot_engine(self):
        return {
            "board": self.board.copy(),
            "turn": self.turn,
            "castling_rights": self.castling_rights.copy(),
            "en_passant_target": self.en_passant_target,
            "halfmove_clock": self.halfmove_clock,
            "position_counts": self.position_counts.copy(),
        }

    def tinh_evaluation_position(self):
        snapshot = self.tao_snapshot_engine()
        engine = vitriengine(snapshot, 0.02)
        return round(engine.tinh_evaluation() / 100.0, 2)

    def tinh_do_phuc_tap_position(self, snapshot):
        engine = vitriengine(snapshot, 0.02)
        moves = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
        so_nuoc_an = sum(
            1
            for move in moves
            if engine.is_nuoc_an_quan(move)
        )
        so_nuoc_phong_cap = sum(
            1
            for move in moves
            if move[2] is not None
        )
        dang_bi_chieu = engine.is_king_in_check(engine.turn)
        so_quan = sum(1 for piece in engine.board if piece != ".")

        branching_score = min(
            1.0,
            max(0.0, (len(moves) - 12) / 28.0),
        )
        tactical_score = min(1.0, so_nuoc_an / 6.0)

        if 12 <= so_quan <= 28:
            phase_score = 1.0
        else:
            phase_score = 0.0

        complexity = 0.12
        complexity += branching_score * 0.38
        complexity += tactical_score * 0.32
        complexity += phase_score * 0.06

        if dang_bi_chieu:
            complexity += 0.12

        if so_nuoc_phong_cap > 0:
            complexity += 0.15

        complexity = min(1.0, complexity)

        return complexity, {
            "legal_moves": len(moves),
            "capture_moves": so_nuoc_an,
            "promotion_moves": so_nuoc_phong_cap,
            "in_check": dang_bi_chieu,
            "piece_count": so_quan,
            "complexity": round(complexity, 3),
        }

    def tinh_ngan_sach_search(self, snapshot):
        complexity, detail = self.tinh_do_phuc_tap_position(snapshot)
        remaining_seconds = self.lay_clock_time(self.engine_color) / 1000.0
        so_quan = detail["piece_count"]

        if so_quan > 24:
            expected_moves_left = 34
        elif so_quan > 12:
            expected_moves_left = 24
        else:
            expected_moves_left = 16

        increment_seconds = self.clock_increment_ms / 1000.0
        clock_allowance = (
            remaining_seconds / (expected_moves_left + 2)
            + increment_seconds * 0.75
        )

        if remaining_seconds < 30.0:
            low_time_limit = max(0.03, remaining_seconds * 0.12)
            clock_allowance = min(clock_allowance, low_time_limit)

        target_time = 0.65 + complexity * 4.35
        safe_available = max(0.02, remaining_seconds - 0.08)
        search_time = min(
            self.gioi_han_search,
            target_time,
            clock_allowance,
            safe_available,
        )
        search_time = max(0.02, search_time)

        detail["remaining_seconds"] = round(remaining_seconds, 3)
        detail["clock_allowance"] = round(clock_allowance, 3)
        detail["target_time"] = round(target_time, 3)
        detail["search_time"] = round(search_time, 3)
        self.thong_ke_time_management = detail

        return search_time

    def chon_nuoc_opening_book(self, snapshot):
        if self.pgn_parser.la_opening(snapshot, len(self.game_records)) == False:
            return None

        position_key = key_thanh_text(self.tao_key_position())
        book_rows = self.database.lay_book_moves(
            position_key,
            self.engine_color,
        )
        gm_rows = [row for row in book_rows if row["gm_count"] > 0]

        if len(gm_rows) == 0:
            return None

        max_weight = max(row["weight"] for row in gm_rows)
        strong_rows = [
            row
            for row in gm_rows
            if row["weight"] >= max_weight * 0.35
        ]
        engine = vitriengine(snapshot, 0.02)
        legal_moves = set(engine.lay_tat_ca_nuoc_di_hop_le(engine.turn))
        valid_rows = []
        weights = []

        for row in strong_rows:
            move = text_thanh_move(row["move_text"], self.engine_color)

            if move not in legal_moves:
                continue

            valid_rows.append((row, move))
            weights.append(max(0.01, row["weight"] ** 0.75))

        if len(valid_rows) == 0:
            return None

        selected_row, selected_move = random.choices(
            valid_rows,
            weights=weights,
            k=1,
        )[0]
        self.thong_ke_search = {
            "source": "GM_OPENING_BOOK",
            "move": selected_move,
            "gm_count": selected_row["gm_count"],
            "weight": selected_row["weight"],
            "depth": 0,
            "nodes": 0,
            "time": 0.0,
        }

        return selected_move

    def dung_search_engine(self):
        if self.engine_stop_event is not None:
            self.engine_stop_event.set()

        self.engine_dang_tim = False

    def bat_dau_search_engine(self):
        if self.dang_chon_mau:
            return
        if self.game_over:
            return
        if self.turn != self.engine_color:
            return
        if self.engine_dang_tim:
            return

        self.cap_nhat_clock()

        if self.game_over:
            return

        if self.engine_thread is not None:
            if self.engine_thread.isRunning():
                QTimer.singleShot(50, self.bat_dau_search_engine)
                return

        danh_sach_nuoc_di = self.lay_tat_ca_nuoc_di_hop_le(
            self.engine_color
        )

        if len(danh_sach_nuoc_di) == 0:
            self.kiem_tra_trang_thai_game()
            return

        snapshot = self.tao_snapshot_engine()
        book_move = self.chon_nuoc_opening_book(snapshot)

        if book_move is not None:
            book_progress = self.thong_ke_search.copy()
            book_progress["stage"] = "FINAL"
            book_progress["session_id"] = self.search_session_id
            self.monitor_engine.emit(book_progress)
            from_index, to_index, promotion_piece = book_move
            self.move_piece(
                from_index,
                to_index,
                True,
                promotion_piece,
                None,
            )
            return

        search_time = self.tinh_ngan_sach_search(snapshot)
        position_key = key_thanh_text(self.tao_key_position())
        correction = self.database.lay_correction(position_key)
        preferred_move = None

        if correction is not None:
            candidate = text_thanh_move(
                correction["new_move"],
                self.engine_color,
            )

            if candidate in danh_sach_nuoc_di:
                preferred_move = candidate

        stop_event = threading.Event()
        session_id = self.search_session_id

        thread = QThread(self)
        worker = engineworker(
            snapshot,
            search_time,
            session_id,
            stop_event,
            str(self.model_path),
            preferred_move,
            str(self.adversarial_model_path),
        )
        worker.moveToThread(thread)

        thread.started.connect(worker.chay)
        worker.tien_do.connect(self.nhan_tien_do_engine)
        worker.ket_qua.connect(self.nhan_ket_qua_engine)
        worker.hoan_tat.connect(thread.quit)
        worker.hoan_tat.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(
            lambda thread_da_xong=thread: self.ket_thuc_thread_engine(
                thread_da_xong
            )
        )

        self.engine_thread = thread
        self.engine_worker = worker
        self.engine_stop_event = stop_event
        self.engine_dang_tim = True
        self.cap_nhat_tieu_de()
        thread.start()

    @Slot(object)
    def nhan_tien_do_engine(self, progress):
        if progress.get("session_id") != self.search_session_id:
            return

        self.monitor_engine.emit(progress.copy())

    @Slot(object)
    def nhan_ket_qua_engine(self, result):
        if result.get("session_id") != self.search_session_id:
            return

        final_result = result.copy()
        final_result["stage"] = "FINAL"
        self.monitor_engine.emit(final_result)

        if result.get("cancelled"):
            return

        self.engine_dang_tim = False

        if "error" in result:
            print(f"Lỗi engine: {result['error']}")
            self.cap_nhat_tieu_de()
            return

        move = result.get("move")

        if move is None:
            self.kiem_tra_trang_thai_game()
            return

        if self.game_over or self.turn != self.engine_color:
            return

        self.thong_ke_search = result.copy()
        from_index, to_index, promotion_piece = move
        self.move_piece(
            from_index,
            to_index,
            True,
            promotion_piece,
            result.get("score_white"),
        )

    def ket_thuc_thread_engine(self, thread_da_xong):
        if self.engine_thread is not thread_da_xong:
            return

        self.engine_thread = None
        self.engine_worker = None
        self.engine_stop_event = None

        if self.engine_dang_tim:
            self.engine_dang_tim = False
            self.cap_nhat_tieu_de()

    def bat_dau_import_pgn(self):
        if self.import_dang_chay:
            return

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Chọn file PGN/TXT có ván GM",
            "",
            "PGN và TXT (*.pgn *.txt);;Tất cả file (*)",
        )

        if len(file_paths) == 0:
            return

        stop_event = threading.Event()
        thread = QThread(self)
        worker = importworker(
            file_paths,
            str(self.database.database_path),
            stop_event,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.chay)
        worker.tien_do.connect(self.nhan_tien_do_import)
        worker.ket_qua.connect(self.nhan_ket_qua_import)
        worker.hoan_tat.connect(thread.quit)
        worker.hoan_tat.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(
            lambda thread_da_xong=thread: self.ket_thuc_import_thread(
                thread_da_xong
            )
        )

        self.import_thread = thread
        self.import_worker = worker
        self.import_stop_event = stop_event
        self.import_dang_chay = True
        self.import_status = "Đang đọc dữ liệu GM..."
        self.update()
        thread.start()

    @Slot(object)
    def nhan_tien_do_import(self, stats):
        self.import_status = (
            f"Đọc {stats['games_seen']} | "
            f"nhập {stats['imported']}"
        )
        self.update()

    @Slot(object)
    def nhan_ket_qua_import(self, stats):
        if "error" in stats:
            self.import_status = "Import lỗi: " + stats["error"]
        else:
            self.import_status = (
                f"Xong: +{stats['imported']} | "
                f"trùng {stats['duplicates']} | "
                f"bỏ {stats['skipped']} | lỗi {stats['errors']}"
            )

        monitor_stats = stats.copy()
        monitor_stats["event"] = "IMPORT_RESULT"
        self.monitor_state.emit(monitor_stats)
        self.update()

    def ket_thuc_import_thread(self, thread_da_xong):
        if self.import_thread is not thread_da_xong:
            return

        self.import_thread = None
        self.import_worker = None
        self.import_stop_event = None
        self.import_dang_chay = False
        self.update()

    def bat_dau_train_model(self):
        if self.train_dang_chay:
            if self.train_stop_event is not None:
                self.train_stop_event.set()

            self.train_status = "Đang dừng sau batch hiện tại..."
            self.update()
            return

        if np is None:
            self.train_status = "Cần cài NumPy để train"
            self.update()
            return

        dataset_path = self.project_dir / "fen_dataset"
        manifest_path = dataset_path / "dataset_manifest.json"
        if not manifest_path.exists():
            self.train_status = "Chưa có FEN dataset; hãy chạy crawler"
            self.update()
            return

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as error:
            self.train_status = "Không đọc được dataset: " + str(error)
            self.update()
            return

        if manifest.get("status") not in ("TARGET_REACHED", "COMPLETE"):
            self.train_status = (
                "Dataset chưa hoàn tất: "
                + str(manifest.get("status", "UNKNOWN"))
            )
            self.update()
            return

        sample_count = int(manifest.get("positions", 0))
        if sample_count == 0:
            self.train_status = "Dataset chưa có vị trí FEN hợp lệ"
            self.update()
            return

        epochs, accepted = QInputDialog.getInt(
            self,
            "CAISSA-JEPA v7",
            "Số epoch train thêm:",
            5,
            1,
            10000,
        )
        if not accepted:
            return

        allow_dataset_change = False
        if self.adversarial_model_path.exists():
            try:
                from adversarial_jepa import dataset_manifest_fingerprint

                current_fingerprint = dataset_manifest_fingerprint(dataset_path)
                with np.load(self.adversarial_model_path, allow_pickle=False) as data:
                    checkpoint_fingerprint = str(data["dataset_fingerprint"][0])
                if checkpoint_fingerprint and checkpoint_fingerprint != current_fingerprint:
                    answer = QMessageBox.question(
                        self,
                        "Dataset đã thay đổi",
                        "Dataset khác fingerprint của checkpoint. Tiếp tục train incremental?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if answer != QMessageBox.Yes:
                        self.train_status = "Đã hủy: fingerprint dataset không khớp"
                        self.update()
                        return
                    allow_dataset_change = True
            except Exception as error:
                self.train_status = "Không đọc được checkpoint: " + str(error)
                self.update()
                return

        stop_event = threading.Event()
        thread = QThread(self)
        worker = trainworker(
            str(self.database.database_path),
            str(self.adversarial_model_path),
            stop_event,
            str(dataset_path),
            epochs,
            batch_size=64,
            latent_size=96,
            allow_dataset_change=allow_dataset_change,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.chay)
        worker.tien_do.connect(self.nhan_tien_do_train)
        worker.ket_qua.connect(self.nhan_ket_qua_train)
        worker.hoan_tat.connect(thread.quit)
        worker.hoan_tat.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(
            lambda thread_da_xong=thread: self.ket_thuc_train_thread(
                thread_da_xong
            )
        )

        self.train_thread = thread
        self.train_worker = worker
        self.train_stop_event = stop_event
        self.train_dang_chay = True
        self.train_status = (
            f"Khởi tạo A-JEPA v7: {epochs} epoch | {sample_count} vị trí..."
        )
        self.update()
        thread.start()

    @Slot(object)
    def nhan_tien_do_train(self, progress):
        self.monitor_train.emit(progress.copy())
        metrics = progress.get("metrics") or {}
        if "loss" not in metrics and isinstance(metrics.get("train"), dict):
            metrics = metrics["train"]
        loss = metrics.get("loss")

        if loss is None:
            loss_text = "--"
        else:
            loss_text = f"{loss:.4f}"

        self.train_status = (
            f"V7 {progress.get('phase', 'train')} | "
            f"Epoch {progress.get('epoch', '--')}/{progress.get('epochs', '--')} | "
            f"batch {progress.get('processed', '--')} | "
            f"{progress.get('progress_percent', 0.0):.1f}% | loss {loss_text}"
        )
        self.update()

    @Slot(object)
    def nhan_ket_qua_train(self, result):
        monitor_result = result.copy()
        monitor_result["event"] = "TRAIN_RESULT"
        self.monitor_train.emit(monitor_result)

        if "error" in result:
            self.train_status = "Train lỗi: " + result["error"]
        elif result.get("cancelled"):
            self.train_status = (
                f"Đã dừng | steps {result['trained_steps']}"
            )
        else:
            self.train_status = (
                f"Train xong | steps {result['trained_steps']}"
            )

        self.update()

    def ket_thuc_train_thread(self, thread_da_xong):
        if self.train_thread is not thread_da_xong:
            return

        self.train_thread = None
        self.train_worker = None
        self.train_stop_event = None
        self.train_dang_chay = False
        self.update()

    def bat_dau_hoc_sau_van_thua(self):
        if self.current_game_id is None or self.engine_color is None:
            return
        if self.learning_thread is not None:
            if self.learning_thread.isRunning():
                return

        stop_event = threading.Event()
        thread = QThread(self)
        worker = learningworker(
            str(self.database.database_path),
            self.current_game_id,
            [item.copy() for item in self.game_records],
            self.engine_color,
            stop_event,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.chay)
        worker.ket_qua.connect(self.nhan_ket_qua_learning)
        worker.hoan_tat.connect(thread.quit)
        worker.hoan_tat.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(
            lambda thread_da_xong=thread: self.ket_thuc_learning_thread(
                thread_da_xong
            )
        )
        self.learning_thread = thread
        self.learning_worker = worker
        self.learning_stop_event = stop_event
        self.learning_status = "Đang phân tích ván thua (tối đa 20 giây)..."
        self.update()
        thread.start()

    @Slot(object)
    def nhan_ket_qua_learning(self, result):
        if "error" in result:
            self.learning_status = "Học sau ván lỗi: " + result["error"]
        else:
            self.learning_status = (
                f"Đã phân tích {result['candidates']} sai lầm, "
                f"lưu {result['learned']} chỉnh sửa"
            )

        self.update()

    def ket_thuc_learning_thread(self, thread_da_xong):
        if self.learning_thread is not thread_da_xong:
            return

        self.learning_thread = None
        self.learning_worker = None
        self.learning_stop_event = None
        self.update()

    def is_pawn_move_valid(self, from_index, to_index):
        moving_piece = self.board[from_index]
        to_piece = self.board[to_index]

        #index cho đi chéo
        from_row = from_index // 8
        from_column = from_index % 8

        to_row = to_index // 8
        to_column = to_index % 8

        row_difference = to_row - from_row
        column_difference = abs(to_column - from_column)

        #quân trắng ở dưới thì sẽ - row để đi, row 1 nằm trên cùng
        if moving_piece == "P":
            if to_index == from_index - 8 and to_piece == ".":
                return True

            if from_row == 6 and to_index == from_index - 16:
                middle_index = from_index - 8

                if self.board[middle_index] == "." and to_piece == ".":
                    return True

            #ăn chéo
            if row_difference == -1 and column_difference == 1:
                if to_piece != ".":
                    return True

                if to_index == self.en_passant_target:
                    captured_pawn_index = to_index + 8

                    if self.board[captured_pawn_index] == "p":
                        return True

            return False

        #quân đen ở trên thì sẽ + row để đi
        if moving_piece == "p":
            if to_index == from_index + 8 and to_piece == ".":
                return True

            if from_row == 1 and to_index == from_index + 16:
                middle_index = from_index + 8

                if self.board[middle_index] == "." and to_piece == ".":
                    return True

            if row_difference == 1 and column_difference == 1:
                if to_piece != ".":
                    return True

                if to_index == self.en_passant_target:
                    captured_pawn_index = to_index - 8

                    if self.board[captured_pawn_index] == "P":
                        return True

            return False

        return False

    def is_knight_move_valid(self, from_index, to_index):
        from_row = from_index // 8
        from_column = from_index % 8

        to_row = to_index // 8
        to_column = to_index % 8

        row_difference = abs(from_row - to_row)
        column_difference = abs(from_column - to_column)

        if row_difference == 2 and column_difference == 1:
            return True
        if column_difference == 2 and row_difference == 1:
            return True

        return False

    def is_bishop_move_valid(self, from_index, to_index):
        from_row = from_index // 8
        from_column = from_index % 8

        to_row = to_index // 8
        to_column = to_index % 8

        row_difference = abs(from_row - to_row)
        column_difference = abs(from_column - to_column)

        if row_difference == column_difference:
            return True

        return False

    def is_bishop_path_clear(self, from_index, to_index):
        from_row = from_index // 8
        from_column = from_index % 8

        to_row = to_index // 8
        to_column = to_index % 8

        if to_row > from_row:
            row_step = 1
        else:
            row_step = -1

        if to_column > from_column:
            column_step = 1
        else:
            column_step = -1

        #xét từng vị trí trên con đường tới điểm đến
        cur_row = from_row + row_step
        cur_col = from_column + column_step

        while cur_row != to_row:
            square_index = cur_row * 8 + cur_col

            if self.board[square_index] != ".":
                return False

            cur_row = cur_row + row_step
            cur_col = cur_col + column_step

        return True

    def is_rook_move_valid(self, from_index, to_index):
        from_row = from_index // 8
        from_col = from_index % 8

        to_row = to_index // 8
        to_col = to_index % 8

        if from_row == to_row:
            return True
        if from_col == to_col:
            return True

        return False

    def is_rook_path_clear(self, from_index, to_index):
        from_row = from_index // 8
        from_col = from_index % 8

        to_row = to_index // 8
        to_col = to_index % 8

        if from_row == to_row:
            start_col = min(from_col, to_col) + 1
            end_col = max(from_col, to_col)

            for col in range(start_col, end_col):
                square_index = from_row * 8 + col

                if self.board[square_index] != ".":
                    return False

            return True

        if from_col == to_col:
            start_row = min(from_row, to_row) + 1
            end_row = max(from_row, to_row)

            for row in range(start_row, end_row):
                square_index = row * 8 + from_col

                if self.board[square_index] != ".":
                    return False

            return True

        return False

    #hậu thì nó giống tượng + xe
    def is_queen_move_valid_and_clear(self, from_index, to_index):
        ngang_doc_valid = self.is_rook_move_valid(from_index, to_index)
        xeo_xeo_valid = self.is_bishop_move_valid(from_index, to_index)

        if ngang_doc_valid:
            return self.is_rook_path_clear(from_index, to_index)

        if xeo_xeo_valid:
            return self.is_bishop_path_clear(from_index, to_index)

        return False

    def is_king_move_valid(self, from_index, to_index):
        from_row = from_index // 8
        from_col = from_index % 8

        to_row = to_index // 8
        to_col = to_index % 8

        column_difference = abs(from_col - to_col)
        row_difference = abs(from_row - to_row)

        if column_difference <= 1 and row_difference <= 1:
            return True

        return False

    def tim_vi_tri_vua(self, color):
        if color == "white":
            king_piece = "K"
        else:
            king_piece = "k"

        for index in range(64):
            if self.board[index] == king_piece:
                return index

        return None

    def is_square_attacked(self, square_index, attacker_color):
        target_row = square_index // 8
        target_col = square_index % 8

        for from_index in range(64):
            attacking_piece = self.board[from_index]

            if attacking_piece == ".":
                continue

            attacking_piece_color = self.mau_quan_co(attacking_piece)

            if attacking_piece_color != attacker_color:
                continue

            from_row = from_index // 8
            from_col = from_index % 8

            row_difference = target_row - from_row
            column_difference = abs(target_col - from_col)

            if attacking_piece == "P":
                if row_difference == -1 and column_difference == 1:
                    return True

            elif attacking_piece == "p":
                if row_difference == 1 and column_difference == 1:
                    return True

            elif attacking_piece in ("N", "n"):
                if self.is_knight_move_valid(from_index, square_index):
                    return True

            elif attacking_piece in ("B", "b"):
                if self.is_bishop_move_valid(from_index, square_index):
                    if self.is_bishop_path_clear(from_index, square_index):
                        return True

            elif attacking_piece in ("R", "r"):
                if self.is_rook_move_valid(from_index, square_index):
                    if self.is_rook_path_clear(from_index, square_index):
                        return True

            elif attacking_piece in ("Q", "q"):
                if self.is_queen_move_valid_and_clear(from_index, square_index):
                    return True

            elif attacking_piece in ("K", "k"):
                if self.is_king_move_valid(from_index, square_index):
                    return True

        return False

    def is_king_in_check(self, color):
        king_index = self.tim_vi_tri_vua(color)

        if king_index is None:
            return False

        attacker_color = self.mau_doi_thu(color)

        return self.is_square_attacked(
            king_index,
            attacker_color,
        )

    def is_castling_move_valid(self, from_index, to_index):
        moving_piece = self.board[from_index]

        if moving_piece == "K":
            if from_index != 60:
                return False

            if to_index == 62:
                if self.castling_rights["white_kingside"] == False:
                    return False

                if self.board[63] != "R":
                    return False

                if self.board[61] != "." or self.board[62] != ".":
                    return False

                if self.is_square_attacked(60, "black"):
                    return False
                if self.is_square_attacked(61, "black"):
                    return False
                if self.is_square_attacked(62, "black"):
                    return False

                return True

            if to_index == 58:
                if self.castling_rights["white_queenside"] == False:
                    return False

                if self.board[56] != "R":
                    return False

                if self.board[59] != ".":
                    return False
                if self.board[58] != ".":
                    return False
                if self.board[57] != ".":
                    return False

                if self.is_square_attacked(60, "black"):
                    return False
                if self.is_square_attacked(59, "black"):
                    return False
                if self.is_square_attacked(58, "black"):
                    return False

                return True

        if moving_piece == "k":
            if from_index != 4:
                return False

            if to_index == 6:
                if self.castling_rights["black_kingside"] == False:
                    return False

                if self.board[7] != "r":
                    return False

                if self.board[5] != "." or self.board[6] != ".":
                    return False

                if self.is_square_attacked(4, "white"):
                    return False
                if self.is_square_attacked(5, "white"):
                    return False
                if self.is_square_attacked(6, "white"):
                    return False

                return True

            if to_index == 2:
                if self.castling_rights["black_queenside"] == False:
                    return False

                if self.board[0] != "r":
                    return False

                if self.board[3] != ".":
                    return False
                if self.board[2] != ".":
                    return False
                if self.board[1] != ".":
                    return False

                if self.is_square_attacked(4, "white"):
                    return False
                if self.is_square_attacked(3, "white"):
                    return False
                if self.is_square_attacked(2, "white"):
                    return False

                return True

        return False

    def lay_thong_tin_nuoc_di(self, from_index, to_index):
        moving_piece = self.board[from_index]
        to_piece = self.board[to_index]

        move_info = {
            "moving_piece": moving_piece,
            "captured_piece": to_piece,
            "capture_index": to_index,
            "is_en_passant": False,
            "is_castling": False,
            "rook_from": None,
            "rook_to": None,
            "is_pawn_double_move": False,
            "promotion_required": False,
        }

        if moving_piece in ("P", "p"):
            if abs(to_index - from_index) == 16:
                move_info["is_pawn_double_move"] = True

            if to_index == self.en_passant_target and to_piece == ".":
                from_col = from_index % 8
                to_col = to_index % 8

                if abs(from_col - to_col) == 1:
                    move_info["is_en_passant"] = True

                    if moving_piece == "P":
                        move_info["capture_index"] = to_index + 8
                    else:
                        move_info["capture_index"] = to_index - 8

                    move_info["captured_piece"] = self.board[
                        move_info["capture_index"]
                    ]

            to_row = to_index // 8

            if moving_piece == "P" and to_row == 0:
                move_info["promotion_required"] = True

            if moving_piece == "p" and to_row == 7:
                move_info["promotion_required"] = True

        if moving_piece in ("K", "k"):
            if abs(to_index - from_index) == 2:
                move_info["is_castling"] = True

                if to_index > from_index:
                    move_info["rook_from"] = from_index + 3
                    move_info["rook_to"] = from_index + 1
                else:
                    move_info["rook_from"] = from_index - 4
                    move_info["rook_to"] = from_index - 1

        return move_info

    def is_basic_move_valid(self, from_index, to_index):
        if from_index is None:
            return False

        if to_index is None:
            return False

        if from_index < 0 or from_index > 63:
            return False

        if to_index < 0 or to_index > 63:
            return False

        if from_index == to_index:
            return False

        moving_piece = self.board[from_index]
        to_piece = self.board[to_index]

        if moving_piece == ".":
            return False

        moving_piece_color = self.mau_quan_co(moving_piece)
        to_piece_color = self.mau_quan_co(to_piece)

        if moving_piece_color == to_piece_color:
            return False

        if to_piece in ("K", "k"):
            return False

        if moving_piece in ("P", "p"):
            return self.is_pawn_move_valid(from_index, to_index)

        if moving_piece in ("N", "n"):
            return self.is_knight_move_valid(from_index, to_index)

        if moving_piece in ("B", "b"):
            if self.is_bishop_move_valid(from_index, to_index) == False:
                return False

            return self.is_bishop_path_clear(from_index, to_index)

        if moving_piece in ("R", "r"):
            if self.is_rook_move_valid(from_index, to_index) == False:
                return False

            return self.is_rook_path_clear(from_index, to_index)

        if moving_piece in ("Q", "q"):
            return self.is_queen_move_valid_and_clear(from_index, to_index)

        if moving_piece in ("K", "k"):
            if self.is_king_move_valid(from_index, to_index):
                return True

            return self.is_castling_move_valid(from_index, to_index)

        return False

    def ap_dung_nuoc_di(self, from_index, to_index, move_info, promotion_piece=None):
        moving_piece = move_info["moving_piece"]

        self.board[from_index] = "."

        if move_info["is_en_passant"]:
            self.board[move_info["capture_index"]] = "."

        if move_info["is_castling"]:
            rook_piece = self.board[move_info["rook_from"]]
            self.board[move_info["rook_from"]] = "."
            self.board[move_info["rook_to"]] = rook_piece

        if move_info["promotion_required"]:
            if promotion_piece is None:
                if moving_piece == "P":
                    promotion_piece = "Q"
                else:
                    promotion_piece = "q"

            self.board[to_index] = promotion_piece
        else:
            self.board[to_index] = moving_piece

    def hoan_tac_nuoc_di_gia_lap(self, from_index, to_index, move_info):
        moving_piece = move_info["moving_piece"]

        self.board[from_index] = moving_piece

        if move_info["is_en_passant"]:
            self.board[to_index] = "."
            self.board[move_info["capture_index"]] = move_info["captured_piece"]
        else:
            self.board[to_index] = move_info["captured_piece"]

        if move_info["is_castling"]:
            rook_piece = self.board[move_info["rook_to"]]
            self.board[move_info["rook_to"]] = "."
            self.board[move_info["rook_from"]] = rook_piece

    def is_move_valid(self, from_index, to_index):
        if from_index is None or to_index is None:
            return False
        if not (0 <= from_index < 64 and 0 <= to_index < 64):
            return False
        engine = vitriengine(self.tao_snapshot_engine(), 0.02)
        return any(
            move[0] == from_index and move[1] == to_index
            for move in engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
        )

    def tim_cac_o_valid(self, from_index):
        engine = vitriengine(self.tao_snapshot_engine(), 0.02)
        self.valid_move_index = sorted({
            move[1]
            for move in engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
            if move[0] == from_index
        })

    def co_nuoc_di_hop_le(self, color):
        snapshot = self.tao_snapshot_engine()
        snapshot["turn"] = color
        engine = vitriengine(snapshot, 0.02)
        return bool(engine.lay_tat_ca_nuoc_di_hop_le(engine.turn))

    def lay_tat_ca_nuoc_di_hop_le(self, color):
        snapshot = self.tao_snapshot_engine()
        snapshot["turn"] = color
        engine = vitriengine(snapshot, 0.02)
        return [
            (move[0], move[1])
            for move in engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
        ]

    def chon_quan_phong_cap(self, color):
        choices = ["Hậu", "Xe", "Tượng", "Mã"]

        selected_text, ok = QInputDialog.getItem(
            self,
            "Phong cấp",
            "Chọn quân để phong cấp:",
            choices,
            0,
            False,
        )

        if ok == False:
            selected_text = "Hậu"

        white_piece_map = {
            "Hậu": "Q",
            "Xe": "R",
            "Tượng": "B",
            "Mã": "N",
        }

        selected_piece = white_piece_map[selected_text]

        if color == "white":
            return selected_piece

        return selected_piece.lower()

    def cap_nhat_quyen_nhap_thanh(self, from_index, to_index, move_info):
        moving_piece = move_info["moving_piece"]
        captured_piece = move_info["captured_piece"]
        capture_index = move_info["capture_index"]

        if moving_piece == "K":
            self.castling_rights["white_kingside"] = False
            self.castling_rights["white_queenside"] = False

        elif moving_piece == "k":
            self.castling_rights["black_kingside"] = False
            self.castling_rights["black_queenside"] = False

        elif moving_piece == "R":
            if from_index == 63:
                self.castling_rights["white_kingside"] = False
            elif from_index == 56:
                self.castling_rights["white_queenside"] = False

        elif moving_piece == "r":
            if from_index == 7:
                self.castling_rights["black_kingside"] = False
            elif from_index == 0:
                self.castling_rights["black_queenside"] = False

        if captured_piece == "R":
            if capture_index == 63:
                self.castling_rights["white_kingside"] = False
            elif capture_index == 56:
                self.castling_rights["white_queenside"] = False

        elif captured_piece == "r":
            if capture_index == 7:
                self.castling_rights["black_kingside"] = False
            elif capture_index == 0:
                self.castling_rights["black_queenside"] = False

    def cap_nhat_en_passant(self, from_index, to_index, move_info):
        self.en_passant_target = None

        if move_info["is_pawn_double_move"]:
            self.en_passant_target = (from_index + to_index) // 2

    def en_passant_co_hieu_luc(self):
        if self.en_passant_target is None:
            return "-"

        target = self.en_passant_target
        target_row = target // 8
        target_col = target % 8

        if self.turn == "white":
            pawn_row = target_row + 1
            pawn_piece = "P"
        else:
            pawn_row = target_row - 1
            pawn_piece = "p"

        for pawn_col in (target_col - 1, target_col + 1):
            if pawn_row < 0 or pawn_row > 7:
                continue
            if pawn_col < 0 or pawn_col > 7:
                continue

            pawn_index = pawn_row * 8 + pawn_col

            if self.board[pawn_index] == pawn_piece:
                return str(target)

        return "-"

    def tao_key_position(self):
        board_key = "".join(self.board)

        castling_key = ""

        if self.castling_rights["white_kingside"]:
            castling_key += "K"
        if self.castling_rights["white_queenside"]:
            castling_key += "Q"
        if self.castling_rights["black_kingside"]:
            castling_key += "k"
        if self.castling_rights["black_queenside"]:
            castling_key += "q"

        if castling_key == "":
            castling_key = "-"

        en_passant_key = self.en_passant_co_hieu_luc()

        return (
            board_key,
            self.turn,
            castling_key,
            en_passant_key,
        )

    def ghi_nhan_position(self):
        key = self.tao_key_position()
        self.position_counts[key] = self.position_counts.get(key, 0) + 1

    def is_lap_lai_3_lan(self):
        key = self.tao_key_position()
        return self.position_counts.get(key, 0) >= 3

    def is_thieu_quan(self):
        non_king_pieces = []

        for index, piece in enumerate(self.board):
            if piece == ".":
                continue
            if piece in ("K", "k"):
                continue

            non_king_pieces.append((index, piece))

        if len(non_king_pieces) == 0:
            return True

        if len(non_king_pieces) == 1:
            piece = non_king_pieces[0][1]

            if piece in ("B", "b", "N", "n"):
                return True

        if len(non_king_pieces) == 2:
            first_index, first_piece = non_king_pieces[0]
            second_index, second_piece = non_king_pieces[1]

            if first_piece in ("B", "b") and second_piece in ("B", "b"):
                first_color = self.mau_quan_co(first_piece)
                second_color = self.mau_quan_co(second_piece)

                if first_color != second_color:
                    first_square_color = (
                        (first_index // 8) + (first_index % 8)
                    ) % 2
                    second_square_color = (
                        (second_index // 8) + (second_index % 8)
                    ) % 2

                    if first_square_color == second_square_color:
                        return True

        return False

    def tao_pgn_tu_game_records(self, result_token):
        move_parts = []

        for index in range(0, len(self.game_records), 2):
            move_number = index // 2 + 1
            white_san = self.game_records[index]["san"]
            move_text = f"{move_number}. {white_san}"

            if index + 1 < len(self.game_records):
                move_text += " " + self.game_records[index + 1]["san"]

            move_parts.append(move_text)

        return " ".join(move_parts + [result_token])

    def luu_game_hien_tai(self, result_text):
        if self.game_da_luu:
            return
        if self.player_color is None or self.engine_color is None:
            return

        if result_text.startswith("Trắng thắng"):
            winner_color = "white"
            result_token = "1-0"
        elif result_text.startswith("Đen thắng"):
            winner_color = "black"
            result_token = "0-1"
        else:
            winner_color = None
            result_token = "1/2-1/2"

        source_data = {
            "started_at": self.game_started_at,
            "player_color": self.player_color,
            "engine_color": self.engine_color,
            "moves": [item["move_text"] for item in self.game_records],
            "result": result_token,
        }
        source_hash = hashlib.sha256(
            json.dumps(
                source_data,
                sort_keys=True,
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()

        try:
            game_id, is_new = self.database.luu_game({
                "created_at": self.game_started_at,
                "source": "PLAYED",
                "source_hash": source_hash,
                "player_color": self.player_color,
                "engine_color": self.engine_color,
                "winner_color": winner_color,
                "result": result_token,
                "reason": result_text,
                "move_count": (len(self.game_records) + 1) // 2,
                "moves": self.game_records,
                "evals": [
                    item["evaluation"]
                    for item in self.game_records
                ],
                "positions": [
                    item["position_json"]
                    for item in self.game_records
                ],
                "white_time_ms": self.white_time_ms,
                "black_time_ms": self.black_time_ms,
                "headers": {
                    "White": "Player" if self.player_color == "white" else "Engine",
                    "Black": "Player" if self.player_color == "black" else "Engine",
                    "Result": result_token,
                },
                "pgn_text": self.tao_pgn_tu_game_records(result_token),
            })

            if is_new:
                if winner_color == self.engine_color:
                    engine_outcome = 1.0
                    learning_weight = 0.02
                elif winner_color is None:
                    engine_outcome = 0.0
                    learning_weight = 0.005
                else:
                    engine_outcome = -1.0
                    learning_weight = 0.01

                engine_records = [
                    (index, item)
                    for index, item in enumerate(self.game_records)
                    if item["side"] == self.engine_color
                ]
                contributions = []
                samples = []

                for record_index, item in engine_records:
                    contributions.append({
                        "position_key": item["position_key"],
                        "move_text": item["move_text"],
                        "side": self.engine_color,
                        "source_type": "PERSONAL",
                        "outcome": engine_outcome,
                        "weight": learning_weight,
                        "move_number": record_index + 1,
                        "is_opening": item["is_opening"],
                    })

                    if winner_color != self.engine_color:
                        continue

                    if record_index + 1 < len(self.game_records):
                        future2_json = self.game_records[
                            record_index + 1
                        ]["next_position_json"]
                    else:
                        future2_json = None

                    if record_index + 3 < len(self.game_records):
                        future4_json = self.game_records[
                            record_index + 3
                        ]["next_position_json"]
                    else:
                        future4_json = None

                    samples.append({
                        "position_key": item["position_key"],
                        "position_json": item["position_json"],
                        "move_text": item["move_text"],
                        "next_position_json": item[
                            "next_position_json"
                        ],
                        "future2_json": future2_json,
                        "future4_json": future4_json,
                        "target": 1.0,
                        "source_type": "PERSONAL",
                    })

                self.database.them_contributions(game_id, contributions)
                self.database.them_model_samples(game_id, samples)
                self.database.rebuild_opening_book()

            self.current_game_id = game_id
            self.game_da_luu = True
        except Exception as error:
            print(f"Lỗi lưu ván: {error}")

    def ket_thuc_game(self, result_text):
        self.dung_search_engine()
        self.clock_dang_chay = False
        self.clock_moc_thoi_gian = None
        self.game_over = True
        self.game_result = result_text
        self.selected_index = None
        self.valid_move_index = []
        self.drag_start_index = None
        self.drag_piece = None
        self.is_dragging = False

        self.luu_game_hien_tai(result_text)

        engine_lost = (
            (self.engine_color == "white" and result_text.startswith("Đen thắng"))
            or (
                self.engine_color == "black"
                and result_text.startswith("Trắng thắng")
            )
        )

        if engine_lost:
            self.bat_dau_hoc_sau_van_thua()

        self.cap_nhat_tieu_de()
        self.update()

    def kiem_tra_trang_thai_game(self):
        current_color = self.turn
        current_color_in_check = self.is_king_in_check(current_color)
        current_color_has_move = self.co_nuoc_di_hop_le(current_color)

        if current_color_has_move == False:
            if current_color_in_check:
                winner = self.mau_doi_thu(current_color)

                if winner == "white":
                    self.ket_thuc_game("Trắng thắng")
                else:
                    self.ket_thuc_game("Đen thắng")
            else:
                self.ket_thuc_game("Hòa stalemate")

            return

        if self.is_thieu_quan():
            self.ket_thuc_game("Hòa thiếu quân")
            return

        if self.is_lap_lai_3_lan():
            self.ket_thuc_game("Hòa lặp lại 3 lần")
            return

        self.cap_nhat_tieu_de()

    def tinh_evaluation_material(self):
        piece_value = {
            "P": 1.0,
            "N": 3.0,
            "B": 3.0,
            "R": 5.0,
            "Q": 9.0,
            "K": 0.0,
        }

        score = 0.0

        for piece in self.board:
            if piece == ".":
                continue

            value = piece_value[piece.upper()]

            if piece.isupper():
                score = score + value
            else:
                score = score - value

        return round(score, 1)

    def ve_evaluation_bar(
        self,
        painter,
        startx,
        starty,
        board_size,
        square_size,
    ):
        bar_width = max(30, int(square_size * 0.50))
        bar_gap = max(8, int(square_size * 0.14))
        bar_x = startx - bar_gap - bar_width

        max_score = 10.0
        limited_score = max(
            -max_score,
            min(max_score, self.evaluation_score),
        )

        white_ratio = 0.5 + limited_score / (max_score * 2)
        white_height = board_size * white_ratio
        black_height = board_size - white_height

        if self.player_color == "black":
            white_rect = QRectF(
                bar_x,
                starty,
                bar_width,
                white_height,
            )
            black_rect = QRectF(
                bar_x,
                starty + white_height,
                bar_width,
                black_height,
            )
        else:
            black_rect = QRectF(
                bar_x,
                starty,
                bar_width,
                black_height,
            )
            white_rect = QRectF(
                bar_x,
                starty + black_height,
                bar_width,
                white_height,
            )

        painter.fillRect(black_rect, QColor("#25211E"))
        painter.fillRect(white_rect, QColor("#F4EEE4"))

        border_pen = QPen(QColor("#4E3B2C"))
        border_pen.setWidth(3)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(
            QRectF(
                bar_x,
                starty,
                bar_width,
                board_size,
            )
        )

        if self.evaluation_score > 0:
            score_text = f"+{self.evaluation_score:.1f}"
            if self.player_color == "black":
                text_y = starty + square_size * 0.10
            else:
                text_y = starty + board_size - square_size * 0.42
            text_color = QColor("#25211E")
        elif self.evaluation_score < 0:
            score_text = f"{self.evaluation_score:.1f}"
            if self.player_color == "black":
                text_y = starty + board_size - square_size * 0.42
            else:
                text_y = starty + square_size * 0.10
            text_color = QColor("#F4EEE4")
        else:
            score_text = "0.0"
            text_y = starty + board_size / 2 - square_size * 0.16
            text_color = QColor("#F4EEE4")

        text_rect = QRectF(
            bar_x,
            text_y,
            bar_width,
            square_size * 0.32,
        )

        painter.setPen(text_color)
        painter.setFont(
            QFont(
                "Arial",
                max(8, int(square_size * 0.13)),
                QFont.Bold,
            )
        )
        painter.drawText(
            text_rect,
            Qt.AlignCenter,
            score_text,
        )

    def ve_mot_clock(self, painter, rect, color, owner_text):
        if color == "white":
            background = QColor("#F4EEE4")
            text_color = QColor("#25211E")
            color_text = "TRẮNG"
        else:
            background = QColor("#25211E")
            text_color = QColor("#F4EEE4")
            color_text = "ĐEN"

        painter.fillRect(rect, background)

        if self.turn == color and self.game_over == False:
            border_color = QColor("#D59A45")
            border_width = 4
        else:
            border_color = QColor("#6E513B")
            border_width = 2

        border_pen = QPen(border_color)
        border_pen.setWidth(border_width)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)

        label_rect = QRectF(
            rect.x() + 6,
            rect.y() + 5,
            rect.width() - 12,
            rect.height() * 0.28,
        )
        time_rect = QRectF(
            rect.x() + 4,
            rect.y() + rect.height() * 0.27,
            rect.width() - 8,
            rect.height() * 0.66,
        )

        painter.setPen(text_color)
        painter.setFont(
            QFont(
                "Arial",
                max(8, int(rect.height() * 0.12)),
                QFont.Bold,
            )
        )
        painter.drawText(
            label_rect,
            Qt.AlignCenter,
            f"{owner_text} • {color_text}",
        )

        painter.setFont(
            QFont(
                "Arial",
                max(18, int(rect.height() * 0.29)),
                QFont.Bold,
            )
        )
        painter.drawText(
            time_rect,
            Qt.AlignCenter,
            self.doi_clock_thanh_text(self.lay_clock_time(color)),
        )

    def ve_hai_clock(
        self,
        painter,
        startx,
        starty,
        board_size,
        square_size,
    ):
        if self.player_color is None:
            self.clock_top_rect = QRectF()
            self.clock_bottom_rect = QRectF()
            return

        clock_x = startx + board_size + 15
        available_width = self.width() - clock_x - 12
        clock_width = min(145, max(90, available_width))
        clock_height = max(72, min(96, int(square_size * 1.10)))
        edge_gap = int(square_size * 0.55)

        self.clock_top_rect = QRectF(
            clock_x,
            starty + edge_gap,
            clock_width,
            clock_height,
        )
        self.clock_bottom_rect = QRectF(
            clock_x,
            starty + board_size - edge_gap - clock_height,
            clock_width,
            clock_height,
        )
        self.ve_mot_clock(
            painter,
            self.clock_top_rect,
            self.engine_color,
            "ENGINE",
        )
        self.ve_mot_clock(
            painter,
            self.clock_bottom_rect,
            self.player_color,
            "BẠN",
        )

    def ve_control_panel(
        self,
        painter,
        startx,
        starty,
        board_size,
        square_size,
    ):
        panel_x = startx + board_size + 15
        panel_width = min(145, max(90, self.width() - panel_x - 12))
        button_height = max(34, int(square_size * 0.48))
        gap = 10
        total_height = button_height * 3 + gap * 2
        panel_y = starty + (board_size - total_height) / 2

        self.history_button_rect = QRectF(
            panel_x,
            panel_y,
            panel_width,
            button_height,
        )
        self.import_button_rect = QRectF(
            panel_x,
            panel_y + button_height + gap,
            panel_width,
            button_height,
        )
        self.train_button_rect = QRectF(
            panel_x,
            panel_y + (button_height + gap) * 2,
            panel_width,
            button_height,
        )

        button_data = (
            (self.history_button_rect, "LỊCH SỬ"),
            (
                self.import_button_rect,
                "IMPORT..." if self.import_dang_chay else "IMPORT PGN",
            ),
            (
                self.train_button_rect,
                "DỪNG TRAIN" if self.train_dang_chay else "TRAIN MODEL",
            ),
        )

        for rect, text_value in button_data:
            painter.fillRect(rect, QColor("#D9BE97"))
            pen = QPen(QColor("#4E3B2C"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)
            painter.setPen(QColor("#35271D"))
            painter.setFont(
                QFont(
                    "Arial",
                    max(8, int(button_height * 0.18)),
                    QFont.Bold,
                )
            )
            painter.drawText(rect, Qt.AlignCenter, text_value)

        status_parts = [
            item
            for item in (
                self.import_status,
                self.train_status,
                self.learning_status,
            )
            if item
        ]

        if status_parts:
            status_rect = QRectF(
                panel_x,
                self.train_button_rect.bottom() + 8,
                panel_width,
                max(45, int(square_size * 0.8)),
            )
            painter.setPen(QColor("#4E3B2C"))
            painter.setFont(
                QFont("Arial", max(7, int(square_size * 0.10)))
            )
            painter.drawText(
                status_rect,
                Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap,
                "\n".join(status_parts),
            )

    def tai_history(self):
        self.history_rows = self.database.lay_history(
            limit=5,
            offset=self.history_page * 5,
        )

    def mo_history(self):
        self.history_open = True
        self.history_detail = None
        self.history_page = 0
        self.history_detail_page = 0
        self.tai_history()
        self.update()

    def format_history_time(self, time_ms):
        if time_ms is None:
            return "--:--.-"

        return self.doi_clock_thanh_text(time_ms)

    def ve_history_list(
        self,
        painter,
        panel_x,
        panel_y,
        panel_width,
        panel_height,
    ):
        self.history_row_rects = []
        self.history_delete_rects = []
        content_top = panel_y + panel_height * 0.16
        content_height = panel_height * 0.68
        row_height = content_height / 5

        if len(self.history_rows) == 0:
            empty_rect = QRectF(
                panel_x + panel_width * 0.08,
                content_top,
                panel_width * 0.84,
                content_height,
            )
            painter.setPen(QColor("#F7EBD8"))
            painter.setFont(QFont("Arial", 16, QFont.Bold))
            painter.drawText(
                empty_rect,
                Qt.AlignCenter,
                "CHƯA CÓ VÁN ĐÃ CHƠI",
            )

        for index, row in enumerate(self.history_rows):
            row_rect = QRectF(
                panel_x + panel_width * 0.05,
                content_top + index * row_height + 3,
                panel_width * 0.90,
                row_height - 6,
            )
            delete_width = max(58, panel_width * 0.13)
            delete_rect = QRectF(
                row_rect.right() - delete_width - 5,
                row_rect.y() + 5,
                delete_width,
                row_rect.height() - 10,
            )
            open_rect = QRectF(
                row_rect.x(),
                row_rect.y(),
                row_rect.width() - delete_width - 10,
                row_rect.height(),
            )
            self.history_row_rects.append((row["id"], open_rect))
            self.history_delete_rects.append((row["id"], delete_rect))

            painter.fillRect(row_rect, QColor(116, 82, 57, 210))
            painter.fillRect(delete_rect, QColor("#B75A4B"))
            painter.setPen(QColor("#F8EEDA"))
            painter.setFont(QFont("Arial", 10, QFont.Bold))

            created_text = row["created_at"].replace("T", " ")[:16]
            player_text = "Trắng" if row["player_color"] == "white" else "Đen"
            info_text = (
                f"{created_text}  |  Bạn: {player_text}\n"
                f"{row['reason']}  |  {row['move_count']} nước  |  "
                f"{self.format_history_time(row['white_time_ms'])} / "
                f"{self.format_history_time(row['black_time_ms'])}"
            )
            painter.drawText(
                open_rect.adjusted(10, 2, -5, -2),
                Qt.AlignVCenter | Qt.AlignLeft | Qt.TextWordWrap,
                info_text,
            )
            painter.drawText(delete_rect, Qt.AlignCenter, "XÓA")

        total_games = self.database.dem_history()
        total_pages = max(1, math.ceil(total_games / 5))
        footer_y = panel_y + panel_height * 0.88
        button_width = panel_width * 0.18
        button_height = panel_height * 0.07
        self.history_prev_rect = QRectF(
            panel_x + panel_width * 0.22,
            footer_y,
            button_width,
            button_height,
        )
        self.history_next_rect = QRectF(
            panel_x + panel_width * 0.60,
            footer_y,
            button_width,
            button_height,
        )

        for rect, text_value in (
            (self.history_prev_rect, "TRƯỚC"),
            (self.history_next_rect, "SAU"),
        ):
            painter.fillRect(rect, QColor("#D9BE97"))
            painter.setPen(QColor("#3A2A20"))
            painter.drawText(rect, Qt.AlignCenter, text_value)

        page_rect = QRectF(
            panel_x + panel_width * 0.42,
            footer_y,
            panel_width * 0.16,
            button_height,
        )
        painter.setPen(QColor("#F8EEDA"))
        painter.drawText(
            page_rect,
            Qt.AlignCenter,
            f"{self.history_page + 1}/{total_pages}",
        )

    def ve_history_detail(
        self,
        painter,
        panel_x,
        panel_y,
        panel_width,
        panel_height,
    ):
        detail = self.history_detail
        moves = json.loads(detail.get("moves_json", "[]"))
        evals = json.loads(detail.get("evals_json", "[]"))
        per_page = 24
        total_pages = max(1, math.ceil(len(moves) / per_page))
        self.history_detail_page = min(
            self.history_detail_page,
            total_pages - 1,
        )
        start = self.history_detail_page * per_page
        end = min(len(moves), start + per_page)
        contribution_moves = {
            row["move_number"]
            for row in detail.get("contributions", [])
        }
        lines = []

        for index in range(start, end):
            move_item = moves[index]

            if isinstance(move_item, dict):
                san_text = move_item.get("san", move_item.get("move_text", ""))
                uci_text = move_item.get("move_text", "")
                evaluation = move_item.get(
                    "evaluation",
                    evals[index] if index < len(evals) else 0.0,
                )
            else:
                san_text = str(move_item)
                uci_text = str(move_item)
                evaluation = evals[index] if index < len(evals) else 0.0

            learned_text = " • học" if index + 1 in contribution_moves else ""
            lines.append(
                f"{index + 1:>3}. {san_text} ({uci_text})  "
                f"eval {float(evaluation):+.2f}{learned_text}"
            )

        info_rect = QRectF(
            panel_x + panel_width * 0.07,
            panel_y + panel_height * 0.14,
            panel_width * 0.86,
            panel_height * 0.14,
        )
        move_rect = QRectF(
            panel_x + panel_width * 0.07,
            panel_y + panel_height * 0.29,
            panel_width * 0.86,
            panel_height * 0.56,
        )
        painter.setPen(QColor("#F8EEDA"))
        painter.setFont(QFont("Arial", 11, QFont.Bold))
        painter.drawText(
            info_rect,
            Qt.AlignTop | Qt.TextWordWrap,
            (
                f"{detail['created_at'].replace('T', ' ')[:19]} | "
                f"{detail['reason']} | {detail['move_count']} nước\n"
                f"Correction: {len(detail.get('corrections', []))} | "
                f"Contribution: {len(detail.get('contributions', []))}"
            ),
        )
        painter.setFont(QFont("Consolas", 10))
        painter.drawText(
            move_rect,
            Qt.AlignTop | Qt.AlignLeft,
            "\n".join(lines),
        )

        button_width = panel_width * 0.18
        button_height = panel_height * 0.07
        footer_y = panel_y + panel_height * 0.89
        self.history_back_rect = QRectF(
            panel_x + panel_width * 0.05,
            footer_y,
            button_width,
            button_height,
        )
        self.history_prev_rect = QRectF(
            panel_x + panel_width * 0.31,
            footer_y,
            button_width,
            button_height,
        )
        self.history_next_rect = QRectF(
            panel_x + panel_width * 0.69,
            footer_y,
            button_width,
            button_height,
        )

        for rect, text_value in (
            (self.history_back_rect, "QUAY LẠI"),
            (self.history_prev_rect, "TRƯỚC"),
            (self.history_next_rect, "SAU"),
        ):
            painter.fillRect(rect, QColor("#D9BE97"))
            painter.setPen(QColor("#3A2A20"))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(rect, Qt.AlignCenter, text_value)

        painter.setPen(QColor("#F8EEDA"))
        page_rect = QRectF(
            panel_x + panel_width * 0.51,
            footer_y,
            panel_width * 0.16,
            button_height,
        )
        painter.drawText(
            page_rect,
            Qt.AlignCenter,
            f"{self.history_detail_page + 1}/{total_pages}",
        )

    def ve_history_overlay(
        self,
        painter,
        startx,
        starty,
        board_size,
    ):
        if self.history_open == False:
            return

        painter.fillRect(
            QRectF(startx, starty, board_size, board_size),
            QColor(20, 14, 10, 150),
        )
        panel_x = startx + board_size * 0.04
        panel_y = starty + board_size * 0.04
        panel_width = board_size * 0.92
        panel_height = board_size * 0.92
        panel_rect = QRectF(
            panel_x,
            panel_y,
            panel_width,
            panel_height,
        )
        painter.fillRect(panel_rect, QColor(92, 66, 45, 245))
        pen = QPen(QColor("#E6CDAA"))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(panel_rect)
        painter.setPen(QColor("#FFF1DA"))
        painter.setFont(QFont("Arial", 19, QFont.Bold))
        title_rect = QRectF(
            panel_x + panel_width * 0.08,
            panel_y + panel_height * 0.03,
            panel_width * 0.84,
            panel_height * 0.08,
        )
        title_text = "CHI TIẾT VÁN" if self.history_detail else "LỊCH SỬ"
        painter.drawText(title_rect, Qt.AlignCenter, title_text)
        self.history_close_rect = QRectF(
            panel_x + panel_width * 0.91,
            panel_y + panel_height * 0.02,
            panel_width * 0.06,
            panel_height * 0.07,
        )
        painter.fillRect(self.history_close_rect, QColor("#B75A4B"))
        painter.drawText(self.history_close_rect, Qt.AlignCenter, "×")

        if self.history_detail is None:
            self.ve_history_list(
                painter,
                panel_x,
                panel_y,
                panel_width,
                panel_height,
            )
        else:
            self.ve_history_detail(
                painter,
                panel_x,
                panel_y,
                panel_width,
                panel_height,
            )

    def xu_ly_history_click(self, position):
        if self.history_close_rect.contains(position):
            self.history_open = False
            self.history_detail = None
            self.update()
            return

        if self.history_detail is not None:
            moves = json.loads(self.history_detail.get("moves_json", "[]"))
            total_pages = max(1, math.ceil(len(moves) / 24))

            if self.history_back_rect.contains(position):
                self.history_detail = None
                self.tai_history()
            elif self.history_prev_rect.contains(position):
                self.history_detail_page = max(
                    0,
                    self.history_detail_page - 1,
                )
            elif self.history_next_rect.contains(position):
                self.history_detail_page = min(
                    total_pages - 1,
                    self.history_detail_page + 1,
                )

            self.update()
            return

        for game_id, delete_rect in self.history_delete_rects:
            if delete_rect.contains(position):
                self.database.xoa_game(game_id)
                total_games = self.database.dem_history()
                max_page = max(0, math.ceil(total_games / 5) - 1)
                self.history_page = min(self.history_page, max_page)
                self.tai_history()
                self.update()
                return

        for game_id, row_rect in self.history_row_rects:
            if row_rect.contains(position):
                self.history_detail = self.database.lay_game_detail(game_id)
                self.history_detail_page = 0
                self.update()
                return

        total_games = self.database.dem_history()
        max_page = max(0, math.ceil(total_games / 5) - 1)

        if self.history_prev_rect.contains(position):
            self.history_page = max(0, self.history_page - 1)
            self.tai_history()
        elif self.history_next_rect.contains(position):
            self.history_page = min(max_page, self.history_page + 1)
            self.tai_history()

        self.update()

    def move_piece(
        self,
        from_index,
        to_index,
        la_nuoc_engine=False,
        promotion_piece_engine=None,
        evaluation_engine=None,
    ):
        if self.dang_chon_mau:
            return False

        if self.game_over:
            return False

        if from_index is None or to_index is None:
            return False

        moving_piece = self.board[from_index]
        moving_piece_color = self.mau_quan_co(moving_piece)

        if moving_piece_color != self.turn:
            return False

        if la_nuoc_engine:
            if moving_piece_color != self.engine_color:
                return False
        else:
            if moving_piece_color != self.player_color:
                return False

        if self.is_move_valid(from_index, to_index) == False:
            return False

        self.cap_nhat_clock()

        if self.game_over:
            return False

        move_info = self.lay_thong_tin_nuoc_di(from_index, to_index)
        promotion_piece = None

        if move_info["promotion_required"]:
            if la_nuoc_engine:
                if promotion_piece_engine is not None:
                    promotion_piece = promotion_piece_engine
                elif moving_piece_color == "white":
                    promotion_piece = "Q"
                else:
                    promotion_piece = "q"
            else:
                promotion_piece = self.chon_quan_phong_cap(
                    moving_piece_color
                )

                self.cap_nhat_clock()

                if self.game_over:
                    return False

        move_for_record = (
            from_index,
            to_index,
            promotion_piece,
        )
        before_snapshot = self.tao_snapshot_engine()
        record_engine = vitriengine(before_snapshot, 0.02)
        record_engine.position_counts[
            record_engine.tao_key_position()
        ] = 1

        legal_moves_for_san = record_engine.lay_tat_ca_nuoc_di_hop_le(
            record_engine.turn
        )
        try:
            san_text = self.pgn_parser.tao_san(
                record_engine,
                move_for_record,
                legal_moves_for_san,
            )
        except Exception:
            san_text = move_thanh_text(move_for_record)

        position_key_text = key_thanh_text(
            record_engine.tao_key_position()
        )
        is_opening_record = self.pgn_parser.la_opening(
            before_snapshot,
            len(self.game_records),
        )

        # Apply through the same exact state machine used by search.  The GUI
        # retains presentation helpers, but no longer owns a second mutable
        # implementation of castling, en-passant, promotion or halfmove rules.
        if move_for_record not in legal_moves_for_san:
            return False
        record_engine.thuc_hien_nuoc_di(move_for_record)
        self.board = record_engine.board.copy()
        self.turn = record_engine.turn
        self.castling_rights = record_engine.castling_rights.copy()
        self.en_passant_target = record_engine.en_passant_target
        self.halfmove_clock = record_engine.halfmove_clock

        self.cong_increment_clock(moving_piece_color)
        self.clock_moc_thoi_gian = time.perf_counter()

        self.selected_index = None
        self.valid_move_index = []
        self.drag_start_index = None
        self.drag_piece = None
        self.is_dragging = False

        self.ghi_nhan_position()

        if evaluation_engine is None:
            self.evaluation_score = self.tinh_evaluation_position()
        else:
            self.evaluation_score = round(float(evaluation_engine), 2)

        after_snapshot = self.tao_snapshot_engine()
        self.game_records.append({
            "ply": len(self.game_records),
            "side": moving_piece_color,
            "is_engine": la_nuoc_engine,
            "position_key": position_key_text,
            "position_json": snapshot_thanh_json(before_snapshot),
            "move_text": move_thanh_text(move_for_record),
            "san": san_text,
            "next_position_json": snapshot_thanh_json(after_snapshot),
            "evaluation": self.evaluation_score,
            "white_time_ms": round(self.white_time_ms, 1),
            "black_time_ms": round(self.black_time_ms, 1),
            "is_opening": is_opening_record,
            "search": self.thong_ke_search.copy()
            if la_nuoc_engine
            else {},
        })

        self.kiem_tra_trang_thai_game()
        self.update()

        if self.game_over == False:
            if self.turn == self.engine_color:
                if la_nuoc_engine == False:
                    QTimer.singleShot(250, self.bat_dau_search_engine)

        return True

    def ve_bang_chon_mau(
        self,
        painter,
        startx,
        starty,
        board_size,
    ):
        painter.fillRect(
            QRectF(startx, starty, board_size, board_size),
            QColor(20, 14, 10, 75),
        )

        panel_size = int(board_size * 0.46)
        panel_x = startx + (board_size - panel_size) / 2
        panel_y = starty + (board_size - panel_size) / 2

        panel_rect = QRectF(
            panel_x,
            panel_y,
            panel_size,
            panel_size,
        )

        painter.save()
        painter.setOpacity(0.70)
        painter.fillRect(panel_rect, QColor(92, 66, 45))
        painter.restore()

        panel_pen = QPen(QColor(230, 205, 171))
        panel_pen.setWidth(max(2, int(panel_size * 0.012)))
        painter.setPen(panel_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(panel_rect)

        painter.setPen(QColor(255, 244, 222))
        painter.setFont(
            QFont(
                "Arial",
                max(20, int(panel_size * 0.085)),
                QFont.Bold,
            )
        )

        title_rect = QRectF(
            panel_x + panel_size * 0.08,
            panel_y + panel_size * 0.12,
            panel_size * 0.84,
            panel_size * 0.18,
        )

        painter.drawText(
            title_rect,
            Qt.AlignCenter,
            "CHỌN MÀU",
        )

        button_width = panel_size * 0.68
        button_height = panel_size * 0.18
        button_x = panel_x + (panel_size - button_width) / 2

        self.white_button_rect = QRectF(
            button_x,
            panel_y + panel_size * 0.42,
            button_width,
            button_height,
        )

        self.black_button_rect = QRectF(
            button_x,
            panel_y + panel_size * 0.67,
            button_width,
            button_height,
        )

        painter.fillRect(
            self.white_button_rect,
            QColor(244, 238, 228),
        )

        painter.fillRect(
            self.black_button_rect,
            QColor(37, 33, 30),
        )

        button_pen = QPen(QColor(67, 45, 31))
        button_pen.setWidth(max(2, int(panel_size * 0.012)))
        painter.setPen(button_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.white_button_rect)
        painter.drawRect(self.black_button_rect)

        painter.setFont(
            QFont(
                "Arial",
                max(15, int(panel_size * 0.060)),
                QFont.Bold,
            )
        )

        painter.setPen(QColor(37, 33, 30))
        painter.drawText(
            self.white_button_rect,
            Qt.AlignCenter,
            "TRẮNG",
        )

        painter.setPen(QColor(244, 238, 228))
        painter.drawText(
            self.black_button_rect,
            Qt.AlignCenter,
            "ĐEN",
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        background_color = QColor("#F5EEDC")
        light_square = QColor("#E6D5B8")
        dark_square = QColor("#7A5C45")
        border_color = QColor("#4E3B2C")

        selected_square_color = QColor("#20F0E8")
        valid_move_dot_color = QColor("#2F9E9E")
        capture_square_color = QColor("#C96B5A")
        check_square_color = QColor("#D94C4C")

        painter.fillRect(self.rect(), background_color)

        startx, starty, board_size, square_size = self.tinhtoan_kich_co()

        self.ve_evaluation_bar(
            painter,
            startx,
            starty,
            board_size,
            square_size,
        )

        self.ve_hai_clock(
            painter,
            startx,
            starty,
            board_size,
            square_size,
        )

        self.ve_control_panel(
            painter,
            startx,
            starty,
            board_size,
            square_size,
        )

        white_king_index = self.tim_vi_tri_vua("white")
        black_king_index = self.tim_vi_tri_vua("black")

        white_king_in_check = self.is_king_in_check("white")
        black_king_in_check = self.is_king_in_check("black")

        for display_row in range(8):
            for display_col in range(8):
                x = startx + (square_size * display_col)
                y = starty + (square_size * display_row)

                square_rect = QRect(
                    x,
                    y,
                    square_size,
                    square_size,
                )

                if (display_row + display_col) % 2 == 0:
                    painter.fillRect(square_rect, light_square)
                else:
                    painter.fillRect(square_rect, dark_square)

                index = self.index_tu_o_hien_thi(
                    display_row,
                    display_col,
                )
                piece = self.board[index]

                if index in self.valid_move_index:
                    if piece != ".":
                        painter.fillRect(
                            square_rect,
                            capture_square_color,
                        )
                    elif self.selected_index is not None:
                        selected_piece = self.board[self.selected_index]

                        if selected_piece in ("P", "p"):
                            if index == self.en_passant_target:
                                painter.fillRect(
                                    square_rect,
                                    capture_square_color,
                                )

                if index == self.selected_index:
                    painter.fillRect(
                        square_rect,
                        selected_square_color,
                    )

                if white_king_in_check:
                    if index == white_king_index:
                        painter.fillRect(
                            square_rect,
                            check_square_color,
                        )

                if black_king_in_check:
                    if index == black_king_index:
                        painter.fillRect(
                            square_rect,
                            check_square_color,
                        )

                if index in self.valid_move_index:
                    is_en_passant_capture = False

                    if self.selected_index is not None:
                        selected_piece = self.board[self.selected_index]

                        if selected_piece in ("P", "p"):
                            if index == self.en_passant_target:
                                is_en_passant_capture = True

                    if piece == "." and is_en_passant_capture == False:
                        dot_diameter = int(square_size * 0.40)

                        dot_x = x + (square_size - dot_diameter) / 2
                        dot_y = y + (square_size - dot_diameter) / 2

                        dot_rect = QRectF(
                            dot_x,
                            dot_y,
                            dot_diameter,
                            dot_diameter,
                        )

                        painter.setPen(Qt.NoPen)
                        painter.setBrush(valid_move_dot_color)
                        painter.drawEllipse(dot_rect)

                if self.is_dragging and index == self.drag_start_index:
                    continue

                if piece != ".":
                    renderer = self.piece_renderers.get(piece)

                    #tìm asset cho piece
                    if renderer is not None:
                        piece_rect = QRectF(square_rect)
                        renderer.render(painter, piece_rect)

                    #nếu ko có asset thì viết chữ tạm (hope not)
                    else:
                        painter.setPen(QColor("#2F241B"))
                        painter.setFont(
                            QFont(
                                "DejaVu Sans",
                                int(square_size * 0.68),
                                QFont.Normal,
                            )
                        )

                        painter.drawText(
                            square_rect,
                            Qt.AlignCenter,
                            self.piece_symbols.get(piece, piece),
                        )

        pen = QPen(border_color)
        pen.setWidth(6)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        painter.drawRect(
            startx,
            starty,
            board_size,
            board_size,
        )

        #vẽ quân đang bị kéo theo chuột
        if self.is_dragging and self.drag_piece is not None:
            drag_rect = QRectF(
                self.drag_mouse_x - square_size / 2,
                self.drag_mouse_y - square_size / 2,
                square_size,
                square_size,
            )

            renderer = self.piece_renderers.get(self.drag_piece)

            if renderer is not None:
                renderer.render(painter, drag_rect)
            else:
                painter.setPen(QColor("#2F241B"))
                painter.setFont(
                    QFont(
                        "DejaVu Sans",
                        int(square_size * 0.68),
                        QFont.Normal,
                    )
                )

                painter.drawText(
                    drag_rect,
                    Qt.AlignCenter,
                    self.piece_symbols.get(self.drag_piece, self.drag_piece),
                )

        if self.dang_chon_mau:
            self.ve_bang_chon_mau(
                painter,
                startx,
                starty,
                board_size,
            )

        if self.game_over:
            painter.fillRect(
                QRectF(startx, starty, board_size, board_size),
                QColor(20, 14, 10, 75),
            )

            panel_size = int(board_size * 0.46)
            panel_x = startx + (board_size - panel_size) / 2
            panel_y = starty + (board_size - panel_size) / 2

            panel_rect = QRectF(
                panel_x,
                panel_y,
                panel_size,
                panel_size,
            )

            painter.save()
            painter.setOpacity(0.70)
            painter.fillRect(panel_rect, QColor(92, 66, 45))
            painter.restore()

            panel_pen = QPen(QColor(230, 205, 171))
            panel_pen.setWidth(max(2, int(panel_size * 0.012)))
            painter.setPen(panel_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(panel_rect)

            painter.setPen(QColor(255, 244, 222))
            painter.setFont(
                QFont(
                    "Arial",
                    max(14, int(panel_size * 0.055)),
                    QFont.Bold,
                )
            )

            title_rect = QRectF(
                panel_x + panel_size * 0.08,
                panel_y + panel_size * 0.10,
                panel_size * 0.84,
                panel_size * 0.14,
            )

            painter.drawText(
                title_rect,
                Qt.AlignCenter,
                "VÁN ĐẤU KẾT THÚC",
            )

            painter.setFont(
                QFont(
                    "Arial",
                    max(20, int(panel_size * 0.095)),
                    QFont.Bold,
                )
            )

            result_rect = QRectF(
                panel_x + panel_size * 0.08,
                panel_y + panel_size * 0.29,
                panel_size * 0.84,
                panel_size * 0.25,
            )

            painter.drawText(
                result_rect,
                Qt.AlignCenter | Qt.TextWordWrap,
                self.game_result,
            )

            button_width = panel_size * 0.64
            button_height = panel_size * 0.18
            button_x = panel_x + (panel_size - button_width) / 2
            button_y = panel_y + panel_size * 0.68

            self.restart_button_rect = QRectF(
                button_x,
                button_y,
                button_width,
                button_height,
            )

            painter.fillRect(
                self.restart_button_rect,
                QColor(225, 190, 145),
            )

            button_pen = QPen(QColor(67, 45, 31))
            button_pen.setWidth(max(2, int(panel_size * 0.012)))
            painter.setPen(button_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.restart_button_rect)

            painter.setPen(QColor(54, 36, 25))
            painter.setFont(
                QFont(
                    "Arial",
                    max(15, int(panel_size * 0.065)),
                    QFont.Bold,
                )
            )

            painter.drawText(
                self.restart_button_rect,
                Qt.AlignCenter,
                "RESTART",
            )

        self.ve_history_overlay(
            painter,
            startx,
            starty,
            board_size,
        )

    def mousePressEvent(self, event):
        if self.history_open:
            self.xu_ly_history_click(event.position())
            return

        if self.history_button_rect.contains(event.position()):
            self.mo_history()
            return

        if self.import_button_rect.contains(event.position()):
            self.bat_dau_import_pgn()
            return

        if self.train_button_rect.contains(event.position()):
            self.bat_dau_train_model()
            return

        if self.dang_chon_mau:
            if self.white_button_rect.contains(event.position()):
                self.chon_mau_nguoi_choi("white")
            elif self.black_button_rect.contains(event.position()):
                self.chon_mau_nguoi_choi("black")
            return

        if self.game_over:
            if self.restart_button_rect.contains(event.position()):
                self.khoi_dong_lai_game()
            return

        if self.turn != self.player_color:
            return

        mouse_x = event.position().x()
        mouse_y = event.position().y()

        clicked_index = self.vi_tri_piece_từ_click_chuot(
            mouse_x,
            mouse_y,
        )

        if clicked_index is None:
            self.selected_index = None
            self.valid_move_index = []
            self.drag_start_index = None
            self.drag_piece = None
            self.is_dragging = False

            self.update()
            return

        clicked_piece = self.board[clicked_index]
        clicked_piece_color = self.mau_quan_co(clicked_piece)

        if self.selected_index is not None:
            if clicked_index != self.selected_index:
                if clicked_piece_color == self.turn:
                    self.selected_index = clicked_index
                    self.tim_cac_o_valid(clicked_index)

                    self.drag_start_index = clicked_index
                    self.drag_piece = clicked_piece
                    self.drag_mouse_x = mouse_x
                    self.drag_mouse_y = mouse_y
                    self.is_dragging = False

                    self.update()
                    return

                self.move_piece(
                    self.selected_index,
                    clicked_index,
                )
                return

        if clicked_piece_color != self.turn:
            return

        self.selected_index = clicked_index
        self.tim_cac_o_valid(clicked_index)

        self.drag_start_index = clicked_index
        self.drag_piece = clicked_piece
        self.drag_mouse_x = mouse_x
        self.drag_mouse_y = mouse_y
        self.is_dragging = False

        self.update()

    def mouseMoveEvent(self, event):
        if self.history_open:
            self.setCursor(Qt.PointingHandCursor)
            return

        if self.history_button_rect.contains(event.position()):
            self.setCursor(Qt.PointingHandCursor)
            return
        if self.import_button_rect.contains(event.position()):
            self.setCursor(Qt.PointingHandCursor)
            return
        if self.train_button_rect.contains(event.position()):
            self.setCursor(Qt.PointingHandCursor)
            return

        if self.dang_chon_mau:
            if self.white_button_rect.contains(event.position()):
                self.setCursor(Qt.PointingHandCursor)
            elif self.black_button_rect.contains(event.position()):
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.unsetCursor()
            return

        if self.game_over:
            if self.restart_button_rect.contains(event.position()):
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.unsetCursor()
            return

        if self.turn != self.player_color:
            return

        if self.drag_start_index is None:
            return
        if self.drag_piece is None:
            return

        self.drag_mouse_x = event.position().x()
        self.drag_mouse_y = event.position().y()
        self.is_dragging = True

        self.update()

    def mouseReleaseEvent(self, event):
        if self.dang_chon_mau:
            return

        if self.game_over:
            return

        if self.turn != self.player_color:
            return

        if not self.is_dragging:
            self.drag_start_index = None
            self.drag_piece = None
            return

        mouse_x = event.position().x()
        mouse_y = event.position().y()

        released_index = self.vi_tri_piece_từ_click_chuot(
            mouse_x,
            mouse_y,
        )
        old_drag_start_index = self.drag_start_index

        self.drag_start_index = None
        self.drag_piece = None
        self.is_dragging = False

        self.move_piece(old_drag_start_index, released_index)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self.khoi_dong_lai_game()
            return

        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.dung_search_engine()

        if self.engine_thread is not None:
            if self.engine_thread.isRunning():
                self.engine_thread.quit()

                if self.engine_thread.wait(2000) == False:
                    event.ignore()
                    return

        if self.import_stop_event is not None:
            self.import_stop_event.set()

        if self.import_thread is not None:
            if self.import_thread.isRunning():
                self.import_thread.quit()

                if self.import_thread.wait(2000) == False:
                    event.ignore()
                    return

        if self.train_stop_event is not None:
            self.train_stop_event.set()

        if self.train_thread is not None:
            if self.train_thread.isRunning():
                self.train_thread.quit()

                if self.train_thread.wait(3000) == False:
                    event.ignore()
                    return

        if self.learning_stop_event is not None:
            self.learning_stop_event.set()

        if self.learning_thread is not None:
            if self.learning_thread.isRunning():
                self.learning_thread.quit()

                if self.learning_thread.wait(3000) == False:
                    event.ignore()
                    return

        event.accept()


class monitorwidget(QWidget):
    neon_green = QColor("#39FF14")
    neon_green_dim = QColor("#117A2B")
    neon_cyan = QColor("#00E5FF")
    neon_magenta = QColor("#FF2BD6")
    neon_orange = QColor("#FFB000")
    neon_blue = QColor("#4D7CFF")
    text_primary = QColor("#B7FFAE")
    text_muted = QColor("#63A86C")
    panel_background = QColor("#030A07")

    def __init__(self, board_widget):
        super().__init__()
        self.board_widget = board_widget
        self.setMinimumSize(1100, 700)
        self.setFocusPolicy(Qt.StrongFocus)

        self.train_history = []
        self.recent_metric_history = []
        self.max_history_storage = 12000
        self.max_plot_points = 600
        self.loss_ema = None
        self.history_start_wall_time = None
        self.training_active = False
        self.eta_seconds = None
        self.estimated_finish_timestamp = None
        self.latest_train = {}
        self.latest_metrics = {}
        self.latest_engine = {"stage": "IDLE"}
        self.last_engine_final = {}
        self.last_mcts_progress = {}
        self.latest_heatmap = None
        self.heatmap_info = {}
        self.heatmap_window_seconds = 30 * 60
        self.heatmap_min_seconds = 5 * 60
        self.heatmap_min_points = 128
        self.heatmap_last_compute = 0.0
        self.heatmap_last_prune = 0.0
        self.heatmap_metric_specs = (
            ("loss", "TOTAL", "Total loss"),
            ("latent_loss", "LATENT", "Latent loss"),
            ("value_loss", "VALUE", "Value loss"),
            ("ranking_loss", "RANK_L", "Ranking loss"),
            ("variance_loss", "VAR_L", "Variance loss"),
            ("ranking_accuracy", "RANK_A", "Ranking accuracy"),
            ("cosine_gap", "COS_G", "Cosine gap"),
            ("latent_std_mean", "LAT_STD", "Latent std mean"),
            ("effective_rank", "E_RANK", "Effective rank"),
            ("gradient_norm", "GRAD_N", "Gradient norm"),
        )
        self.log_lines = []
        self.checkpoint_steps = 0
        self.checkpoint_version = 0
        self.sample_count = 0

        try:
            dataset_manifest = self.board_widget.project_dir / "fen_dataset/dataset_manifest.json"
            if dataset_manifest.exists():
                with dataset_manifest.open("r", encoding="utf-8") as handle:
                    self.sample_count = int(json.load(handle).get("positions", 0))
            else:
                self.sample_count = self.board_widget.database.dem_model_samples()
        except Exception:
            self.sample_count = 0

        self.nap_thong_tin_checkpoint()
        self.them_log("MONITOR ONLINE")

        self.board_widget.monitor_train.connect(self.nhan_train)
        self.board_widget.monitor_engine.connect(self.nhan_engine)
        self.board_widget.monitor_state.connect(self.nhan_state)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(250)
        self.refresh_timer.timeout.connect(self.update)
        self.refresh_timer.start()

    def nap_thong_tin_checkpoint(self):
        model_path = self.board_widget.model_path
        if self.board_widget.adversarial_model_path.exists():
            model_path = self.board_widget.adversarial_model_path

        if np is None or model_path.exists() == False:
            return

        try:
            with np.load(model_path, allow_pickle=False) as data:
                if "trained_steps" in data:
                    self.checkpoint_steps = int(data["trained_steps"][0])

                if "model_version" in data:
                    self.checkpoint_version = int(data["model_version"][0])
        except Exception as error:
            self.them_log("CHECKPOINT READ ERROR: " + str(error))

    def them_log(self, text_value):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_lines.append(f"[{timestamp}] {text_value}")
        self.log_lines = self.log_lines[-8:]

    @Slot(object)
    def nhan_train(self, progress):
        if progress.get("event") == "TRAIN_RESULT":
            self.training_active = False
            self.eta_seconds = None
            self.estimated_finish_timestamp = None
            self.checkpoint_steps = int(
                progress.get("trained_steps", self.checkpoint_steps)
            )

            if "error" in progress:
                self.them_log("TRAIN ERROR: " + progress["error"])
            elif progress.get("cancelled"):
                self.them_log(
                    f"TRAIN STOPPED @ STEP {self.checkpoint_steps}"
                )
            else:
                self.them_log(
                    f"TRAIN COMPLETE @ STEP {self.checkpoint_steps}"
                )

            self.nap_thong_tin_checkpoint()
            self.update()
            return

        incoming_overall = int(progress.get("overall_processed", 0))
        incoming_total = int(progress.get("overall_total", 0))
        previous_overall = int(
            self.latest_train.get("overall_processed", 0)
        )
        previous_total = int(self.latest_train.get("overall_total", 0))

        if self.train_history and (
            incoming_overall < previous_overall
            or (
                previous_total > 0
                and incoming_total > 0
                and incoming_total != previous_total
            )
        ):
            self.train_history = []
            self.recent_metric_history = []
            self.loss_ema = None
            self.history_start_wall_time = None
            self.latest_heatmap = None
            self.heatmap_info = {}
            self.heatmap_last_compute = 0.0
            self.heatmap_last_prune = 0.0
            self.them_log("NEW TRAINING TIMELINE")

        self.latest_train = progress.copy()
        metrics = progress.get("metrics") or {}
        self.latest_metrics = metrics.copy()
        self.training_active = True
        self.eta_seconds = progress.get("eta_seconds")
        self.estimated_finish_timestamp = progress.get(
            "estimated_finish_timestamp"
        )
        self.checkpoint_steps = int(
            progress.get("trained_steps", self.checkpoint_steps)
        )
        loss_value = metrics.get("loss")

        if loss_value is not None:
            loss_value = float(loss_value)
            wall_time = float(progress.get("wall_time", time.time()))

            if self.history_start_wall_time is None:
                self.history_start_wall_time = wall_time

            if self.loss_ema is None:
                self.loss_ema = loss_value
            else:
                self.loss_ema = 0.05 * loss_value + 0.95 * self.loss_ema

            history_item = {
                "step": self.checkpoint_steps,
                "wall_time": wall_time,
                "loss": loss_value,
                "loss_ema": self.loss_ema,
                "valid_samples": int(
                    progress.get("valid_samples", 0)
                ),
            }

            for key in (
                "latent_loss",
                "value_loss",
                "ranking_loss",
                "variance_loss",
                "latent_loss_h1",
                "latent_loss_h2",
                "latent_loss_h4",
                "ranking_accuracy",
                "cosine_gap",
                "latent_std_mean",
                "effective_rank",
                "gradient_norm",
            ):
                value = metrics.get(key)
                history_item[key] = None if value is None else float(value)

            self.train_history.append(history_item)

            if len(self.train_history) > self.max_history_storage:
                newest_item = self.train_history[-1]
                self.train_history = self.train_history[::2]

                if self.train_history[-1] is not newest_item:
                    self.train_history.append(newest_item)

            self.recent_metric_history.append(history_item)
            cutoff = wall_time - self.heatmap_window_seconds

            if (
                len(self.recent_metric_history) % 128 == 0
                or wall_time - self.heatmap_last_prune >= 10.0
            ):
                self.recent_metric_history = [
                    item
                    for item in self.recent_metric_history
                    if item["wall_time"] >= cutoff
                ]
                self.heatmap_last_prune = wall_time

            self.cap_nhat_heatmap_dai_han(wall_time)

        self.update()

    @Slot(object)
    def nhan_engine(self, progress):
        self.latest_engine = progress.copy()
        stage = progress.get("stage", "UNKNOWN")

        if stage == "MCTS":
            self.last_mcts_progress = progress.copy()

        if stage == "FINAL":
            self.last_engine_final = progress.copy()
            source = progress.get("source", "UNKNOWN")
            move = self.dinh_dang_move(progress.get("move"))
            self.them_log(f"ENGINE {source}: {move}")

        self.update()

    @Slot(object)
    def nhan_state(self, state):
        if state.get("event") == "PLAYER_COLOR":
            color_text = state.get("player_color", "--").upper()
            self.them_log("PLAYER COLOR: " + color_text)

        if state.get("event") == "IMPORT_RESULT":
            try:
                self.sample_count = (
                    self.board_widget.database.dem_model_samples()
                )
            except Exception:
                pass

            if "error" in state:
                self.them_log("IMPORT ERROR: " + state["error"])
            else:
                self.them_log(
                    f"IMPORT +{state.get('imported', 0)} GM GAMES"
                )

        self.update()

    def dinh_dang_move(self, move):
        if move is None:
            return "--"

        try:
            return move_thanh_text(tuple(move))
        except Exception:
            return str(move)

    def dinh_dang_so(self, value, digits=3):
        if value is None:
            return "--"

        if isinstance(value, bool):
            return "YES" if value else "NO"

        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)

        absolute = abs(number)

        if absolute >= 1_000_000:
            return f"{number / 1_000_000:.2f}M"
        if absolute >= 1_000:
            return f"{number / 1_000:.2f}K"
        if number.is_integer():
            return str(int(number))

        return f"{number:.{digits}f}"

    def dinh_dang_thoi_luong(self, seconds):
        if seconds is None:
            return "--"

        try:
            total_seconds = max(0, int(round(float(seconds))))
        except (TypeError, ValueError, OverflowError):
            return "--"

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds_value = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours:02d}:{minutes:02d}:{seconds_value:02d}"

        return f"{hours:02d}:{minutes:02d}:{seconds_value:02d}"

    def lay_lich_su_bieu_do(self):
        history = self.train_history

        if len(history) <= self.max_plot_points:
            return history

        first_time = history[0]["wall_time"]
        last_time = history[-1]["wall_time"]

        if last_time - first_time <= 1e-9:
            step = (len(history) - 1) / (self.max_plot_points - 1)
            indexes = {
                min(len(history) - 1, int(round(index * step)))
                for index in range(self.max_plot_points)
            }
            indexes.add(0)
            indexes.add(len(history) - 1)
            return [history[index] for index in sorted(indexes)]

        result = [history[0]]
        history_index = 1

        for point_index in range(1, self.max_plot_points - 1):
            target_time = (
                first_time
                + (last_time - first_time)
                * point_index
                / (self.max_plot_points - 1)
            )

            while (
                history_index + 1 < len(history)
                and abs(
                    history[history_index + 1]["wall_time"]
                    - target_time
                )
                <= abs(
                    history[history_index]["wall_time"]
                    - target_time
                )
            ):
                history_index += 1

            if history[history_index] is not result[-1]:
                result.append(history[history_index])

        if history[-1] is not result[-1]:
            result.append(history[-1])

        return result

    def cap_nhat_heatmap_dai_han(self, wall_time):
        history = self.recent_metric_history

        if len(history) == 0:
            self.latest_heatmap = None
            self.heatmap_info = {"status": "WAITING FOR TRAIN DATA"}
            return

        duration = history[-1]["wall_time"] - history[0]["wall_time"]

        if (
            len(history) < self.heatmap_min_points
            or duration < self.heatmap_min_seconds
            or np is None
        ):
            self.latest_heatmap = None
            self.heatmap_info = {
                "status": "COLLECTING LONG-WINDOW DATA",
                "points": len(history),
                "duration": duration,
                "required_points": self.heatmap_min_points,
                "required_duration": self.heatmap_min_seconds,
            }
            return

        if wall_time - self.heatmap_last_compute < 10.0:
            return

        self.heatmap_last_compute = wall_time
        metric_keys = [item[0] for item in self.heatmap_metric_specs]
        numeric_rows = []
        valid_samples = 0

        for item in history:
            values = [item.get(key) for key in metric_keys]

            if all(
                value is not None and math.isfinite(float(value))
                for value in values
            ):
                numeric_rows.append([float(value) for value in values])
                valid_samples += int(item.get("valid_samples", 0))

        if len(numeric_rows) < self.heatmap_min_points:
            self.latest_heatmap = None
            self.heatmap_info["status"] = "NOT ENOUGH FINITE DATA"
            self.heatmap_info["points"] = len(numeric_rows)
            return

        matrix = np.asarray(numeric_rows, dtype=np.float64)
        centered = matrix - np.mean(matrix, axis=0, keepdims=True)
        standard_deviation = np.std(centered, axis=0, ddof=1)
        active = standard_deviation > 1e-12
        normalized = np.zeros_like(centered)
        normalized[:, active] = (
            centered[:, active] / standard_deviation[active]
        )
        correlation = (
            normalized.T @ normalized / max(1, len(matrix) - 1)
        )
        correlation = np.clip(correlation, -1.0, 1.0)
        np.fill_diagonal(correlation, 1.0)

        off_diagonal = []
        maximum_pair = (0.0, "--")

        for row_index in range(len(metric_keys)):
            for column_index in range(row_index + 1, len(metric_keys)):
                value = float(correlation[row_index, column_index])
                off_diagonal.append(abs(value))

                if abs(value) > maximum_pair[0]:
                    maximum_pair = (
                        abs(value),
                        f"{self.heatmap_metric_specs[row_index][1]} / "
                        f"{self.heatmap_metric_specs[column_index][1]}",
                    )

        self.latest_heatmap = correlation.tolist()
        self.heatmap_info = {
            "status": "READY",
            "points": len(matrix),
            "duration": duration,
            "valid_samples": valid_samples,
            "start_time": history[0]["wall_time"],
            "end_time": history[-1]["wall_time"],
            "mean_abs": (
                sum(off_diagonal) / len(off_diagonal)
                if off_diagonal
                else 0.0
            ),
            "maximum_abs": maximum_pair[0],
            "maximum_pair": maximum_pair[1],
            "constant_metrics": [
                self.heatmap_metric_specs[index][1]
                for index, is_active in enumerate(active)
                if not is_active
            ],
        }

    def ve_panel(self, painter, rect, title):
        painter.fillRect(rect, self.panel_background)
        pen = QPen(self.neon_green_dim)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)

        title_rect = QRectF(
            rect.x() + 10,
            rect.y() + 4,
            rect.width() - 20,
            24,
        )
        painter.setPen(self.neon_green)
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, title)

        line_y = int(rect.y() + 28)
        painter.setPen(QPen(self.neon_green_dim, 1))
        painter.drawLine(
            int(rect.x() + 8),
            line_y,
            int(rect.right() - 8),
            line_y,
        )

    def ve_bieu_do(self, painter, rect, title, series_data):
        self.ve_panel(painter, rect, title)
        chart = rect.adjusted(48, 42, -14, -50)

        if chart.width() < 40 or chart.height() < 40:
            return

        history = self.lay_lich_su_bieu_do()
        all_values = []

        for _, key, _ in series_data:
            for item in history:
                value = item.get(key)

                if value is not None and math.isfinite(value):
                    all_values.append(float(value))

        painter.setFont(QFont("Consolas", 8))

        if len(all_values) == 0:
            painter.setPen(self.text_muted)
            painter.drawText(chart, Qt.AlignCenter, "WAITING FOR TRAIN DATA")
            return

        minimum = min(0.0, min(all_values))
        maximum = max(all_values)

        if maximum - minimum < 1e-9:
            maximum = minimum + 1.0

        for grid_index in range(5):
            ratio = grid_index / 4
            y = int(chart.bottom() - ratio * chart.height())
            painter.setPen(QPen(QColor("#0B321A"), 1))
            painter.drawLine(int(chart.left()), y, int(chart.right()), y)
            grid_value = minimum + ratio * (maximum - minimum)
            label_rect = QRectF(
                rect.x() + 4,
                y - 8,
                38,
                16,
            )
            painter.setPen(self.text_muted)
            painter.drawText(
                label_rect,
                Qt.AlignRight | Qt.AlignVCenter,
                self.dinh_dang_so(grid_value, 2),
            )

        first_time = float(history[0].get("wall_time", 0.0))
        last_time = float(history[-1].get("wall_time", first_time))
        time_span = max(1e-9, last_time - first_time)

        for label, key, color in series_data:
            painter.setPen(QPen(color, 2))
            previous_point = None
            first_point = None
            last_point = None

            for item in history:
                value = item.get(key)

                if value is None or math.isfinite(value) == False:
                    previous_point = None
                    continue

                item_time = float(item.get("wall_time", first_time))
                time_ratio = (item_time - first_time) / time_span
                time_ratio = max(0.0, min(1.0, time_ratio))
                x = int(chart.left() + time_ratio * chart.width())
                normalized = (float(value) - minimum) / (maximum - minimum)
                y = int(chart.bottom() - normalized * chart.height())

                if previous_point is not None:
                    painter.drawLine(
                        previous_point[0],
                        previous_point[1],
                        x,
                        y,
                    )

                previous_point = (x, y)

                if first_point is None:
                    first_point = (x, y)

                last_point = (x, y)

            painter.setPen(QPen(color, 1))
            painter.setBrush(color)

            if first_point is not None:
                painter.drawEllipse(
                    QRectF(first_point[0] - 3, first_point[1] - 3, 6, 6)
                )

            if last_point is not None:
                painter.drawEllipse(
                    QRectF(last_point[0] - 4, last_point[1] - 4, 8, 8)
                )

            painter.setBrush(Qt.NoBrush)

        painter.setPen(QPen(self.neon_green_dim, 1))
        painter.drawLine(
            int(chart.left()),
            int(chart.top()),
            int(chart.left()),
            int(chart.bottom()),
        )
        painter.drawLine(
            int(chart.right()),
            int(chart.top()),
            int(chart.right()),
            int(chart.bottom()),
        )

        start_text = datetime.fromtimestamp(first_time).strftime("%H:%M:%S")
        now_text = datetime.fromtimestamp(last_time).strftime("%H:%M:%S")
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.setPen(self.neon_cyan)
        painter.drawText(
            QRectF(chart.left(), chart.bottom() + 4, chart.width() * 0.34, 16),
            Qt.AlignLeft | Qt.AlignVCenter,
            "START " + start_text,
        )
        painter.setPen(self.neon_orange)
        painter.drawText(
            QRectF(
                chart.left() + chart.width() * 0.66,
                chart.bottom() + 4,
                chart.width() * 0.34,
                16,
            ),
            Qt.AlignRight | Qt.AlignVCenter,
            "NOW " + now_text,
        )
        painter.setPen(self.text_muted)
        painter.setFont(QFont("Consolas", 7))
        painter.drawText(
            QRectF(
                chart.left() + chart.width() * 0.34,
                chart.bottom() + 4,
                chart.width() * 0.32,
                16,
            ),
            Qt.AlignCenter,
            "SPAN " + self.dinh_dang_thoi_luong(time_span),
        )

        legend_x = int(chart.left())
        legend_y = int(rect.bottom() - 17)

        for label, _, color in series_data:
            painter.setPen(QPen(color, 3))
            painter.drawLine(legend_x, legend_y, legend_x + 16, legend_y)
            painter.setPen(self.text_primary)
            painter.drawText(
                QRectF(legend_x + 21, legend_y - 9, 92, 18),
                Qt.AlignLeft | Qt.AlignVCenter,
                label,
            )
            legend_x += 112

    def mau_tuong_quan(self, value):
        value = max(-1.0, min(1.0, float(value)))

        if value >= 0:
            return QColor(
                5 + int(245 * value),
                10 + int(20 * value),
                16 + int(205 * value),
            )

        magnitude = abs(value)
        return QColor(
            4,
            14 + int(210 * magnitude),
            18 + int(237 * magnitude),
        )

    def ve_heatmap(self, painter, rect):
        self.ve_panel(
            painter,
            rect,
            "TRAIN METRIC CORRELATION // ROLLING 30 MIN // PEARSON r",
        )
        matrix = self.latest_heatmap
        info = self.heatmap_info

        if matrix is None:
            painter.setPen(self.text_muted)
            painter.setFont(QFont("Consolas", 9))
            status = info.get("status", "WAITING FOR TRAIN DATA")
            points = int(info.get("points", 0))
            required_points = int(
                info.get("required_points", self.heatmap_min_points)
            )
            duration = self.dinh_dang_thoi_luong(
                info.get("duration", 0)
            )
            required_duration = self.dinh_dang_thoi_luong(
                info.get("required_duration", self.heatmap_min_seconds)
            )
            painter.drawText(
                rect.adjusted(10, 34, -10, -10),
                Qt.AlignCenter | Qt.TextWordWrap,
                f"{status}\n\n"
                f"BATCHES {points}/{required_points}\n"
                f"TIME SPAN {duration}/{required_duration}\n\n"
                "THE MATRIX STARTS AFTER >= 5 MINUTES AND >= 128 "
                "BATCHES SO SHORT-TERM NOISE DOES NOT DOMINATE.\n"
                "CYAN = NEGATIVE | BLACK = 0 | MAGENTA = POSITIVE",
            )
            return

        matrix_size = min(len(self.heatmap_metric_specs), len(matrix))
        available = rect.adjusted(38, 40, -12, -135)
        map_size = min(available.width(), available.height())
        cell_size = max(2.0, map_size / matrix_size)
        map_width = cell_size * matrix_size
        map_x = available.x() + (available.width() - map_width) / 2
        map_y = available.y()
        painter.setPen(Qt.NoPen)

        for row in range(matrix_size):
            for col in range(matrix_size):
                try:
                    value = matrix[row][col]
                except (IndexError, TypeError):
                    value = 0.0

                painter.fillRect(
                    QRectF(
                        map_x + col * cell_size,
                        map_y + row * cell_size,
                        cell_size + 0.5,
                        cell_size + 0.5,
                    ),
                    self.mau_tuong_quan(value),
                )

                if cell_size >= 18:
                    painter.setFont(QFont("Consolas", 6))
                    painter.setPen(
                        QColor("#000000")
                        if abs(float(value)) >= 0.45
                        else self.text_primary
                    )
                    painter.drawText(
                        QRectF(
                            map_x + col * cell_size,
                            map_y + row * cell_size,
                            cell_size,
                            cell_size,
                        ),
                        Qt.AlignCenter,
                        f"{float(value):.2f}",
                    )
                    painter.setPen(Qt.NoPen)

        painter.setPen(QPen(self.neon_green_dim, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(map_x, map_y, map_width, map_width))
        painter.setFont(QFont("Consolas", 8))
        painter.setPen(self.text_muted)

        for tick in range(matrix_size):
            painter.drawText(
                QRectF(
                    map_x + tick * cell_size - 8,
                    map_y + map_width + 3,
                    24,
                    16,
                ),
                Qt.AlignCenter,
                str(tick + 1),
            )
            painter.drawText(
                QRectF(
                    map_x - 30,
                    map_y + tick * cell_size - 5,
                    24,
                    16,
                ),
                Qt.AlignRight | Qt.AlignVCenter,
                str(tick + 1),
            )

        legend_y = map_y + map_width + 8
        legend_column_width = rect.width() / 2 - 12
        painter.setFont(QFont("Consolas", 7))

        for index, (_, short_name, full_name) in enumerate(
            self.heatmap_metric_specs
        ):
            column = 0 if index < 5 else 1
            row = index if index < 5 else index - 5
            x = rect.x() + 10 + column * legend_column_width
            y = legend_y + row * 13
            painter.setPen(self.neon_cyan if column == 0 else self.neon_orange)
            painter.drawText(
                QRectF(x, y, 64, 13),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"{index + 1:>2} {short_name}",
            )
            painter.setPen(self.text_muted)
            painter.drawText(
                QRectF(x + 66, y, legend_column_width - 66, 13),
                Qt.AlignLeft | Qt.AlignVCenter,
                "= " + full_name,
            )

        start_text = datetime.fromtimestamp(
            info.get("start_time", time.time())
        ).strftime("%H:%M:%S")
        end_text = datetime.fromtimestamp(
            info.get("end_time", time.time())
        ).strftime("%H:%M:%S")
        info_line_1 = (
            f"WINDOW {start_text}->{end_text}  "
            f"SPAN {self.dinh_dang_thoi_luong(info.get('duration'))}  "
            f"BATCHES {info.get('points', 0)}  "
            f"VALID SAMPLES {info.get('valid_samples', 0)}"
        )
        info_line_2 = (
            f"MEAN |r| {self.dinh_dang_so(info.get('mean_abs'))}  "
            f"MAX |r| {self.dinh_dang_so(info.get('maximum_abs'))} "
            f"({info.get('maximum_pair', '--')})  "
            "CORRELATION != CAUSATION"
        )
        constant_metrics = info.get("constant_metrics") or []

        if constant_metrics:
            info_line_2 += "  CONST: " + ",".join(constant_metrics)

        painter.setFont(QFont("Consolas", 7))
        painter.setPen(self.text_primary)
        painter.drawText(
            QRectF(rect.x() + 8, rect.bottom() - 47, rect.width() - 16, 14),
            Qt.AlignLeft | Qt.AlignVCenter,
            info_line_1,
        )
        painter.setPen(self.text_muted)
        painter.drawText(
            QRectF(rect.x() + 8, rect.bottom() - 32, rect.width() - 16, 14),
            Qt.AlignLeft | Qt.AlignVCenter,
            info_line_2,
        )
        painter.setPen(self.text_primary)
        painter.drawText(
            QRectF(rect.x() + 8, rect.bottom() - 17, rect.width() - 16, 13),
            Qt.AlignCenter,
            "-1 CYAN      0 BLACK      +1 MAGENTA",
        )

    def ve_danh_sach_chi_so(self, painter, rect):
        self.ve_panel(painter, rect, "TRAIN TELEMETRY")
        progress = self.latest_train
        metrics = self.latest_metrics
        epoch_text = "--"

        if progress:
            epoch_text = (
                f"{progress.get('epoch', '--')}/"
                f"{progress.get('epochs', '--')}"
            )

        processed_text = "--"
        overall_text = "--"

        if progress:
            processed_text = (
                f"{progress.get('processed', '--')}/"
                f"{progress.get('total', '--')}"
            )
            overall_processed = progress.get("overall_processed")
            overall_total = progress.get("overall_total")
            progress_percent = progress.get("progress_percent")

            if progress_percent is None and overall_total:
                progress_percent = (
                    100.0 * float(overall_processed) / float(overall_total)
                )

            overall_text = (
                f"{self.dinh_dang_so(progress_percent, 1)}%  "
                f"({self.dinh_dang_so(overall_processed)}/"
                f"{self.dinh_dang_so(overall_total)})"
            )

        rows = (
            ("CHECKPOINT STEP", self.checkpoint_steps),
            ("EPOCH", epoch_text),
            ("OVERALL PROGRESS", overall_text),
            ("CURRENT EPOCH ROWS", processed_text),
            ("VALID / SKIPPED", (
                f"{progress.get('valid_samples', '--')} / "
                f"{progress.get('skipped_samples', '--')}"
            )),
            ("ROWS / SECOND (EMA)", progress.get("rows_per_second")),
            ("RAW / EMA LOSS", (
                f"{self.dinh_dang_so(metrics.get('loss'))} / "
                f"{self.dinh_dang_so(self.loss_ema)}"
            )),
            ("LATENT H1 / H2 / H4", (
                f"{self.dinh_dang_so(metrics.get('latent_loss_h1'))} / "
                f"{self.dinh_dang_so(metrics.get('latent_loss_h2'))} / "
                f"{self.dinh_dang_so(metrics.get('latent_loss_h4'))}"
            )),
            ("RANK ACCURACY", (
                None
                if metrics.get("ranking_accuracy") is None
                else f"{100 * metrics['ranking_accuracy']:.1f}%"
            )),
            ("COSINE GAP", metrics.get("cosine_gap")),
            ("LATENT STD MEAN", metrics.get("latent_std_mean")),
            ("EFFECTIVE RANK", metrics.get("effective_rank")),
            ("GRADIENT NORM", metrics.get("gradient_norm")),
        )

        content = rect.adjusted(12, 36, -12, -8)
        row_height = max(14.0, content.height() / len(rows))
        font_size = max(7, min(10, int(row_height * 0.56)))
        painter.setFont(QFont("Consolas", font_size))

        for index, (label, value) in enumerate(rows):
            y = content.y() + index * row_height
            label_rect = QRectF(
                content.x(),
                y,
                content.width() * 0.58,
                row_height,
            )
            value_rect = QRectF(
                content.x() + content.width() * 0.58,
                y,
                content.width() * 0.42,
                row_height,
            )
            painter.setPen(self.text_muted)
            painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignVCenter, label)
            painter.setPen(self.text_primary)

            if isinstance(value, str):
                value_text = value
            else:
                value_text = self.dinh_dang_so(value)

            painter.drawText(
                value_rect,
                Qt.AlignRight | Qt.AlignVCenter,
                value_text,
            )

    def ve_engine(self, painter, rect):
        self.ve_panel(painter, rect, "ENGINE SEARCH // LIVE")
        engine = self.latest_engine
        final = self.last_engine_final
        mcts = self.last_mcts_progress
        stage = engine.get("stage", "IDLE")

        if stage == "MCTS":
            moves = engine.get("moves", [])
        elif final.get("mcts_moves"):
            moves = final.get("mcts_moves", [])
        else:
            moves = mcts.get("moves", [])

        stats = (
            ("STAGE", stage),
            ("SOURCE", engine.get("source", final.get("source", "--"))),
            ("MOVE", self.dinh_dang_move(engine.get("move"))),
            ("SCORE WHITE", engine.get("score_white")),
            ("DEPTH", engine.get("depth")),
            ("NODES", engine.get("nodes")),
            ("NPS", engine.get("nps")),
            ("SEARCH TIME / LIMIT", (
                f"{self.dinh_dang_so(engine.get('time'))} / "
                f"{self.dinh_dang_so(engine.get('time_limit'))} s"
            )),
            ("MCTS SIMULATIONS", (
                engine.get("simulations")
                if stage == "MCTS"
                else final.get("mcts_simulations", mcts.get("simulations"))
            )),
            ("MCTS SIM / SECOND", mcts.get("simulations_per_second")),
        )

        content = rect.adjusted(12, 36, -12, -10)
        stats_height = min(content.height() * 0.53, len(stats) * 20)
        row_height = stats_height / len(stats)
        painter.setFont(QFont("Consolas", max(7, int(row_height * 0.52))))

        for index, (label, value) in enumerate(stats):
            y = content.y() + index * row_height
            painter.setPen(self.text_muted)
            painter.drawText(
                QRectF(content.x(), y, content.width() * 0.55, row_height),
                Qt.AlignLeft | Qt.AlignVCenter,
                label,
            )
            painter.setPen(self.text_primary)
            value_text = value if isinstance(value, str) else self.dinh_dang_so(value)
            painter.drawText(
                QRectF(
                    content.x() + content.width() * 0.55,
                    y,
                    content.width() * 0.45,
                    row_height,
                ),
                Qt.AlignRight | Qt.AlignVCenter,
                value_text,
            )

        moves_top = content.y() + stats_height + 8
        painter.setPen(self.neon_green)
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(
            QRectF(content.x(), moves_top, content.width(), 18),
            Qt.AlignLeft | Qt.AlignVCenter,
            "ROOT MOVE     VISITS    SHARE     VALUE     PRIOR",
        )

        painter.setFont(QFont("Consolas", 8))
        move_row_height = 18

        for index, item in enumerate(moves[:6]):
            y = moves_top + 20 + index * move_row_height

            if y + move_row_height > content.bottom():
                break

            move_text = self.dinh_dang_move(item.get("move"))
            line = (
                f"{move_text:<12} "
                f"{int(item.get('visits', 0)):>6}   "
                f"{item.get('visit_share', 0.0):>6.3f}   "
                f"{item.get('value', 0.0):>6.3f}   "
                f"{item.get('prior', 0.0):>6.3f}"
            )
            painter.setPen(
                self.neon_cyan if index == 0 else self.text_primary
            )
            painter.drawText(
                QRectF(content.x(), y, content.width(), move_row_height),
                Qt.AlignLeft | Qt.AlignVCenter,
                line,
            )

    def ve_header(self, painter):
        header = QRectF(14, 10, self.width() - 28, 66)
        painter.fillRect(header, QColor("#020604"))
        painter.setPen(QPen(self.neon_green, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(header)
        painter.setFont(QFont("Consolas", 15, QFont.Bold))
        painter.setPen(self.neon_green)
        painter.drawText(
            QRectF(
                header.x() + 14,
                header.y(),
                header.width() * 0.46,
                header.height(),
            ),
            Qt.AlignLeft | Qt.AlignVCenter,
            "CAISSA-JEPA // TRAINING & ENGINE DEBUG MONITOR",
        )

        eta_rect = QRectF(
            header.x() + header.width() * 0.47,
            header.y() + 7,
            header.width() * 0.24,
            header.height() - 14,
        )
        painter.fillRect(eta_rect, QColor("#050B08"))
        eta_color = self.neon_orange if self.training_active else self.neon_green_dim
        painter.setPen(QPen(eta_color, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(eta_rect)

        eta_text = self.dinh_dang_thoi_luong(self.eta_seconds)
        finish_text = "--"

        if self.estimated_finish_timestamp is not None:
            try:
                finish_text = datetime.fromtimestamp(
                    float(self.estimated_finish_timestamp)
                ).strftime("%Y-%m-%d %H:%M")
            except (TypeError, ValueError, OverflowError, OSError):
                finish_text = "--"

        progress_percent = self.latest_train.get("progress_percent")
        progress_text = (
            "--"
            if progress_percent is None
            else f"{float(progress_percent):.1f}%"
        )
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.setPen(eta_color)
        painter.drawText(
            QRectF(eta_rect.x() + 8, eta_rect.y() + 2, eta_rect.width() - 16, 16),
            Qt.AlignLeft | Qt.AlignVCenter,
            "TRAIN ETA  " + eta_text,
        )
        painter.setFont(QFont("Consolas", 7))
        painter.setPen(self.text_primary)
        painter.drawText(
            QRectF(eta_rect.x() + 8, eta_rect.y() + 18, eta_rect.width() - 16, 14),
            Qt.AlignLeft | Qt.AlignVCenter,
            "FINISH  " + finish_text,
        )
        painter.setPen(self.text_muted)
        painter.drawText(
            QRectF(eta_rect.x() + 8, eta_rect.y() + 33, eta_rect.width() - 16, 14),
            Qt.AlignLeft | Qt.AlignVCenter,
            "PROGRESS  " + progress_text,
        )

        model_path = self.board_widget.model_path
        if self.board_widget.adversarial_model_path.exists():
            model_path = self.board_widget.adversarial_model_path
        model_size = 0

        try:
            if model_path.exists():
                model_size = model_path.stat().st_size
        except OSError:
            model_size = 0

        status = (
            f"MODEL v{self.checkpoint_version or '--'}  |  "
            f"STEP {self.checkpoint_steps}\n"
            f"SAMPLES {self.sample_count}  |  "
            f"CHECKPOINT {model_size / 1024:.1f} KiB"
        )
        painter.setFont(QFont("Consolas", 9))
        painter.setPen(self.text_primary)
        painter.drawText(
            QRectF(
                header.x() + header.width() * 0.72,
                header.y(),
                header.width() * 0.28 - 14,
                header.height(),
            ),
            Qt.AlignRight | Qt.AlignVCenter,
            status,
        )

    def ve_log_footer(self, painter, rect):
        self.ve_panel(painter, rect, "EVENT LOG // F11 TOGGLE FULLSCREEN // ESC WINDOWED")
        content = rect.adjusted(10, 34, -10, -8)
        painter.setFont(QFont("Consolas", 8))
        row_height = 13
        visible_count = max(1, int(content.height() // row_height))
        visible_lines = self.log_lines[-visible_count:]

        for index, line in enumerate(visible_lines):
            y = content.y() + index * row_height
            painter.setPen(
                self.text_primary
                if index == len(visible_lines) - 1
                else self.text_muted
            )
            painter.drawText(
                QRectF(content.x(), y, content.width(), row_height),
                Qt.AlignLeft | Qt.AlignVCenter,
                line,
            )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#000000"))
        self.ve_header(painter)

        margin = 14
        gap = 10
        content_top = 86
        content_bottom = self.height() - margin
        content_height = max(100, content_bottom - content_top)
        top_height = int(content_height * 0.39)
        bottom_height = content_height - top_height - gap
        available_width = self.width() - margin * 2
        first_width = int((available_width - gap) * 0.50)

        loss_rect = QRectF(
            margin,
            content_top,
            first_width,
            top_height,
        )
        component_rect = QRectF(
            margin + first_width + gap,
            content_top,
            available_width - first_width - gap,
            top_height,
        )

        self.ve_bieu_do(
            painter,
            loss_rect,
            "LOSS TREND // FULL RUN COMPRESSED // RAW VS EMA(0.05)",
            (
                ("RAW", "loss", self.neon_magenta),
                ("EMA", "loss_ema", self.neon_green),
            ),
        )
        self.ve_bieu_do(
            painter,
            component_rect,
            "LOSS COMPONENTS // FULL RUN COMPRESSED",
            (
                ("LATENT", "latent_loss", self.neon_cyan),
                ("VALUE", "value_loss", self.neon_orange),
                ("RANK", "ranking_loss", self.neon_magenta),
                ("VAR", "variance_loss", self.neon_green),
            ),
        )

        bottom_y = content_top + top_height + gap
        heatmap_width = int(available_width * 0.34)
        telemetry_width = int(available_width * 0.28)
        engine_width = available_width - heatmap_width - telemetry_width - gap * 2
        log_height = max(92, int(bottom_height * 0.24))
        upper_bottom_height = bottom_height - log_height - gap

        heatmap_rect = QRectF(
            margin,
            bottom_y,
            heatmap_width,
            upper_bottom_height,
        )
        telemetry_rect = QRectF(
            margin + heatmap_width + gap,
            bottom_y,
            telemetry_width,
            upper_bottom_height,
        )
        engine_rect = QRectF(
            margin + heatmap_width + telemetry_width + gap * 2,
            bottom_y,
            engine_width,
            upper_bottom_height,
        )
        log_rect = QRectF(
            margin,
            bottom_y + upper_bottom_height + gap,
            available_width,
            log_height,
        )

        self.ve_heatmap(painter, heatmap_rect)
        self.ve_danh_sach_chi_so(painter, telemetry_rect)
        self.ve_engine(painter, engine_rect)
        self.ve_log_footer(painter, log_rect)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            window = self.window()

            if window.isFullScreen():
                window.showNormal()
            else:
                window.showFullScreen()

            return

        if event.key() == Qt.Key_Escape:
            if self.window().isFullScreen():
                self.window().showNormal()
                return

        super().keyPressEvent(event)


class monitor_window(QMainWindow):
    def __init__(self, board_widget):
        super().__init__()
        self.setWindowTitle(APP_BUILD + " Debug Monitor")
        self.resize(1500, 900)
        self.monitor_widget = monitorwidget(board_widget)
        self.setCentralWidget(self.monitor_widget)


class main_window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("chess - trắng | " + APP_BUILD)
        self.resize(900, 750)
        self.monitor_window = None

        self.board_widget = boardwidget()
        self.setCentralWidget(self.board_widget)

    def gan_monitor_window(self, window):
        self.monitor_window = window

    def closeEvent(self, event):
        if self.board_widget.close() == False:
            event.ignore()
            return

        if self.monitor_window is not None:
            self.monitor_window.close()

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = main_window()
    monitor = monitor_window(window.board_widget)
    window.gan_monitor_window(monitor)
    window.show()

    screens = app.screens()

    if len(screens) > 1:
        monitor.setGeometry(screens[1].geometry())

    monitor.showFullScreen()
    monitor.raise_()
    monitor.activateWindow()
    sys.exit(app.exec())
