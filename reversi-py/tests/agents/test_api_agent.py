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
# --- Game クラスもインポート ---
# Mock オブジェクトの代わりに実際の Game オブジェクトのメソッドシグネチャを使う場合があるため
# (ただし、このテストでは Mock で十分)
# from game import Game
# -----------------------------

class TestApiAgent(unittest.TestCase):

    def setUp(self):
        """各テストの前に実行されるセットアップ"""
        self.api_url = 'http://fake-api.com/play'
        # --- 修正: timeout 引数を渡す ---
        # ApiAgent の __init__ が timeout を受け取るように修正されている前提
        self.agent = ApiAgent(api_url=self.api_url, timeout=10)
        # --------------------------------
        # ダミーのゲームオブジェクトを作成するヘルパー
        self.mock_game = self._create_mock_game([[0]*8]*8, -1, 8) # デフォルト盤面と手番

    def _create_mock_game(self, board, turn, board_size):
        """テスト用のモックゲームオブジェクトを作成"""
        mock_game = Mock()
        mock_game.get_board.return_value = board
        mock_game.turn = turn
        mock_game.get_board_size.return_value = board_size
        return mock_game

    # --- 初期化テスト ---
    def test_init_raises_error_on_empty_url(self):
        """初期化時に空のURLが渡された場合に ValueError を発生させることをテスト"""
        with self.assertRaises(ValueError):
            ApiAgent(api_url="")

    # --- 追加: None URL のテスト ---
    def test_init_raises_error_on_none_url(self):
        """初期化時に None のURLが渡された場合に ValueError を発生させることをテスト"""
        with self.assertRaises(ValueError):
            ApiAgent(api_url=None)
    # -----------------------------

    # --- 追加: timeout 初期化テスト ---
    def test_init_with_default_timeout(self):
        """timeout引数を指定しない場合、デフォルト値(5)が設定されることをテスト"""
        agent = ApiAgent(api_url=self.api_url)
        self.assertEqual(agent.timeout, 5) # デフォルト値が5であることを確認

    def test_init_with_custom_timeout(self):
        """timeout引数を指定した場合、その値が設定されることをテスト"""
        agent = ApiAgent(api_url=self.api_url, timeout=20)
        self.assertEqual(agent.timeout, 20)
    # ---------------------------------

    # --- playメソッドのテスト ---
    @patch('agents.api_agent.requests.post')
    def test_play_returns_valid_move(self, mock_post):
        """APIが有効な手 [row, col] を返した場合、タプル (row, col) を返すことをテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'move': [3, 4]}
        mock_post.return_value = mock_response

        # テスト実行 (timeout=10 のエージェントを使用)
        move = self.agent.play(self.mock_game)

        # 検証
        self.assertEqual(move, (3, 4))
        # requests.post が正しい引数で呼び出されたか確認
        expected_payload = {'board': [[0]*8]*8, 'turn': -1}
        mock_post.assert_called_once_with(
            self.api_url,
            json=expected_payload,
            timeout=10 # setUp で設定したタイムアウト値
        )

    # --- 追加: デフォルト timeout 使用テスト ---
    @patch('agents.api_agent.requests.post')
    def test_play_uses_default_timeout(self, mock_post):
        """デフォルトのtimeout値を使用してAPIが呼び出されることをテスト"""
        # timeoutを指定せずにエージェントを初期化
        agent_default_timeout = ApiAgent(api_url=self.api_url)
        self.assertEqual(agent_default_timeout.timeout, 5) # デフォルト値確認

        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'move': [1, 2]}
        mock_post.return_value = mock_response

        # playメソッドを実行
        agent_default_timeout.play(self.mock_game)

        # requests.post がデフォルトのtimeout値(5)で呼び出されたか確認
        expected_payload = {'board': [[0]*8]*8, 'turn': -1}
        mock_post.assert_called_once_with(
            self.api_url,
            json=expected_payload,
            timeout=5 # デフォルトのタイムアウト値
        )
    # --------------------------------------

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

    # --- 追加: 一般的なリクエスト例外のテスト ---
    @patch('agents.api_agent.requests.post')
    def test_play_returns_none_on_generic_request_exception(self, mock_post):
        """APIリクエスト中に一般的なRequestExceptionが発生した場合、Noneを返すことをテスト"""
        # requests.exceptions.RequestException は Timeout や ConnectionError の基底クラスでもあるため、
        # これら以外の RequestException をシミュレートする
        mock_post.side_effect = requests.exceptions.RequestException("Some generic request error")

        move = self.agent.play(self.mock_game)

        self.assertIsNone(move)
        mock_post.assert_called_once()
    # -----------------------------------------

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

    # --- 追加: 予期せぬ例外のテスト ---
    @patch('agents.api_agent.requests.post')
    def test_play_returns_none_on_unexpected_exception(self, mock_post):
        """API呼び出しまたはその後の処理で予期せぬ例外が発生した場合、Noneを返すことをテスト"""
        # ケース1: requests.post 自体が予期せぬ例外を出す
        mock_post.side_effect = Exception("Unexpected error during request")

        move = self.agent.play(self.mock_game)
        self.assertIsNone(move, "Should return None on unexpected exception during request")
        mock_post.assert_called_once()

        # ケース2: レスポンス処理中に予期せぬ例外が出る (例: json() の挙動がおかしい)
        mock_post.reset_mock() # モックをリセット
        mock_response = Mock()
        mock_response.status_code = 200
        # json() メソッドが予期せぬ例外を出すように設定
        mock_response.json.side_effect = Exception("Unexpected error during JSON processing")
        mock_post.side_effect = None # requests.post は正常なレスポンスを返すように戻す
        mock_post.return_value = mock_response

        move = self.agent.play(self.mock_game)
        self.assertIsNone(move, "Should return None on unexpected exception during response processing")
        mock_post.assert_called_once()
    # ------------------------------------


if __name__ == '__main__':
    # テストを実行 (モジュール名を指定)
    unittest.main(module='tests.agents.test_api_agent')
