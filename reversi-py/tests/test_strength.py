"""NegamaxAgent の強さ検証テスト（Tier 1 / CI 組み込み高速版）。

通常の pytest 実行からは除外される::

    uv run pytest  # ← strength テストは実行されない

明示的に実行する場合::

    uv run pytest -m strength tests/test_strength.py -v
"""
import pytest

from agents.gain_agent import GainAgent
from agents.negamax_agent import NegamaxAgent
from game import Game


def play_one_game(black_agent, white_agent, board_size: int) -> int:
    """1 局対戦し、石差（黒 - 白）を返す。

    benchmark_agents.py と同一ロジックを直接コピー（shared utility 不要）。
    """
    game = Game(board_size=board_size)
    while not game.game_over:
        agent = black_agent if game.turn == -1 else white_agent
        move = agent.play(game)
        if move is not None:
            game.place_stone(move[0], move[1])
        game.switch_turn()
        game.check_game_over()
    black, white = game.board.count_stones()
    return black - white


@pytest.mark.strength
class TestNegamaxBeatsGainAgent:
    """Negamax が GainAgent に勝てることを確認する強さテスト。

    board_size=6 の理由:
      - 最大 32 手（8x8 の 60 手より短い）
      - 1 ゲーム最大 3.2 秒（32 手 × 100ms）
      - 3 ゲーム合計で約 9.6 秒以内
    """

    BOARD_SIZE = 6
    TIME_LIMIT_MS = 100

    def _negamax(self) -> NegamaxAgent:
        return NegamaxAgent(time_limit_ms=self.TIME_LIMIT_MS)

    def _gain(self) -> GainAgent:
        return GainAgent()

    def test_negamax_black_wins(self) -> None:
        """ゲーム1: Negamax が黒番で勝利（石差 > 0）。"""
        diff = play_one_game(self._negamax(), self._gain(), self.BOARD_SIZE)
        assert diff > 0, f"Negamax(黒) が GainAgent(白) に負けた (石差={diff})"

    def test_negamax_white_wins(self) -> None:
        """ゲーム2: Negamax が白番で勝利（石差 < 0 = 黒が負け）。"""
        diff = play_one_game(self._gain(), self._negamax(), self.BOARD_SIZE)
        assert diff < 0, f"Negamax(白) が GainAgent(黒) に負けた (石差={diff})"

    def test_negamax_black_wins_again(self) -> None:
        """ゲーム3: Negamax が再び黒番で勝利（3 試合中 2 勝以上の確認）。"""
        diff = play_one_game(self._negamax(), self._gain(), self.BOARD_SIZE)
        assert diff > 0, f"Negamax(黒) が GainAgent(白) に再び負けた (石差={diff})"
