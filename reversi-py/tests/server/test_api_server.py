import unittest
from unittest.mock import patch

import pytest

pytest.importorskip("fastapi")

from fastapi import status
from fastapi.testclient import TestClient

from server.api_server import app

VALID_BOARD = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, -1, 0, 0, 0],
    [0, 0, 0, -1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]


class TestApiServer(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    # ── 正常系 ─────────────────────────────────────────────
    def test_play_valid_input(self):
        response = self.client.post(
            "/play", json={"board": VALID_BOARD, "turn": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("move", data)
        if data["move"] is not None:
            self.assertIsInstance(data["move"], list)

    def test_play_valid_input_turn_minus1(self):
        response = self.client.post(
            "/play", json={"board": VALID_BOARD, "turn": -1}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_play_default_agent_type_is_random(self):
        response = self.client.post(
            "/play", json={"board": VALID_BOARD, "turn": 1}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("move", response.json())

    # ── agent_type バリエーション ───────────────────────────
    def test_play_agent_type_first(self):
        payload = {"board": VALID_BOARD, "turn": 1, "agent_type": "first"}
        response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("move", data)
        from board import Board
        b = Board(board_size=8)
        b.board = [row[:] for row in VALID_BOARD]
        expected = list(b.get_valid_moves(1)[0])
        self.assertEqual(data["move"], expected)

    def test_play_agent_type_random(self):
        payload = {"board": VALID_BOARD, "turn": 1, "agent_type": "random"}
        response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("move", data)
        if data["move"] is not None:
            from board import Board
            b = Board(board_size=8)
            b.board = [row[:] for row in VALID_BOARD]
            valid = [list(m) for m in b.get_valid_moves(1)]
            self.assertIn(data["move"], valid)

    def test_play_agent_type_gain(self):
        payload = {"board": VALID_BOARD, "turn": 1, "agent_type": "gain"}
        response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("move", data)
        if data["move"] is not None:
            from board import Board
            b = Board(board_size=8)
            b.board = [row[:] for row in VALID_BOARD]
            valid = [list(m) for m in b.get_valid_moves(1)]
            self.assertIn(data["move"], valid)

    def test_play_agent_type_mcts(self):
        payload = {"board": VALID_BOARD, "turn": 1, "agent_type": "mcts"}
        with patch("server.api_server.MonteCarloTreeSearchAgent") as MockMCTS:
            MockMCTS.return_value.play.return_value = (2, 3)
            response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["move"], [2, 3])

    def test_play_agent_type_negamax(self) -> None:
        payload = {"board": VALID_BOARD, "turn": 1, "agent_type": "negamax"}
        with patch("server.api_server.NegamaxAgent") as MockNegamax:
            MockNegamax.return_value.play.return_value = (2, 3)
            response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["move"], [2, 3])

    def test_negamax_time_limit_env_var(self) -> None:
        """NEGAMAX_TIME_LIMIT_MS 環境変数が反映される。"""
        import os

        from unittest.mock import patch as mock_patch

        with mock_patch.dict(os.environ, {"NEGAMAX_TIME_LIMIT_MS": "123"}):
            from server.api_server import _select_agent

            agent = _select_agent("negamax")
        self.assertEqual(agent.time_limit_ms, 123)

    def test_select_agent_unknown_type_returns_none(self) -> None:
        """VALID_AGENT_TYPES 外の文字列を渡すと None を返す（行 87 カバー）。"""
        from server.api_server import _select_agent
        result = _select_agent("bogus_agent_type_xyz")
        self.assertIsNone(result)

    def test_outer_exception_handler_returns_500(self) -> None:
        """PlayRequest.model_dump() が RuntimeError を投げると外側 catch-all が 500 を返す（行 176-180 カバー）。"""
        from server.api_server import PlayRequest
        with patch.object(PlayRequest, "model_dump",
                          side_effect=RuntimeError("unexpected top-level error")):
            response = self.client.post(
                "/play",
                json={"board": VALID_BOARD, "turn": 1},
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Internal server error.")

    def test_play_invalid_agent_type(self):
        payload = {"board": VALID_BOARD, "turn": 1, "agent_type": "unknown"}
        response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("agent_type", response.json()["detail"])

    # ── turn バリデーション ─────────────────────────────────
    def test_play_invalid_input_invalid_turn_value(self):
        response = self.client.post(
            "/play", json={"board": [[0]], "turn": 0}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"detail": "Invalid input: 'turn' must be -1 or 1."},
        )

    def test_play_invalid_turn_two(self):
        response = self.client.post(
            "/play", json={"board": VALID_BOARD, "turn": 2}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── board バリデーション ────────────────────────────────
    def test_play_invalid_input_no_data(self):
        response = self.client.post("/play", json=None)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)
        self.assertEqual(
            response.json(),
            {"detail": [{"loc": ["body"], "msg": "Field required",
                         "type": "missing", "input": None}]},
        )

    def test_play_invalid_input_missing_fields(self):
        response = self.client.post("/play", json={"board": []})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)
        self.assertEqual(
            response.json(),
            {"detail": [{"loc": ["body", "turn"], "msg": "Field required",
                         "type": "missing", "input": {"board": []}}]},
        )

    def test_play_invalid_input_invalid_board_type(self):
        response = self.client.post(
            "/play", json={"board": "not a list", "turn": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)
        self.assertEqual(
            response.json(),
            {"detail": [{"loc": ["body", "board"],
                         "msg": "Input should be a valid list",
                         "type": "list_type",
                         "input": "not a list"}]},
        )

    def test_play_invalid_input_empty_row(self):
        response = self.client.post("/play", json={"board": [[]], "turn": 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"detail": "Invalid input: 'board' cannot be empty."},
        )

    def test_play_invalid_input_non_square_board(self):
        # サイズチェック (4-16) を通過する行数で、行の長さだけ不正にする
        non_square = [[0, 0, 0, 0], [0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        response = self.client.post(
            "/play", json={"board": non_square, "turn": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"detail": "Invalid input: 'board' must be a square matrix."},
        )

    def test_play_invalid_input_invalid_board_value(self):
        # サイズチェック (4-16) を通過する 4×4 盤面で不正な値 (2) を含める
        invalid_value_board = [[0] * 4 for _ in range(4)]
        invalid_value_board[0][0] = 2
        response = self.client.post(
            "/play", json={"board": invalid_value_board, "turn": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"detail": "Invalid input: 'board' must contain only -1, 0, or 1."},
        )

    def test_play_invalid_input_invalid_board_element_type(self):
        response = self.client.post(
            "/play", json={"board": [["not an int"]], "turn": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)
        self.assertEqual(
            response.json(),
            {"detail": [{"loc": ["body", "board", 0, 0],
                         "msg": "Input should be a valid integer, unable to parse string as an integer",
                         "type": "int_parsing",
                         "input": "not an int"}]},
        )

    # ── board バリデーション───────────────────────────────
    def test_play_invalid_board_not_list_of_lists(self):
        """board が list of lists でない場合 422 を返す"""
        response = self.client.post(
            "/play",
            json={"board": "not a list", "turn": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)
        detail = response.json()["detail"]
        self.assertTrue(any("board" in err.get("loc", []) for err in detail))

    def test_play_invalid_board_contains_non_list(self):
        """board の要素が list でない場合 422 を返す"""
        response = self.client.post(
            "/play",
            json={"board": [1, 2, 3], "turn": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)
        detail = response.json()["detail"]
        self.assertTrue(any("board" in err.get("loc", []) for err in detail))

    def test_play_board_too_large_is_rejected(self):
        """巨大盤面（DoS 防止の上限超え）は 400 を返す"""
        size = 32
        huge_board = [[0] * size for _ in range(size)]
        response = self.client.post(
            "/play",
            json={"board": huge_board, "turn": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("size", response.json()["detail"])

    def test_play_board_too_small_is_rejected(self):
        """下限（4）未満の盤面は 400 を返す"""
        tiny_board = [[0, 0], [0, 0]]
        response = self.client.post(
            "/play",
            json={"board": tiny_board, "turn": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("size", response.json()["detail"])

    # ── 500 系エラーハンドリング（カバレッジ確保）───────────
    def test_play_agent_raises_exception_returns_500(self):
        """agent.play() が例外を投げると 500 を返す"""
        with patch("server.api_server.RandomAgent") as MockAgent:
            MockAgent.return_value.play.side_effect = RuntimeError("agent crash")
            response = self.client.post(
                "/play",
                json={"board": VALID_BOARD, "turn": 1, "agent_type": "random"},
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_play_game_creation_exception_returns_500(self):
        """_create_game() が例外を投げると 500 を返す"""
        with patch("server.api_server._create_game",
                   side_effect=RuntimeError("game creation failed")):
            response = self.client.post(
                "/play",
                json={"board": VALID_BOARD, "turn": 1},
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


if __name__ == "__main__":
    unittest.main()
