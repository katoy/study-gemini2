# agents/api_agent.py
import logging
from typing import Optional, Tuple, TYPE_CHECKING

import requests

from .base_agent import Agent

if TYPE_CHECKING:
    from game import Game

logger = logging.getLogger(__name__)


class ApiAgent(Agent):
    """外部 API サーバーから手を取得する AI エージェント。"""

    def __init__(self, api_url: str, timeout: int = 5) -> None:
        """ApiAgent を初期化します。

        Args:
            api_url: 接続先の API サーバーの URL。
            timeout: API リクエストのタイムアウト時間（秒）。デフォルトは 5。
                推奨値は 5 以上。MCTS(time_limit_ms=4000) より大きい値を指定。

        Raises:
            ValueError: api_url が空の場合。
        """
        if not api_url:
            raise ValueError("API URL cannot be empty.")
        self.api_url = api_url
        self.timeout = timeout

    def play(
        self, game: 'Game', timeout: Optional[int] = None
    ) -> Optional[Tuple[int, int]]:
        """API サーバーから次の手を取得します。

        Args:
            game: 現在のゲーム状態。
            timeout: API リクエストのタイムアウト時間（秒）。
                指定しない場合は __init__ で設定された値を使用。

        Returns:
            (row, col) のタプル、またはエラー時は None。
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
            # SSL 検証を有効化（MitM 攻撃対策）
            # timeout が指定されていればそれを使用し、そうでなければ self.timeout を使用
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=timeout if timeout is not None else self.timeout,
                verify=True
            )
            # ステータスコードが200番台以外ならHTTPErrorを送出
            response.raise_for_status()

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
            logger.error(f"API request timed out after {self.timeout} seconds.")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to API server at {self.api_url}.")
            return None
        except requests.exceptions.RequestException:
            # HTTPError を含むその他のリクエスト関連エラー
            logger.error("API request failed", exc_info=False)
            return None
        except ValueError:
            # JSONデコードエラーなど
            logger.error("Failed to parse API response", exc_info=False)
            return None
        except Exception:
            # 予期せぬその他のエラー
            logger.error("An unexpected error occurred during API call or processing", exc_info=False)
            return None
        # ---------------------------------
