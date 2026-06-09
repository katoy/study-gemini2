# agents/random_agent.py
import random
from typing import Optional, Tuple, TYPE_CHECKING

from .base_agent import Agent

if TYPE_CHECKING:
    from game import Game


class RandomAgent(Agent):
    """ランダムに合法手を選択する AI エージェント。"""

    def play(self, game: 'Game') -> Optional[Tuple[int, int]]:
        """合法手からランダムに選択します。

        Args:
            game: 現在のゲーム状態。

        Returns:
            (row, col) のタプル、または合法手がない場合は None。
        """
        valid_moves = game.get_valid_moves()
        if valid_moves:
            return random.choice(valid_moves)
        return None
