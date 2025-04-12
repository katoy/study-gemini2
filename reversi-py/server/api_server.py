# server/api_server.py
import random
import sys
from pathlib import Path
from flask import Flask, request, jsonify

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

app = Flask(__name__)

@app.route('/play', methods=['POST'])
def play():
    """
    ゲームの盤面と手番を受け取り、ランダムな有効手を返すAPIエンドポイント。
    """
    data = request.get_json()

    # --- 入力バリデーション ---
    if not data:
        return jsonify({"error": "Invalid input: No JSON data received."}), 400
    if 'board' not in data or 'turn' not in data:
        return jsonify({"error": "Invalid input: 'board' and 'turn' are required."}), 400

    board_data = data['board']
    turn = data['turn']

    if not isinstance(board_data, list):
        return jsonify({"error": "Invalid input: 'board' must be a list."}), 400
    if not all(isinstance(row, list) for row in board_data):
        return jsonify({"error": "Invalid input: 'board' must be a list of lists."}), 400
    if turn not in [-1, 1]:
        return jsonify({"error": "Invalid input: 'turn' must be -1 or 1."}), 400

    # Board オブジェクトの作成と盤面設定
    try:
        # board_data のサイズから board_size を取得
        if not board_data or not board_data[0]: # 空のボードや空の行がないかチェック
            return jsonify({"error": "Invalid input: 'board' cannot be empty."}), 400
        board_size = len(board_data)
        if board_size == 0 or not all(len(row) == board_size for row in board_data):
            return jsonify({"error": "Invalid input: 'board' must be a square matrix."}), 400

        temp_board = Board(board_size=board_size)
        # 受け取った盤面データを Board オブジェクトに設定
        # Boardクラスの board 属性に直接代入
        if hasattr(temp_board, 'board'):
            # 値のバリデーションも行うとより堅牢 (0, 1, -1 以外がないかなど)
            temp_board.board = board_data
        else:
            # 通常ここには来ないはずだが、念のため
            print("警告: Boardクラスに 'board' 属性が見つかりません。")
            return jsonify({"error": "Internal server error: Board class structure mismatch."}), 500

    except Exception as e:
        print(f"Error creating Board object or setting state: {e}")
        # エラーの詳細をログに出力するなど検討
        return jsonify({"error": "Internal server error processing board data."}), 500

    # --- 有効な手の取得 ---
    try:
        valid_moves = temp_board.get_valid_moves(turn)
    except Exception as e:
        print(f"Error getting valid moves: {e}")
        # エラーの詳細をログに出力するなど検討
        return jsonify({"error": "Internal server error getting valid moves."}), 500

    # --- ランダムな手の選択 ---
    if valid_moves:
        selected_move = random.choice(valid_moves)
        # JSONはタプルをサポートしないため、リストに変換
        response_move = list(selected_move)
    else:
        response_move = None

    # --- レスポンス返却 ---
    return jsonify({"move": response_move})

if __name__ == "__main__":
    # debug=True は開発用です。本番環境では False にしてください。
    # host='0.0.0.0' で外部からのアクセスを許可します（必要に応じて変更）。
    # ポート番号は 5001 を使用
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
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
