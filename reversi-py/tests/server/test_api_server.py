# tests/server/test_api_server.py
import unittest
import json
import sys
from pathlib import Path

# プロジェクトルートをsys.pathに追加
# このテストファイル (test_api_server.py) の親 (server) のさらに親 (tests) のさらに親 (プロジェクトルート)
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# server ディレクトリ内の api_server から Flask アプリケーションインスタンスをインポート
# board モジュールから Board クラスもインポート（有効手の検証用）
try:
    from server.api_server import app
    from board import Board
except ImportError as e:
    print(f"テストのインポートエラー: {e}")
    print("server/api_server.py または board.py が見つからないか、インポートできません。")
    print("プロジェクト構造と sys.path を確認してください。")
    print(f"現在の sys.path: {sys.path}")
    sys.exit(1)


class TestApiServer(unittest.TestCase):

    def setUp(self):
        """各テストの前に実行されるセットアップ"""
        app.config['TESTING'] = True
        # Flask >= 2.0 では app.test_client() はコンテキストマネージャとしても使える
        self.app = app.test_client()
        # テスト用の初期盤面 (8x8)
        self.initial_board_data = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, -1, 0, 0, 0],
            [0, 0, 0, -1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ]
        # テスト用の有効手がない盤面 (例: 全て黒石)
        self.no_moves_board_data = [[-1] * 8 for _ in range(8)]

    def test_play_valid_move_black(self):
        """黒番(-1)で有効な手がある場合に、有効な手が返されることをテスト"""
        turn = -1
        payload = {'board': self.initial_board_data, 'turn': turn}
        # json パラメータで辞書を直接渡す
        response = self.app.post('/play', json=payload)

        self.assertEqual(response.status_code, 200)
        # response.get_json() で直接辞書を取得
        data = response.get_json()
        self.assertIn('move', data)
        self.assertTrue(isinstance(data['move'], list) or data['move'] is None)

        if isinstance(data['move'], list):
            self.assertEqual(len(data['move']), 2)
            # 返された手が実際に有効か検証 (Boardクラスを使用)
            temp_board = Board(board_size=8)
            temp_board.board = self.initial_board_data # 盤面を設定
            valid_moves = temp_board.get_valid_moves(turn)
            # レスポンスの move (リスト) をタプルに変換して比較
            self.assertIn(tuple(data['move']), valid_moves)

    def test_play_valid_move_white(self):
        """白番(1)で有効な手がある場合に、有効な手が返されることをテスト"""
        turn = 1
        payload = {'board': self.initial_board_data, 'turn': turn}
        response = self.app.post('/play', json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('move', data)
        self.assertTrue(isinstance(data['move'], list) or data['move'] is None)

        if isinstance(data['move'], list):
            self.assertEqual(len(data['move']), 2)
            # 返された手が実際に有効か検証
            temp_board = Board(board_size=8)
            temp_board.board = self.initial_board_data
            valid_moves = temp_board.get_valid_moves(turn)
            self.assertIn(tuple(data['move']), valid_moves)

    def test_play_no_valid_moves(self):
        """有効な手がない場合に {"move": null} が返されることをテスト"""
        turn = 1 # 白番で、盤面は全て黒石
        payload = {'board': self.no_moves_board_data, 'turn': turn}
        response = self.app.post('/play', json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, {'move': None})

    def test_play_invalid_input_missing_key(self):
        """リクエストに必要なキーがない場合に 400 エラーが返されることをテスト"""
        payload = {'board': self.initial_board_data} # 'turn' がない
        response = self.app.post('/play', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

        payload = {'turn': -1} # 'board' がない
        response = self.app.post('/play', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    def test_play_invalid_input_wrong_type(self):
        """リクエストのキーの型が違う場合に 400 エラーが返されることをテスト"""
        payload = {'board': 'not a list', 'turn': -1} # 'board' がリストでない
        response = self.app.post('/play', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

        payload = {'board': self.initial_board_data, 'turn': 'not an int'} # 'turn' が整数でない
        response = self.app.post('/play', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    def test_play_invalid_input_wrong_turn_value(self):
        """'turn' の値が -1 または 1 でない場合に 400 エラーが返されることをテスト"""
        payload = {'board': self.initial_board_data, 'turn': 0}
        response = self.app.post('/play', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

        payload = {'board': self.initial_board_data, 'turn': 2}
        response = self.app.post('/play', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    def test_play_invalid_board_format(self):
        """'board' の形式が不正な場合に 400 エラーが返されることをテスト"""
        # 正方形でないボード
        invalid_board = [[0, 0], [0, 0, 0]]
        payload = {'board': invalid_board, 'turn': -1}
        response = self.app.post('/play', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

        # 空のボード
        payload = {'board': [], 'turn': -1}
        response = self.app.post('/play', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

        # 行の長さが異なるボード
        invalid_board_row_len = [[0,0,0], [0,0]]
        payload = {'board': invalid_board_row_len, 'turn': 1}
        response = self.app.post('/play', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

        # 要素がリストでないボード
        invalid_board_element = [0, 1, 2]
        payload = {'board': invalid_board_element, 'turn': 1}
        response = self.app.post('/play', json=payload)
        self.assertEqual(response.status_code, 400) # 'board' must be a list of lists (or similar check)
        data = response.get_json()
        self.assertIn('error', data)


if __name__ == '__main__':
    # テストを実行
    unittest.main(module='tests.server.test_api_server')
