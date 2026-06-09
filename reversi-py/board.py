# board.py
from typing import List, Tuple

from config.game_constants import CellState, Player


class Board:
    """オセロ（リバーシ）の盤面を管理するクラス。

    盤の初期化、石の配置、有効手の判定、石の反転などを行う。
    """

    def __init__(self, board_size: int = 8) -> None:
        """Board を初期化します。

        Args:
            board_size: 盤面のサイズ（デフォルトは 8×8）。

        Raises:
            ValueError: board_size が 4 未満の場合。
        """
        self.board_size = board_size
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        # 初期配置（中央 2×2 に白2個、黒2個）
        self.board[self.board_size // 2 - 1][self.board_size // 2 - 1] = self.board[self.board_size // 2][self.board_size // 2] = 1  # 白
        self.board[self.board_size // 2 - 1][self.board_size // 2] = self.board[self.board_size // 2][self.board_size // 2 - 1] = -1  # 黒

    def _get_flipped_in_direction(self, row: int, col: int, dr: int, dc: int, turn: int) -> List[Tuple[int, int]]:
        """指定方向でひっくり返す石を取得します。

        Args:
            row: 開始行番号。
            col: 開始列番号。
            dr: 行方向（-1, 0, 1）。
            dc: 列方向（-1, 0, 1）。
            turn: プレイヤー（-1: 黒、1: 白）。

        Returns:
            ひっくり返す (row, col) のタプルのリスト。
        """
        to_flip: list[tuple[int, int]] = []
        r, c = row + dr, col + dc
        while 0 <= r < self.board_size and 0 <= c < self.board_size:
            if self.board[r][c] == 0:
                break
            if self.board[r][c] == turn:
                return to_flip
            to_flip.append((r, c))
            r += dr
            c += dc
        return []

    def is_valid_move(self, row: int, col: int, turn: int) -> bool:
        """指定位置への石の配置が合法手かを判定します。

        Args:
            row: 行番号（0-indexed）。
            col: 列番号（0-indexed）。
            turn: プレイヤー（-1: 黒、1: 白）。

        Returns:
            True であれば合法手、False であれば不合法手。
        """
        if not (0 <= row < self.board_size and 0 <= col < self.board_size) or self.board[row][col] != 0:
            return False

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                if self._get_flipped_in_direction(row, col, dr, dc, turn):
                    return True
        return False

    def get_valid_moves(self, turn: int) -> List[Tuple[int, int]]:
        """指定されたプレイヤーの合法手をすべて取得します。

        Args:
            turn: プレイヤー（-1: 黒、1: 白）。

        Returns:
            (row, col) のタプルのリスト。
        """
        valid_moves = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.is_valid_move(row, col, turn):
                    valid_moves.append((row, col))
        return valid_moves

    def place_stone(self, row: int, col: int, turn: int) -> bool:
        """指定位置に石を配置し、反転処理を行います。

        Args:
            row: 行番号（0-indexed）。
            col: 列番号（0-indexed）。
            turn: プレイヤー（-1: 黒、1: 白）。

        Returns:
            True であれば配置成功、False であれば配置失敗（不合法手）。
        """
        if not self.is_valid_move(row, col, turn):
            return False

        self.board[row][col] = turn
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                to_flip = self._get_flipped_in_direction(row, col, dr, dc, turn)
                for fr, fc in to_flip:
                    self.board[fr][fc] = turn
        return True

    def count_stones(self) -> Tuple[int, int]:
        """盤面の黒石と白石の数を数えます。

        Returns:
            (黒石数, 白石数) のタプル。
        """
        black_count = sum(row.count(-1) for row in self.board)
        white_count = sum(row.count(1) for row in self.board)
        return black_count, white_count

    def get_board(self) -> List[List[int]]:
        """現在の盤面を取得します。

        Returns:
            2次元リスト。0: 空、-1: 黒、1: 白。
        """
        return self.board

    def get_flipped_stones(self, row: int, col: int, turn: int) -> List[Tuple[int, int]]:
        """指定位置に石を配置した場合に反転する石のリストを取得します。

        Args:
            row: 行番号（0-indexed）。
            col: 列番号（0-indexed）。
            turn: プレイヤー（-1: 黒、1: 白）。

        Returns:
            反転する (row, col) のタプルのリスト。
        """
        flipped_stones = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                to_flip: list[tuple[int, int]] = []
                while 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if self.board[r][c] == 0:
                        break
                    if self.board[r][c] == turn:
                        flipped_stones.extend(to_flip)
                        break
                    to_flip.append((r, c))
                    r += dr
                    c += dc
        return flipped_stones