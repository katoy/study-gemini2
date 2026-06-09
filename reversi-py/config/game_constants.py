# config/game_constants.py
"""ゲーム定数を定義するモジュール。"""

from enum import IntEnum


class Player(IntEnum):
    """プレイヤーの定義。"""

    BLACK = -1
    WHITE = 1


class CellState(IntEnum):
    """盤面のセルの状態。"""

    EMPTY = 0
    BLACK = -1
    WHITE = 1


class GameConstants:
    """ゲーム全般の定数。"""

    DEFAULT_BOARD_SIZE = 8
    INITIAL_TURN = Player.BLACK
