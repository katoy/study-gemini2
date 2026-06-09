import logging
import os
import random
import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ロギング設定
logger = logging.getLogger(__name__)

# このファイルの親ディレクトリ (server) のさらに親 (プロジェクトルート) をパスに追加
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# board モジュールから Board クラスをインポート
try:
    from board import Board
except ImportError:
    logger.error("board.py が見つからないか、インポートできません。")
    logger.debug(f"プロジェクト構造を確認してください。sys.path: {sys.path}")
    sys.exit(1)

app = FastAPI()

class PlayRequest(BaseModel):
    board: List[List[int]]
    turn: int

@app.post("/play")
async def play(request: PlayRequest):
    """
    ゲームの盤面と手番を受け取り、ランダムな有効手を返すAPIエンドポイント。
    """
    try:
        data = request.model_dump()

        # --- 入力バリデーション ---
        if not data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input: No JSON data received.")
        if 'board' not in data or 'turn' not in data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input: 'board' and 'turn' are required.")

        board_data = data['board']
        turn = data['turn']

        if not isinstance(board_data, list):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input: 'board' must be a list.")
        if not all(isinstance(row, list) for row in board_data):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input: 'board' must be a list of lists.")
        if turn not in [-1, 1]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input: 'turn' must be -1 or 1.")

        # Board オブジェクトの作成と盤面設定
        try:
            # board_data のサイズから board_size を取得
            if not board_data or not board_data[0]: # 空のボードや空の行がないかチェック
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input: 'board' cannot be empty.")
            board_size = len(board_data)
            if board_size == 0 or not all(len(row) == board_size for row in board_data):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input: 'board' must be a square matrix.")
            if any(cell not in (-1, 0, 1) for row in board_data for cell in row):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input: 'board' must contain only -1, 0, or 1.")

            board = Board(board_size=board_size)
            board.board = [row[:] for row in board_data]

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating Board object or setting state: {e}", exc_info=False)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error processing board data.")

        # --- 有効な手の取得 ---
        try:
            valid_moves = board.get_valid_moves(turn)
        except Exception as e:
            logger.error(f"Error getting valid moves: {e}", exc_info=False)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error getting valid moves.")

        # --- ランダムな手の選択 ---
        if valid_moves:
            selected_move = random.choice(valid_moves)
            response_move = list(selected_move)  # Convert tuple to list for JSON serialization
        else:
            response_move = None

        # --- レスポンス返却 ---
        return JSONResponse({"move": response_move})

    except HTTPException as http_exception:
        # HTTPExceptionをそのまま返す
        raise http_exception
    except Exception as e:
        # 予期せぬエラー
        logger.error(f"Unexpected error: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")

if __name__ == "__main__":
    import uvicorn
    # ホストをセキュアにするため、デフォルトをローカルホストに設定
    # 環境変数 API_HOST で変更可能（本番環境では慎重に設定）
    # ポート番号は環境変数 API_PORT または 5001 を使用
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", "5001"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    # ロギングの基本設定
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    try:
        logger.info(f"Starting API server on {api_host}:{api_port}")
        uvicorn.run(app, host=api_host, port=api_port, log_level=log_level)
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {api_port} is already in use.")
        else:
            logger.error(f"Server startup error: {e}")
        sys.exit(1)
    except Exception:
        logger.exception("Unexpected error occurred")
        sys.exit(1)
