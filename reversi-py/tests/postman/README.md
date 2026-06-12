Reversi API Postman/Newman tests

目的
- server/api_server.py の POST /play に対する外形テストを Postman コレクションで記述し、Newman で実行できるようにする。

前提
- API サーバをローカルで起動しておくこと（デフォルト: 127.0.0.1:5001）。
  例: `python -m uvicorn server.api_server:app --host 127.0.0.1 --port 5001`

実行方法（推奨）
1. tests/postman ディレクトリに移動:
   cd tests/postman
2. npm を使って newman をインストール:
   npm ci
3. Newman でコレクションを実行:
   npm run newman:run

代替（npx を使う）
- npx newman run reversi-api.postman_collection.json -e reversi-api.postman_environment.json --timeout-request 20000

備考
- テストは API の契約（ステータスコード、JSON 構造、代表的な異常系）を人が読みやすい形で表現することを目的とする。
- CI 統合は今回の作業範囲外（ローカル実行のみ）。将来的に CI に組み込む場合はサーバ起動ジョブの追加が必要。
