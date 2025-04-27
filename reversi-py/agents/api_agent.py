# agents/api_agent.py
from .base_agent import Agent
import requests
import time
import logging
import os  # 環境変数を参照するために追加

# ロギングの設定
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
numeric_level = getattr(logging, log_level, None)
if not isinstance(numeric_level, int):
    print(f"Invalid log level: {log_level}, defaulting to INFO")
    numeric_level = logging.INFO
logging.basicConfig(level=numeric_level, format='%(asctime)s - %(levelname)s - %(message)s')

class ApiAgent(Agent):
    # --- 修正: __init__ メソッドで timeout 引数を受け取る ---
    def __init__(self, api_url, timeout=5):
        """
        ApiAgentを初期化します。
        Args:
            api_url (str): 接続先のAPIサーバーのURL。
            timeout (int, optional): APIリクエストのタイムアウト時間(秒)。デフォルトは5。
        Raises:
            ValueError: api_urlが空の場合。
        """
        if not api_url: # 行 10
            raise ValueError("API URL cannot be empty.")
        self.api_url = api_url
        # --- 修正: timeout をインスタンス変数に設定 ---
        self.timeout = timeout # 行 15-18 あたり
        # -----------------------------------------

    def play(self, game, timeout=None):
        """
        APIサーバーに現在の盤面と手番を送信し、次の手を取得します。
        Args:
            game (Game): 現在のゲーム状態。
            timeout (int, optional): APIリクエストのタイムアウト時間(秒)。指定しない場合は、__init__で設定された値を使用。
        Returns:
            tuple[int, int] | None: APIから取得した手 (row, col)、またはエラー時は None。
        """
        board_state = game.get_board()
        turn = game.turn
        board_size = game.get_board_size()

        payload = {
            'board': board_state,
            'turn': turn
        }

        try:
            # APIサーバーにPOSTリクエストを送信
            # timeout が指定されていればそれを使用し、そうでなければ self.timeout を使用
            response = requests.post(self.api_url, json=payload, timeout=timeout if timeout is not None else self.timeout)
            response.raise_for_status()  # ステータスコードが200番台以外ならHTTPErrorを送出

            # レスポンスをJSONとして解析
            data = response.json()

            # レスポンス形式のバリデーション
            if not isinstance(data, dict):
                logging.warning(f"API response is not a dictionary: {data}")
                return None

            if 'move' not in data:
                logging.warning(f"API response missing 'move' key: {data}")
                return None

            move = data['move']

            if move is None:
                # APIが明示的にNoneを返した場合 (パスなど)
                return None

            if not isinstance(move, list):
                logging.warning(f"API returned invalid move format: {move}")
                return None

            if len(move) != 2:
                logging.warning(f"API returned invalid move format: {move}")
                return None

            if not all(isinstance(x, int) for x in move):
                logging.warning(f"API returned invalid move format: {move}")
                return None

            row, col = move
            if not (0 <= row < board_size and 0 <= col < board_size):
                logging.warning(f"API returned out-of-bounds move: {move}")
                return None

            return tuple(move) # タプル形式で返す

        except requests.exceptions.Timeout:
            logging.error(f"API request timed out after {self.timeout} seconds.")
            return None
        except requests.exceptions.ConnectionError:
            logging.error(f"Failed to connect to API server at {self.api_url}.")
            return None
        except requests.exceptions.RequestException as e:
            # HTTPError を含むその他のリクエスト関連エラー
            logging.error(f"API request failed: {e}")
            return None
        except ValueError as e:
            # JSONデコードエラーなど
            logging.error(f"Failed to parse API response: {e}")
            return None
        # --- 修正: 予期せぬ例外をキャッチ ---
        except Exception as e: # 行 98-100 あたり
            # 予期せぬその他のエラー
            logging.exception(f"An unexpected error occurred during API call or processing: {e}")
            return None
        # ---------------------------------
