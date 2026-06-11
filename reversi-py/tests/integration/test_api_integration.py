"""API サーバーと ApiAgent の統合テスト。

実際の uvicorn サーバープロセスに対して requests / ApiAgent で通信し、
エンドツーエンドの動作を検証する。
"""
from unittest.mock import Mock

import requests

from agents.api_agent import ApiAgent

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
        for agent_type in ("first", "random", "gain"):
            response = requests.post(
                f"{api_server_url}/play",
                json={"board": STANDARD_BOARD, "turn": 1, "agent_type": agent_type},
                timeout=5,
            )
            assert response.status_code == 200, (
                f"agent_type={agent_type!r} returned {response.status_code}"
            )

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
