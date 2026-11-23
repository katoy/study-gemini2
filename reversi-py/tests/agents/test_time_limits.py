"""時間制限付きエージェントが実局面で制限を守るかの単体テスト。

探索を mock せずに実際に動かし、中盤〜終盤の局面で 1 手の思考時間が
制限内に収まること、探索後にゲームの盤面を書き換えていないことを確認する。
"""
from __future__ import annotations

import random
import threading
from typing import Callable, Optional

import pytest

from agents.alpha_zero_agent import AlphaZeroAgent
from agents.base_agent import Agent
from agents.mcts_agent import MonteCarloTreeSearchAgent
from agents.minimax_agent import MinimaxAgent
from agents.negamax_agent import NegamaxAgent
from agents.pattern_agent import PatternAgent
from agents.transposition_negamax_agent import TranspositionNegamaxAgent
from game import Game

# 各エージェントに与える思考時間の上限（ミリ秒）
TIME_LIMIT_MS = 200
# 1 手の許容時間（秒）。CI の負荷を考慮して制限より十分大きく取る
MAX_SECONDS_PER_MOVE = 1.0
# 局面生成に使う乱数シード
POSITION_SEEDS = (0, 1)
# 中盤〜終盤の局面を作るために進める手数
MIDGAME_PLIES = (20, 40, 50)
# AlphaZero の終盤読み切りが必ず使われるよう、読み切りの空き数を大きく取る
AZ_ENDGAME_EMPTIES = 20
# 読み切り対象の局面（空き 20 以下）を作るための手数
AZ_ENDGAME_PLIES = (44, 50)
# AlphaZero の MCTS 探索回数（読み切り局面では使われない）
AZ_N_SIMULATIONS = 50

PATTERN_WEIGHTS_PATH = "data/pattern_weights_8x8.json"
AZ_MODEL_PATH = "models/alpha_zero_minimax80_best.pth"


def _random_position(seed: int, plies: int) -> Game:
    """初期局面からランダムに plies 手進めた局面を返す。

    Args:
        seed: 着手選択に使う乱数シード。
        plies: 進める手数（パスも 1 手と数える）。

    Returns:
        生成した局面の Game。
    """
    rng = random.Random(seed)
    game = Game(board_size=8)
    for _ in range(plies):
        if game.game_over:
            break
        moves = game.get_valid_moves()
        if moves:
            move = rng.choice(moves)
            game.place_stone(move[0], move[1])
        game.switch_turn()
        game.check_game_over()
    return game


AGENT_CASES: list[tuple[str, Callable[[], Agent], tuple[int, ...]]] = [
    ("negamax", lambda: NegamaxAgent(time_limit_ms=TIME_LIMIT_MS), MIDGAME_PLIES),
    ("minimax", lambda: MinimaxAgent(time_limit_ms=TIME_LIMIT_MS), MIDGAME_PLIES),
    ("transposition", lambda: TranspositionNegamaxAgent(time_limit_ms=TIME_LIMIT_MS), MIDGAME_PLIES),
    (
        "pattern",
        lambda: PatternAgent(weights_path=PATTERN_WEIGHTS_PATH, time_limit_ms=TIME_LIMIT_MS),
        MIDGAME_PLIES,
    ),
    (
        "mcts",
        lambda: MonteCarloTreeSearchAgent(iterations=10**9, time_limit_ms=TIME_LIMIT_MS),
        MIDGAME_PLIES,
    ),
    (
        "alphazero_endgame",
        lambda: AlphaZeroAgent(
            n_simulations=AZ_N_SIMULATIONS,
            model_path=AZ_MODEL_PATH,
            endgame_empties=AZ_ENDGAME_EMPTIES,
            endgame_time_limit_ms=TIME_LIMIT_MS,
        ),
        AZ_ENDGAME_PLIES,
    ),
]


@pytest.mark.parametrize(
    ("name", "make_agent", "plies_list"),
    AGENT_CASES,
    ids=[case[0] for case in AGENT_CASES],
)
def test_play_respects_time_limit_on_real_positions(
    name: str, make_agent: Callable[[], Agent], plies_list: tuple[int, ...]
) -> None:
    """実局面で 1 手が許容時間内に返り、合法手を選び、盤面を書き換えない。"""
    agent = make_agent()
    checked = 0
    for seed in POSITION_SEEDS:
        for plies in plies_list:
            game = _random_position(seed, plies)
            valid_moves = game.get_valid_moves()
            if game.game_over or not valid_moves:
                continue
            board_before = [row[:] for row in game.board.board]

            # 制限を守らず返ってこない場合もテストが止まらないよう、別スレッドで実行して待つ
            result: dict[str, Optional[tuple[int, int]]] = {}
            thread = threading.Thread(
                target=lambda: result.update(move=agent.play(game)), daemon=True
            )
            thread.start()
            thread.join(timeout=MAX_SECONDS_PER_MOVE)

            assert not thread.is_alive(), (
                f"{name}: seed={seed} plies={plies} で {MAX_SECONDS_PER_MOVE} 秒以内に返らなかった"
            )
            assert result["move"] in valid_moves
            assert game.board.board == board_before, f"{name}: 盤面が書き換えられた"
            checked += 1
    # 検査対象の局面が 1 つも無いとテストの意味が無いため確認する
    assert checked > 0
