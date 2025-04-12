# tests/agents/test_api_agent.py
import unittest
from unittest.mock import patch, Mock
import sys
from pathlib import Path
import requests # requests.exceptions を使うためにインポート

# プロジェクトルートをsys.pathに追加
# このテストファイル (test_api_agent.py) の親 (agents) のさらに親 (tests) のさらに親 (プロジェクトルート)
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# agents.api_agent から ApiAgent クラスをインポート
try:
    from agents.api_agent import ApiAgent
except ImportError as e:
    print(f"テストのインポートエラー: {e}")
    print("agents/api_agent.py が見つからないか、インポートできません。")
    print("プロジェクト構造と sys.path を確認してください。")
    print(f"現在の sys.path: {sys.path}")
    sys.exit(1)

class TestApiAgent(unittest.TestCase):

    def setUp(self):
        """各テストの前に実行されるセットアップ"""
        self.api_url = 'http://fake-api.com/play'
        self.agent = ApiAgent(api_url=self.api_url)
        # ダミーのゲームオブジェクトを作成するヘルパー
        self.mock_game = self._create_mock_game([[0]*8]*8, -1, 8) # デフォルト盤面と手番

    def _create_mock_game(self, board, turn, board_size):
        """テスト用のモックゲームオブジェクトを作成"""
        mock_game = Mock()
        mock_game.get_board.return_value = board
        mock_game.turn = turn
        mock_game.get_board_size.return_value = board_size
        return mock_game

    @patch('agents.api_agent.requests.post')
    def test_play_returns_valid_move(self, mock_post):
        """APIが有効な手 [row, col] を返した場合、タプル (row, col) を返すことをテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'move': [3, 4]}
        mock_post.return_value = mock_response

        # テスト実行
        move = self.agent.play(self.mock_game)

        # 検証
        self.assertEqual(move, (3, 4))
        # requests.post が正しい引数で呼び出されたか確認
        expected_payload = {'board': [[0]*8]*8, 'turn': -1}
        mock_post.assert_called_once_with(
            self.api_url,
            json=expected_payload,
            timeout=self.agent.timeout # 設定したタイムアウト値
        )

    @patch('agents.api_agent.requests.post')
    def test_play_returns_none_when_api_returns_null(self, mock_post):
        """APIが {"move": null} を返した場合、None を返すことをテスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'move': None}
        mock_post.return_value = mock_response

        move = self.agent.play(self.mock_game)

        self.assertIsNone(move)
        mock_post.assert_called_once()

    @patch('agents.api_agent.requests.post')
    def test_play_returns_none_on_api_error_status(self, mock_post):
        """APIがエラーステータスコード (例: 500) を返した場合、None を返すことをテスト"""
        mock_response = Mock()
        mock_response.status_code = 500
        # raise_for_status() が呼び出されたときに HTTPError を発生させるように設定
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
        mock_post.return_value = mock_response

        move = self.agent.play(self.mock_game)

        self.assertIsNone(move)
        mock_post.assert_called_once()

    @patch('agents.api_agent.requests.post')
    def test_play_returns_none_on_timeout(self, mock_post):
        """APIリクエストがタイムアウトした場合、None を返すことをテスト"""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        move = self.agent.play(self.mock_game)

        self.assertIsNone(move)
        mock_post.assert_called_once()

    @patch('agents.api_agent.requests.post')
    def test_play_returns_none_on_connection_error(self, mock_post):
        """APIサーバーへの接続に失敗した場合、None を返すことをテスト"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        move = self.agent.play(self.mock_game)

        self.assertIsNone(move)
        mock_post.assert_called_once()

    @patch('agents.api_agent.requests.post')
    def test_play_returns_none_on_invalid_json_response(self, mock_post):
        """APIが不正なJSONレスポンスを返した場合、None を返すことをテスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON") # JSONデコードエラーをシミュレート
        mock_post.return_value = mock_response

        move = self.agent.play(self.mock_game)

        self.assertIsNone(move)
        mock_post.assert_called_once()

    @patch('agents.api_agent.requests.post')
    def test_play_returns_none_if_move_key_missing(self, mock_post):
        """APIレスポンスに 'move' キーがない場合、None を返すことをテスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'other_key': 'value'} # 'move' がない
        mock_post.return_value = mock_response

        move = self.agent.play(self.mock_game)

        self.assertIsNone(move)
        mock_post.assert_called_once()

    @patch('agents.api_agent.requests.post')
    def test_play_returns_none_if_move_format_invalid(self, mock_post):
        """APIレスポンスの 'move' の形式が不正な場合、None を返すことをテスト"""
        invalid_moves = [
            {'move': 'not a list'},
            {'move': [1]}, # 要素数が足りない
            {'move': [1, 2, 3]}, # 要素数が多い
            {'move': ['a', 'b']}, # 要素が整数でない
            {'move': [8, 8]} # 範囲外 (board_size=8 の場合)
        ]
        for response_json in invalid_moves:
            with self.subTest(response_json=response_json):
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = response_json
                mock_post.return_value = mock_response
                mock_post.reset_mock() # 前回の呼び出し情報をリセット

                move = self.agent.play(self.mock_game)

                self.assertIsNone(move)
                mock_post.assert_called_once()

    def test_init_raises_error_on_empty_url(self):
        """初期化時に空のURLが渡された場合に ValueError を発生させることをテスト"""
        with self.assertRaises(ValueError):
            ApiAgent(api_url="")


if __name__ == '__main__':
    # テストを実行 (モジュール名を指定)
    unittest.main(module='tests.agents.test_api_agent')
