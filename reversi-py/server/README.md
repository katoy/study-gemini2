# Reversi API (リバーシ API)

このプロジェクトは、FastAPI を使用して構築されたリバーシ (オセロ) の API です。

## 概要

この API は、リバーシの盤面と手番を受け取り、ランダムな有効手を返します。

## エンドポイント

- `POST /play`: ゲームの盤面と手番を受け取り、有効手を返します。

## 使い方

1.  リクエストボディの例:

```json
{
  "board": [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, -1, 0, 0, 0],
    [0, 0, 0, -1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0]
  ],
  "turn": 1
}
```

2.  レスポンスの例:

```json
{
  "move": [3, 2]
}
```

## 依存関係

-   FastAPI
-   uvicorn
-   pydantic

## インストール

```bash
pip install fastapi uvicorn pydantic
```

## 実行方法

```bash
python3 api_server.py
```

## テスト

テストを実行するには、次のコマンドを実行します。

```bash
python3 -m pytest
```

カバレッジレポートを作成するには、次のコマンドを実行します。

```bash
python3 -m pytest --cov=.
```

## API ドキュメント

API ドキュメントは、Swagger UI で表示できます。サーバーを起動後、ブラウザで http://localhost:5001/docs にアクセスしてください。

OpenAPI 仕様 (JSON 形式) は、http://localhost:5001/openapi.json から取得できます。

## ライセンス

このプロジェクトは MIT ライセンスの下で提供されています。詳細については、[LICENSE](LICENSE) ファイルを参照してください。
