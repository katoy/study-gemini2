"""API サーバーと ApiAgent の統合テスト。

実際の uvicorn サーバープロセスに対して requests / ApiAgent で通信し、
エンドツーエンドの動作を検証する。
"""
import random
from typing import Any, cast
from unittest.mock import Mock

import requests

from agents.api_agent import ApiAgent
from config.agents_config import AGENT_DEFINITIONS
from game import Game
from server.api_server import VALID_AGENT_TYPES

STANDARD_BOARD = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, -1, 0, 0, 0],
    [0, 0, 0, -1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]


def _make_mock_game(board: list, turn: int = 1, size: int = 8) -> Mock:
    game = Mock()
    game.get_board.return_value = board
    game.turn = turn
    game.get_board_size.return_value = size
    return game


def _configured_timeout(agent_type: str) -> int:
    """AGENT_DEFINITIONS に設定されたタイムアウト秒数（未指定時は ApiAgent 既定の 5 秒）を返す。"""
    for raw_def in AGENT_DEFINITIONS:
        defn = cast(dict[str, Any], raw_def)
        params = defn.get("params", {})
        if params.get("agent_type") == agent_type:
            return int(params.get("timeout", 5))
    # GUI 未掲載の "negamax"（既定 3000ms、テスト時は 200ms）向けの余裕あるタイムアウト
    return 10


def _make_endgame_position(target_empties: int = 14) -> Game:
    """空きマスが target_empties 以下で合法手が 2 手以上ある 8x8 終盤局面を生成する。"""
    for seed in range(20):
        rng = random.Random(seed)
        game = Game(board_size=8)
        while not game.game_over:
            empties = sum(row.count(0) for row in game.get_board())
            valid_moves = game.get_valid_moves()
            if empties <= target_empties and len(valid_moves) >= 2:
                return game
            if valid_moves:
                row, col = rng.choice(valid_moves)
                game.place_stone(row, col)
            game.switch_turn()
            game.check_game_over()
    raise AssertionError("終盤テスト局面の生成に失敗しました")


class TestServerEndpoint:
    """requests を直接使って /play エンドポイントを検証するテスト群。"""

    def test_server_is_reachable(self, api_server_url: str) -> None:
        response = requests.post(
            f"{api_server_url}/play",
            json={"board": STANDARD_BOARD, "turn": 1},
            timeout=5,
        )
        assert response.status_code == 200

    def test_play_returns_valid_move_structure(self, api_server_url: str) -> None:
        response = requests.post(
            f"{api_server_url}/play",
            json={"board": STANDARD_BOARD, "turn": 1},
            timeout=5,
        )
        data = response.json()
        assert "move" in data
        if data["move"] is not None:
            assert isinstance(data["move"], list)
            assert len(data["move"]) == 2
            assert all(isinstance(x, int) for x in data["move"])

    def test_play_all_agent_types_respond_200(self, api_server_url: str) -> None:
        for agent_type in sorted(VALID_AGENT_TYPES):
            response = requests.post(
                f"{api_server_url}/play",
                json={"board": STANDARD_BOARD, "turn": 1, "agent_type": agent_type},
                timeout=_configured_timeout(agent_type),
            )
            assert response.status_code == 200, (
                f"agent_type={agent_type!r} returned {response.status_code}"
            )
            data = response.json()
            assert isinstance(data.get("move"), list)
            assert len(data["move"]) == 2

    def test_play_invalid_turn_returns_400(self, api_server_url: str) -> None:
        response = requests.post(
            f"{api_server_url}/play",
            json={"board": STANDARD_BOARD, "turn": 99},
            timeout=5,
        )
        assert response.status_code == 400

    def test_play_invalid_agent_type_returns_400(self, api_server_url: str) -> None:
        response = requests.post(
            f"{api_server_url}/play",
            json={"board": STANDARD_BOARD, "turn": 1, "agent_type": "cheating"},
            timeout=5,
        )
        assert response.status_code == 400


class TestApiAgentIntegration:
    """ApiAgent が実際のサーバーと通信するエンドツーエンドテスト群。"""

    def test_api_agent_returns_valid_move(self, api_server_url: str) -> None:
        agent = ApiAgent(
            api_url=f"{api_server_url}/play",
            timeout=10,
            agent_type="first",
        )
        move = agent.play(_make_mock_game(STANDARD_BOARD, turn=1))
        assert move is not None
        row, col = move
        assert 0 <= row < 8
        assert 0 <= col < 8

    def test_api_agent_with_random_agent_type(self, api_server_url: str) -> None:
        agent = ApiAgent(
            api_url=f"{api_server_url}/play",
            timeout=10,
            agent_type="random",
        )
        move = agent.play(_make_mock_game(STANDARD_BOARD, turn=-1))
        assert move is not None

    def test_api_agent_handles_server_error_gracefully(
        self, api_server_url: str
    ) -> None:
        """サーバーが 400 を返しても ApiAgent は None を返してクラッシュしない。"""
        agent = ApiAgent(
            api_url=f"{api_server_url}/play",
            timeout=10,
            agent_type="invalid_type",
        )
        move = agent.play(_make_mock_game(STANDARD_BOARD, turn=1))
        assert move is None

    def test_api_agent_wrong_url_returns_none(self) -> None:
        """存在しないサーバーへの接続失敗時に ApiAgent は None を返す。"""
        agent = ApiAgent(
            api_url="http://127.0.0.1:19999/play",
            timeout=2,
        )
        move = agent.play(_make_mock_game(STANDARD_BOARD, turn=1))
        assert move is None

    def test_alphazero_minimax_endgame_does_not_timeout(
        self, api_server_url: str
    ) -> None:
        """終盤読み切り（空き 14 以下）で GUI 実設定の ApiAgent がタイムアウトしない。"""
        az_def = next(
            cast(dict[str, Any], d)
            for d in AGENT_DEFINITIONS
            if cast(dict[str, Any], d).get("params", {}).get("agent_type")
            == "alphazero_minimax"
        )
        params = dict(az_def["params"])
        params["api_url"] = f"{api_server_url}/play"

        agent = ApiAgent(**params)
        endgame = _make_endgame_position(target_empties=14)
        move = agent.play(endgame)
        assert move is not None
        assert move in endgame.get_valid_moves()
