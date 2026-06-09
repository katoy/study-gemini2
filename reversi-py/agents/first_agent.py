# agents/first_agent.py
from typing import Optional, Tuple, TYPE_CHECKING

from .base_agent import Agent

if TYPE_CHECKING:
    from game import Game


class FirstAgent(Agent):
    """最初に見つかった合法手を選択する単純な AI エージェント。"""

    def play(self, game: 'Game') -> Optional[Tuple[int, int]]:
        """合法手の中から最初に見つかった手を返します。

        Args:
            game: 現在のゲーム状態。

        Returns:
            (row, col) のタプル、または合法手がない場合は None。
        """
        valid_moves = game.get_valid_moves()
        if valid_moves:
            return valid_moves[0]
        return None
