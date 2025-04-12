# agents/api_agent.py
import requests
import logging
import sys
from pathlib import Path

# プロジェクトルートをsys.pathに追加 (環境に合わせて調整が必要な場合があります)
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# base_agent モジュールから Agent クラスをインポート
try:
    from agents.base_agent import Agent
except ImportError:
    print("エラー: agents/base_agent.py が見つからないか、インポートできません。")
    print("プロジェクト構造を確認し、必要であれば sys.path を調整してください。")
    sys.exit(1)

# ロガーの設定 (エラー出力用)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ApiAgent(Agent):
    """
    ネットワーク上のAPIサーバーに問い合わせて手を選択するエージェント。
    """
    def __init__(self, api_url: str):
        """
        Args:
            api_url (str): 問い合わせ先のAPIエンドポイントURL (例: 'http://127.0.0.1:5001/play')
        """
        if not api_url:
            raise ValueError("API URL cannot be empty.")
        self.api_url = api_url
        # タイムアウト設定 (秒)
        self.timeout = 2.0 # 必要に応じて調整

    def play(self, game):
        """
        現在のゲーム状態をAPIサーバーに送信し、返された手を取得する。
        Args:
            game (Game): 現在のゲームオブジェクト。
        Returns:
            tuple[int, int] | None: APIサーバーから返された手 (row, col)、またはエラーや手がない場合は None。
        """
        try:
            board_state = game.get_board()
            turn = game.turn

            payload = {
                "board": board_state,
                "turn": turn
            }

            # APIサーバーにPOSTリクエストを送信
            response = requests.post(self.api_url, json=payload, timeout=self.timeout)
            response.raise_for_status() # ステータスコードが 2xx でない場合に例外を発生させる

            # レスポンスをJSONとしてパース
            data = response.json()

            # 'move' キーが存在し、値がリスト形式かNoneか確認
            if 'move' not in data:
                logger.error(f"Invalid API response from {self.api_url}: 'move' key missing. Response: {data}")
                return None

            move_data = data['move']

            if move_data is None:
                # APIサーバーが有効な手がないと判断した場合
                return None
            elif isinstance(move_data, list) and len(move_data) == 2:
                # 有効な手が返された場合、タプルに変換して返す
                row, col = move_data
                # 簡単なバリデーション (整数であること、範囲内であること)
                board_size = game.get_board_size()
                if isinstance(row, int) and isinstance(col, int) and \
                    0 <= row < board_size and 0 <= col < board_size:
                    return (row, col)
                else:
                    logger.error(f"Invalid move data received from {self.api_url}: {move_data}. Board size: {board_size}")
                    return None
            else:
                # 予期しない形式の 'move' データ
                logger.error(f"Unexpected 'move' format from {self.api_url}: {move_data}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"API request timed out to {self.api_url} after {self.timeout} seconds.")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed to {self.api_url}: {e}")
            return None
        except (ValueError, TypeError) as e: # JSONデコードエラーなど
            logger.error(f"Failed to parse API response from {self.api_url}: {e}")
            return None
        except Exception as e: # 予期せぬエラー
            logger.error(f"An unexpected error occurred during API agent play: {e}")
            return None

