# agents/base_agent.py
from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game


class Agent:
    """AI エージェントの基本インターフェース。"""

    def play(self, game: 'Game') -> Optional[Tuple[int, int]]:
        """現在のゲーム状態から最善の手を選択します。

        Args:
            game: ゲーム状態。

        Returns:
            (row, col) のタプル、または移動不可の場合は None。

        Raises:
            NotImplementedError: サブクラスで実装してください。
        """
        raise NotImplementedError
