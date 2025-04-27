import random
import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# このファイルの親ディレクトリ (server) のさらに親 (プロジェクトルート) をパスに追加
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# board モジュールから Board クラスをインポート
try:
    from board import Board
except ImportError:
    print("エラー: board.py が見つからないか、インポートできません。")
    print("プロジェクト構造を確認し、必要であれば sys.path を調整してください。")
    print(f"現在の sys.path: {sys.path}")
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

            board = Board(board_size=board_size)
            board.board = board_data

        except Exception as e:
            print(f"Error creating Board object or setting state: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error processing board data.")

        # --- 有効な手の取得 ---
        try:
            valid_moves = board.get_valid_moves(turn)
        except Exception as e:
            print(f"Error getting valid moves: {e}")
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
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")

if __name__ == "__main__":
    import uvicorn
    # debug=True は開発用です。本番環境では False にしてください。
    # host='0.0.0.0' で外部からのアクセスを許可します（必要に応じて変更）。
    # ポート番号は 5001 を使用
    try:
        uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"エラー: ポート 5001 は既に使用中です。")
            print("他のプロセスがポートを使用していないか確認するか、別のポートを指定してください。")
        else:
            print(f"サーバー起動エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        sys.exit(1)
