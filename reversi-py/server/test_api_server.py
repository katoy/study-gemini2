import unittest
import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from server.api_server import app
from fastapi import status

class TestApiServer(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_play_valid_input(self):
        # 有効な入力に対するテスト
        valid_payload = {
            "board": [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, -1, 0, 0, 0],
                [0, 0, 0, -1, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0]
            ],
            "turn": 1
        }
        response = self.client.post("/play", json=valid_payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("move", data)
        # move が None でない場合、リストであることを確認
        if data["move"] is not None:
            self.assertIsInstance(data["move"], list)

    def test_play_invalid_input_no_data(self):
        # 無効な入力 (データなし) に対するテスト
        response = self.client.post("/play", json=None)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)
        self.assertEqual(
            response.json(),
            {"detail":[{"loc":["body"],"msg":"Field required","type":"missing","input":None}]}
        )

    def test_play_invalid_input_missing_fields(self):
        # 無効な入力 (必須フィールドの欠落) に対するテスト
        response = self.client.post("/play", json={"board": []})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)
        self.assertEqual(
            response.json(),
            {"detail":[{"loc":["body","turn"],"msg":"Field required","type":"missing","input":{"board":[]}}]}
        )

    def test_play_invalid_input_invalid_board_type(self):
        # 無効な入力 (無効な盤面タイプ) に対するテスト
        response = self.client.post("/play", json={"board": "not a list", "turn": 1})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)
        self.assertEqual(
            response.json(),
            {"detail":[
                {"loc":["body","board"],
                 "msg":"Input should be a valid list",
                 "type":"list_type",
                 "input":"not a list"}
            ]}
        )

    def test_play_invalid_input_empty_row(self):
        # 無効な入力 (空の行) に対するテスト
        response = self.client.post("/play", json={"board": [[]], "turn": 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"detail":"Invalid input: 'board' cannot be empty."}
        )

    def test_play_invalid_input_non_square_board(self):
        # 無効な入力 (正方行列でない盤面) に対するテスト
        response = self.client.post("/play", json={"board": [[0, 0], [0]], "turn": 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"detail":"Invalid input: 'board' must be a square matrix."}
        )

    def test_play_invalid_input_invalid_board_value(self):
        # 無効な入力 (盤面値が -1, 0, 1 以外) に対するテスト
        response = self.client.post("/play", json={"board": [[2]], "turn": 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"detail":"Invalid input: 'board' must contain only -1, 0, or 1."}
        )

    def test_play_invalid_input_invalid_board_element_type(self):
        # 無効な入力 (無効な盤面要素タイプ) に対するテスト
        response = self.client.post("/play", json={"board":[["not an int"]], "turn": 1})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)
        self.assertEqual(
            response.json(),
            {"detail":[
                {"loc":["body","board",0,0],
                 "msg":"Input should be a valid integer, unable to parse string as an integer",
                 "type":"int_parsing",
                 "input":"not an int"}
            ]}
        )

    def test_play_invalid_input_invalid_turn_value(self):
        # 無効な入力 (turn の値が不正) に対するテスト
        response = self.client.post("/play", json={"board":[[0]], "turn": 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"detail":"Invalid input: 'turn' must be -1 or 1."}
        )

    # agent_type パラメータのテスト
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

    def test_play_agent_type_first(self):
        """agent_type=first は合法手の先頭を返す"""
        payload = {"board": self.VALID_BOARD, "turn": 1, "agent_type": "first"}
        response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("move", data)
        # 先頭手は board.get_valid_moves(1)[0] と一致する
        from board import Board
        b = Board(board_size=8)
        b.board = [row[:] for row in self.VALID_BOARD]
        expected = list(b.get_valid_moves(1)[0])
        self.assertEqual(data["move"], expected)

    def test_play_agent_type_random(self):
        """agent_type=random は合法手の中からいずれかを返す"""
        payload = {"board": self.VALID_BOARD, "turn": 1, "agent_type": "random"}
        response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("move", data)
        if data["move"] is not None:
            from board import Board
            b = Board(board_size=8)
            b.board = [row[:] for row in self.VALID_BOARD]
            valid = [list(m) for m in b.get_valid_moves(1)]
            self.assertIn(data["move"], valid)

    def test_play_agent_type_gain(self):
        """agent_type=gain は合法手のうちフリップ数最大の手を返す"""
        payload = {"board": self.VALID_BOARD, "turn": 1, "agent_type": "gain"}
        response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("move", data)
        if data["move"] is not None:
            from board import Board
            b = Board(board_size=8)
            b.board = [row[:] for row in self.VALID_BOARD]
            valid = [list(m) for m in b.get_valid_moves(1)]
            self.assertIn(data["move"], valid)

    def test_play_agent_type_mcts(self):
        """agent_type=mcts は MCTS エージェントの手を返す（モック）"""
        from unittest.mock import patch
        payload = {"board": self.VALID_BOARD, "turn": 1, "agent_type": "mcts"}
        with patch("server.api_server.MonteCarloTreeSearchAgent") as MockMCTS:
            mock_instance = MockMCTS.return_value
            mock_instance.play.return_value = (2, 3)
            response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["move"], [2, 3])

    def test_play_invalid_agent_type(self):
        """未知の agent_type は 400 を返す"""
        payload = {"board": self.VALID_BOARD, "turn": 1, "agent_type": "unknown"}
        response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("agent_type", response.json()["detail"])

    def test_play_default_agent_type_is_random(self):
        """agent_type 省略時は random として動作する（後方互換）"""
        payload = {"board": self.VALID_BOARD, "turn": 1}
        response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("move", response.json())

if __name__ == "__main__":
    unittest.main()
