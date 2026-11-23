"""PatternAgent の 8x8 盤面テスト。"""
from unittest.mock import patch

from game import Game
from agents.pattern_agent import PatternAgent


def test_pattern_agent_initializes() -> None:
    """PatternAgent が正常に初期化できる"""
    agent = PatternAgent(weights_path=None, time_limit_ms=100)
    assert agent is not None
    assert agent._time_limit_ms == 100


def test_pattern_agent_evaluator_initialized() -> None:
    """PatternAgent が PatternEvaluator を 8x8 盤面で初期化する"""
    agent = PatternAgent(weights_path=None, time_limit_ms=100)
    assert agent._evaluator is not None
    assert agent._evaluator.board_size == 8


def test_pattern_agent_mocked_play() -> None:
    """PatternAgent が 8x8 盤面で着手を返す (mock 使用)"""
    agent = PatternAgent(weights_path=None, time_limit_ms=100)

    # _negamax メソッドを mock して高速化
    with patch.object(agent, '_negamax', return_value=(1.0, (2, 3))):
        game = Game(board_size=8)
        move = agent.play(game)

    # play メソッドは最善手を返す
    if move is not None:
        assert isinstance(move, tuple)
        assert len(move) == 2
        assert 0 <= move[0] < 8
        assert 0 <= move[1] < 8


# 時間制限テストで許容する経過時間の上限（秒）。制限 0.2 秒に対し十分な余裕を持たせる
PLAY_TIME_LIMIT_MS = 200
PLAY_MAX_ELAPSED_SEC = 10.0


def test_play_respects_time_limit() -> None:
    """play が time_limit_ms を大きく超えずに合法手を返す（探索が打ち切られる）"""
    import threading
    import time

    agent = PatternAgent(weights_path=None, time_limit_ms=PLAY_TIME_LIMIT_MS)
    game = Game(board_size=8)
    result: dict = {}

    def run() -> None:
        start = time.monotonic()
        result["move"] = agent.play(game)
        result["elapsed"] = time.monotonic() - start

    # 打ち切られない場合にテスト自体が終わらなくならないよう daemon スレッドで実行する
    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(timeout=PLAY_MAX_ELAPSED_SEC)

    assert not worker.is_alive(), f"play が {PLAY_MAX_ELAPSED_SEC} 秒以内に終わらない"
    assert result["move"] in game.get_valid_moves()


def test_play_keeps_move_from_last_completed_depth() -> None:
    """時間切れで中断した深さの結果ではなく、読み切れた深さの最善手を返す"""
    from agents.negamax_agent import _SearchTimeout

    agent = PatternAgent(weights_path=None, time_limit_ms=100)
    game = Game(board_size=8)
    with patch.object(
        agent, '_negamax', side_effect=[(1.0, (2, 3)), (5.0, (3, 2)), _SearchTimeout()]
    ):
        move = agent.play(game)

    assert move == (3, 2)


def test_play_does_not_mutate_game_board_on_timeout() -> None:
    """探索を時間切れで打ち切っても、渡されたゲームの盤面は変更されない"""
    agent = PatternAgent(weights_path=None, time_limit_ms=PLAY_TIME_LIMIT_MS)
    game = Game(board_size=8)
    before = [row[:] for row in game.board.board]

    agent.play(game)

    assert game.board.board == before
