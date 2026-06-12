# ゲーム途中でのエージェント切り替え対応

## Summary
- FastAPI の `/play` を拡張し、`agent_type` で着手戦略を切り替えられるようにする。
- GUI はゲーム途中でも黒/白それぞれのプレイヤー種別を変更できるようにする。
- 非同期 AI の遅延応答が、切り替え後の状態に誤って適用されないようにする。

## API Design

### Request
`POST /play` の body に以下を追加する。

- `board`: 既存どおり 2 次元配列
- `turn`: 既存どおり `-1` または `1`
- `agent_type`: 戦略指定用の文字列

想定値:

- `first`
- `random`
- `gain`
- `mcts`

### Response
既存どおり `{"move": [row, col]}` または `{"move": null}` を返す。

### Validation
- `agent_type` が未知なら 400 を返す。
- `board` と `turn` の既存バリデーションは維持する。
- `agent_type` ごとの実装は API サーバー内で分岐し、盤面検証と着手候補取得は共通化する。

### Routing Policy
- `first`: 合法手の先頭を返す。
- `random`: 合法手からランダムに返す。
- `gain`: ひっくり返せる数が最大の手を返す。
- `mcts`: MCTS で得た手を返す。

## Implementation Changes

### `server/api_server.py`
- `PlayRequest` に `agent_type: str` を追加する。
- 既存の `Board` 組み立てと `turn` バリデーションを再利用する。
- `agent_type` に応じた戦略選択を関数分割する。
- 戦略選択の失敗や予期しない例外は既存方針どおり 500 にする。
- `move` が存在しない場合の互換性は維持する。

### `agents/api_agent.py`
- `__init__` に `agent_type` を追加する。`api_url` は既存どおり必須、`agent_type` は既定値を持たせる。
- `play()` の payload に `agent_type` を含める。
- レスポンス解釈は既存のまま維持する。
- `agent_type` を変更する用途に備えて、インスタンス生成後でも設定を差し替えやすい構造にする。

### `config/agents_config.py`
- `API (Random)` の定義を、`agent_type='random'` を持つ `ApiAgent` として明示する。
- 将来の追加候補として `API (First)` などを増やせる形にする。
- GUI のラジオ選択は `display_name` をそのまま使う。

### `main.py`
- ゲーム開始後でもプレイヤー選択 UI を操作可能にする。
- 黒/白の設定変更時に `game.set_players(...)` を再実行して即時反映する。
- 設定変更で `AI -> 人間` に変わった場合、進行中の AI スレッド結果を無効化する。
- 設定変更で `人間 -> AI` に変わった場合、次の手番から新しいエージェントで思考を開始する。
- 遅延応答対策として、AI 思考開始時の世代 ID を持ち、応答受領時に一致しない結果は破棄する。

### State / Concurrency Policy
- 切り替えは盤面を保持したまま行う。
- `history`、`history_index`、`turn`、`game_over` は原則維持する。
- AI 思考中に設定が変わった場合、古い思考結果は「無効」とみなす。
- 可能なら `is_ai_thinking` に加えて、思考開始時のスナップショット識別子を導入する。

## Test Plan

### API tests
- `agent_type=random` で `/play` が合法手の中からランダムな手を返すことを確認する。
- `agent_type=first` で先頭手を返すことを確認する。
- `agent_type=gain` で最大フリップ数の手を返すことを確認する。
- `agent_type=mcts` で MCTS の戻り値を返すことを確認する。
- 不正な `agent_type` で 400 を返すことを確認する。
- `board` / `turn` の既存の異常系が壊れていないことを確認する。

### CI / Postman
- GitHub Actions に Postman/Newman を追加済み（`postman-newman.yml`）。
- 追加: npm / pip のキャッシュ（actions/cache）を導入してビルド時間を短縮。
- 追加: Newman の JUnit レポートを `tests/postman/newman-results.xml` に出力し、CI 実行時にアーティファクトとして保存する。
- ローカル実行: `cd reversi-py && API_HOST=127.0.0.1 API_PORT=5001 python -m uvicorn server.api_server:app --host 127.0.0.1 --port 5001` でサーバ起動後、`cd reversi-py/tests/postman && npx newman run reversi-api.postman_collection.fixed.json -e reversi-api.postman_environment.json --timeout-request 20000 --reporters cli,junit --reporter-junit-export newman-results.xml` を実行して確認可能。

### `ApiAgent` tests
- `requests.post` の JSON body に `agent_type` が含まれることを確認する。
- `agent_type` が設定どおりに送信されることを確認する。
- サーバーが `move: null` を返した場合の互換性を確認する。
- タイムアウト、接続失敗、HTTP error、JSON error の既存挙動を維持する。
- `agent_type` を差し替えたとき、次回送信に反映されることを確認する。

### GUI / game flow tests
- ゲーム開始前だけでなく、ゲーム途中でも黒/白のエージェント選択を変更できることを確認する。
- 黒のみ変更、白のみ変更、両方変更の各ケースで、次の AI 手番に新しい設定が使われることを確認する。
- 人間 -> AI への切り替え後、次の手番から AI が動くことを確認する。
- AI -> 人間 への切り替え後、AI の遅延結果が盤面へ反映されないことを確認する。
- `restart` / `reset` / `undo` / `pass` が切り替え後も壊れないことを確認する。

### Regression tests
- 人間対人間、人間対AI、AI対AI の基本対局を通す。
- 既存のログや履歴の挙動が変わらないことを確認する。
- テストで非同期処理が絡む箇所は、スレッド完了待ちやモックで安定化する。

## Assumptions
- FastAPI の設計は `単一 /play + agent_type` に固定する。
- ゲーム途中の切り替えは黒/白ともに許可する。
- 切り替えは「次の手番」ではなく、設定変更後の次回判定から有効にする。
- API 戦略はまず既存の内部エージェントに対応する `first / random / gain / mcts` に限定する。
- 既存の `ApiAgent` は外部サービスを 1 回叩くクライアントとして維持し、複雑なローカル戦略は持たせない。
