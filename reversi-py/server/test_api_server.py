import unittest
import json
from fastapi.testclient import TestClient
from api_server import app
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
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(
            response.json(),
            {"detail":[{"loc":["body"],"msg":"Field required","type":"missing","input":None}]}
        )

    def test_play_invalid_input_missing_fields(self):
        # 無効な入力 (必須フィールドの欠落) に対するテスト
        response = self.client.post("/play", json={"board": []})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(
            response.json(),
            {"detail":[{"loc":["body","turn"],"msg":"Field required","type":"missing","input":{"board":[]}}]}
        )

    def test_play_invalid_input_invalid_board_type(self):
        # 無効な入力 (無効な盤面タイプ) に対するテスト
        response = self.client.post("/play", json={"board": "not a list", "turn": 1})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(
            response.json(),
            {"detail":[
                {"loc":["body","board"],
                 "msg":"Input should be a valid list",
                 "type":"list_type",
                 "input":"not a list"}
            ]}
        )

    def test_play_invalid_input_invalid_board_element_type(self):
        # 無効な入力 (無効な盤面要素タイプ) に対するテスト
        response = self.client.post("/play", json={"board":[["not an int"]], "turn": 1})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
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

if __name__ == "__main__":
    unittest.main()
