"""AI Agent の強さ検証テスト（Tier 1 / CI 組み込み高速版）。

Negamax、Transposition、Pattern エージェントが初期化でき、
基本的な着手を返すことを確認。

通常の pytest 実行からは除外される::

    uv run pytest  # ← strength テストは実行されない

明示的に実行する場合::

    uv run pytest -m strength tests/test_strength.py -v
"""
import pytest

from agents.gain_agent import GainAgent
from agents.negamax_agent import NegamaxAgent
from agents.transposition_negamax_agent import TranspositionNegamaxAgent
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


@pytest.mark.strength
class TestTranspositionAgent:
    """TranspositionNegamaxAgent の初期化と基本動作確認。

    TranspositionTable + PVS + Killer Move heuristics を備えた強化版 Negamax。
    強さテストではなく、正常に初期化でき、着手を返すことを確認。
    """

    def test_transposition_initializes(self) -> None:
        """TranspositionNegamaxAgent が正常に初期化される。"""
        agent = TranspositionNegamaxAgent(time_limit_ms=100)
        assert agent is not None, "TranspositionNegamaxAgent の初期化に失敗"

    def test_transposition_returns_move(self) -> None:
        """TranspositionNegamaxAgent が初期盤面で合法手を返す。"""
        agent = TranspositionNegamaxAgent(time_limit_ms=100)
        game = Game(board_size=6)
        move = agent.play(game)
        # 初期盤面では黒が合法手を持つ
        assert move is not None, "TranspositionNegamaxAgent が着手を返さない"
        assert isinstance(move, tuple) and len(move) == 2, f"不正な着手形式: {move}"
        assert 0 <= move[0] < 6 and 0 <= move[1] < 6, f"着手が盤面外: {move}"


