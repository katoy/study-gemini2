# agents/api_agent.py
from .base_agent import Agent
import requests
import time
import logging # ロギングを追加

# ロガーの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

    def play(self, game):
        """
        APIサーバーに現在の盤面と手番を送信し、次の手を取得します。
        Args:
            game (Game): 現在のゲーム状態。
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
            response = requests.post(self.api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()  # ステータスコードが200番台以外ならHTTPErrorを送出

            # レスポンスをJSONとして解析
            data = response.json()

            # 'move' キーが存在し、その値がリスト形式か確認
            if 'move' in data and isinstance(data['move'], list):
                move = data['move']
                # 手の形式 (長さ2のリストで、要素が整数) と範囲を検証
                if len(move) == 2 and all(isinstance(x, int) for x in move):
                    row, col = move
                    if 0 <= row < board_size and 0 <= col < board_size:
                        return tuple(move) # タプル形式で返す
                    else:
                        logging.warning(f"API returned out-of-bounds move: {move}")
                        return None
                else:
                    logging.warning(f"API returned invalid move format: {move}")
                    return None
            elif 'move' in data and data['move'] is None:
                # APIが明示的にNoneを返した場合 (パスなど)
                return None
            else:
                logging.warning(f"API response missing 'move' key or invalid format: {data}")
                return None

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
