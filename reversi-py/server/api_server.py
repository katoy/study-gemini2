import logging
import os
import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

"""FastAPI ベースのリバーシ AI サーバー。

GUI アプリから ApiAgent 経由で REST API で着手を取得する。
複数のローカル AI エージェント実装を提供。

アーキテクチャ：
    GUI (main.py)
    └→ ApiAgent
        └→ HTTP POST http://localhost:5001/play
            └→ api_server.py (_select_agent で着手を計算)
                └→ ローカルエージェント (FirstAgent, RandomAgent など)

REST API：
    POST /play
        Request: board (List[List[int]]), turn (int), agent_type (str)
        Response: {move: [row, col]} or error

設計：
- PlayRequest (Pydantic): リクエスト検証
- _select_agent: agent_type → エージェントインスタンス → 着手
"""

logger = logging.getLogger(__name__)

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))  # pragma: no cover

try:
    from game import Game
    from agents.first_agent import FirstAgent
    from agents.random_agent import RandomAgent
    from agents.gain_agent import GainAgent
    from agents.mcts_agent import MonteCarloTreeSearchAgent
    from agents.negamax_agent import NegamaxAgent
except ImportError as e:  # pragma: no cover
    logger.error(f"必要なモジュールのインポートに失敗しました: {e}")
    sys.exit(1)

app = FastAPI()

VALID_AGENT_TYPES = frozenset({"first", "random", "gain", "mcts", "negamax"})

# 盤面サイズの許容範囲。巨大盤面による CPU/メモリ枯渇（DoS）を防ぐ
MIN_BOARD_SIZE = 4
MAX_BOARD_SIZE = 16


class PlayRequest(BaseModel):
    board: List[List[int]]
    turn: int
    agent_type: str = "random"


def _create_game(board_data: List[List[int]], turn: int) -> Game:
    """ボードデータと手番から一時的な Game オブジェクトを生成する。"""
    game = Game(board_size=len(board_data))
    game.board.board = [row[:] for row in board_data]
    game.turn = turn
    return game


def _select_agent(agent_type: str):
    """agent_type 文字列に対応するエージェントインスタンスを返す。"""
    if agent_type == "first":
        return FirstAgent()
    if agent_type == "random":
        return RandomAgent()
    if agent_type == "gain":
        return GainAgent()
    if agent_type == "mcts":
        return MonteCarloTreeSearchAgent()
    if agent_type == "negamax":
        return NegamaxAgent(
            time_limit_ms=int(os.getenv("NEGAMAX_TIME_LIMIT_MS", "3000"))
        )
    return None


@app.post("/play")
def play(request: PlayRequest) -> JSONResponse:
    """
    ゲームの盤面・手番・エージェント種別を受け取り、選択された戦略で着手を返すAPIエンドポイント。

    注記: CPU バウンドな探索（MCTS など）でイベントループをブロックしないよう、
    あえて同期関数 (def) として定義し、FastAPI のスレッドプールで実行させる。
    """
    try:
        data = request.model_dump()

        board_data = data['board']
        turn = data['turn']
        agent_type = data.get('agent_type', 'random')

        if turn not in [-1, 1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input: 'turn' must be -1 or 1."
            )
        if agent_type not in VALID_AGENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid input: 'agent_type' must be one of "
                    f"{sorted(VALID_AGENT_TYPES)}."
                )
            )

        try:
            if not board_data or not board_data[0]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: 'board' cannot be empty."
                )
            board_size = len(board_data)
            if not (MIN_BOARD_SIZE <= board_size <= MAX_BOARD_SIZE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Invalid input: 'board' size must be between "
                        f"{MIN_BOARD_SIZE} and {MAX_BOARD_SIZE}."
                    )
                )
            if not all(len(row) == board_size for row in board_data):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: 'board' must be a square matrix."
                )
            if any(cell not in (-1, 0, 1) for row in board_data for cell in row):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: 'board' must contain only -1, 0, or 1."
                )
            game = _create_game(board_data, turn)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"ボードオブジェクト生成エラー: {e}", exc_info=False)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error processing board data."
            )

        try:
            agent = _select_agent(agent_type)
            move = agent.play(game)
        except Exception as e:
            logger.error(f"エージェント実行エラー: {e}", exc_info=False)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error getting move."
            )

        response_move = list(move) if move is not None else None
        return JSONResponse({"move": response_move})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"予期しないエラー: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error."
        )


if __name__ == "__main__":
    import uvicorn
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", "5001"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    try:
        logger.info(f"API サーバーを {api_host}:{api_port} で起動します")
        uvicorn.run(app, host=api_host, port=api_port, log_level=log_level)
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"ポート {api_port} は既に使用中です。")
        else:
            logger.error(f"サーバー起動エラー: {e}")
        sys.exit(1)
    except Exception:
        logger.exception("予期しないエラーが発生しました")
        sys.exit(1)
