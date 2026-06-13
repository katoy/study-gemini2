# 設計書: 外部エンジン (Edax) 統合エージェント（案 B — 最強クラスの API プレイヤー）

- 作成日: 2026-06-13
- ステータス: 設計のみ（未実装）
- 関連設計: [Negamax エージェント設計](./2026-06-13-negamax-agent-design.md)（案 A）

## 1. 背景と動機

現在の API サーバー最強エージェントは `agents/mcts_agent.py` の `MonteCarloTreeSearchAgent`
（iterations=100、time_limit_ms=1000、完全ランダムロールアウト）であり、強さの天井が低い。

本設計は、世界最強クラスのオープンソースリバーシエンジン **Edax** を外部プロセスとして統合し、
`agent_type = "edax"` で利用できる API プレイヤーを追加する。純 Python 実装では到達できない
強さ（bitboard + 完全読み切り + 学習済み評価関数）を提供する。

## 2. エンジン選定

### 第一候補: Edax 4.x (abulmo/edax-reversi)

| 項目 | 内容 |
|---|---|
| 強さ | 世界最強クラス。bitboard + 終盤完全読み切り + 学習済み評価関数（要 `eval.dat` 約 80MB） |
| 配布形態 | GitHub Releases のバイナリは古いため**ソースビルド推奨**。C 言語 + 単一 Makefile で依存なし、ビルドは数十秒。macOS arm64: `make build ARCH=arm64-modern COMP=clang OS=osx` / Linux CI: `make build ARCH=x86-64-v2 COMP=gcc OS=linux` |
| 評価データ | `data/eval.dat` をリリースアセット（`eval.7z`）から別途取得。エンジンは実行ディレクトリ基準の相対パスで探すため、`cwd` をエンジン配置ディレクトリにして起動する |
| ライセンス | GPL v3。**リポジトリに同梱しない**（3.5 節） |
| プロトコル | 起動オプションなしのコンソールモード。`setboard <64 文字 + 手番>`、`go`（出力 `Edax plays f5`）、`level <n>`、`move-time <s>`、`quit` |
| 制約 | **8x8 専用**。本プロジェクトの可変盤面 (4-16) はフォールバックで吸収する（3.4 節） |

### 代替候補（参考）

- **Egaroucid**: Edax を超える強さ。C++20 でビルドがやや重いが、Edax 互換プロトコルモードがあるため
  本設計の `EDAX_PATH` 差し替えで将来利用可能な構造にしておく。
- **Zebra/WZebra**: メンテナンス停止・ビルド困難のため不採用。
- **自前 Negamax（純 Python）**: 「最強クラス」ではないが移植性最高。
  [案 A](./2026-06-13-negamax-agent-design.md) として別設計。

## 3. アーキテクチャ

### 3.1 プロセス統合方式: 常駐 subprocess + ロック（採用）

| 方式 | 評価 |
|---|---|
| 1 手ごとに起動 | 実装単純・リークなし。ただし起動ごとに `eval.dat`（約 80MB）のロードで 0.5-2 秒を消費し、クライアント `ApiAgent` の 5 秒タイムアウト予算を圧迫する。**不採用** |
| **常駐（採用）** | 初回リクエストで lazy 起動し stdin/stdout パイプで対話。2 手目以降は思考時間のみ |

常駐プロセスの設計（`EdaxEngine` クラス）:

- **起動**: lazy singleton。初回 `play` 時に
  `subprocess.Popen([edax_path, "-q"], stdin=PIPE, stdout=PIPE, stderr=DEVNULL, cwd=engine_dir, text=True, encoding="utf-8", errors="replace")`。
  起動直後にバナー/プロンプトを読み捨て、`level N` / `move-time T` を送信する。
- **直列化**: `POST /play` は同期 `def` で FastAPI のスレッドプールから並行に呼ばれうる
  （`server/api_server.py` 行 85-92 の注記参照）。エンジンは 1 局面ずつしか扱えないため、
  `threading.Lock` で `get_move()` 全体を直列化する。
- **クラッシュ回復**: コマンド送信前に `proc.poll() is not None` なら破棄して再起動（1 回だけリトライ）。
  `BrokenPipeError` / 読み取り EOF も同様に再起動してリトライ。リトライも失敗なら例外 → API は 503。
- **応答待ちタイムアウト**: stdout の読み取りはブロッキングのため、補助スレッドで readline して
  `queue.Queue` に積み、`Queue.get(timeout=EDAX_TIMEOUT)` で待つ。タイムアウト時はプロセスの状態が
  不定なので `kill()` して再起動する。
- **終了処理**: `atexit` で `quit` 送信 → `terminate()` → `wait(2s)` → `kill()`。
  テスト用に `shutdown()` メソッドを公開する（冪等）。

### 3.2 盤面の受け渡し

- **board → setboard 文字列**: 行 0 から行優先で 64 文字を連結。マッピングは
  `-1`（黒）→ `X` / `1`（白）→ `O` / `0` → `-`。末尾に手番 1 文字（黒 = `X`、白 = `O`）。
  - 注意: 内部表現と Edax の X/O 対応は実装時に統合テストで検証する（逆であれば定数 1 つで反転できる構造にする）。
- **着手の座標変換**（純粋関数として独立させ、個別にテスト）:
  - `coord_to_rowcol("f5") -> (4, 5)`: `col = ord(c[0]) - ord('a')`、`row = int(c[1]) - 1`
  - 逆変換 `rowcol_to_coord` もデバッグログ用に用意する。
- **応答パース**: `go` 後の出力から正規表現 `r"plays\s+([A-Ha-h][1-8]|PS|pass)"`（大文字小文字無視）で抽出。
  pass / `PS` は `None` を返す（API の `{"move": null}` 既存仕様に合致）。
- **整合性ガード**: パース結果が `game.board.get_valid_moves(turn)` に含まれることを検証する。
  含まれなければエンジン異常（`EdaxProtocolError`）として扱う。

### 3.3 クラス設計（2 ファイル分離でテスト容易性を確保）

**`agents/edax_engine.py`** — プロセス管理専任（`Agent` 非依存、subprocess を直接モック可能）:

```python
class EdaxProtocolError(Exception): ...
class EdaxNotAvailableError(Exception): ...

class EdaxEngine:
    def __init__(self, edax_path, level, move_time, timeout,
                 popen=subprocess.Popen) -> None: ...
        # popen を注入可能にして単体テストでフェイクに差し替える
    def is_available(self) -> bool: ...        # パス存在 + 実行権限のみ（起動しない）
    def _ensure_started(self) -> None: ...     # lazy 起動 + 初期化コマンド送信
    def _restart(self) -> None: ...
    def get_move(self, board_str: str, turn_char: str) -> Optional[str]: ...
        # with lock: setboard → go → パース。失敗時は 1 回だけ再起動リトライ
    def shutdown(self) -> None: ...

# モジュール関数（純粋・個別テスト可能）
def board_to_edax(board, turn) -> str: ...
def coord_to_rowcol(coord) -> Tuple[int, int]: ...
def rowcol_to_coord(row, col) -> str: ...
```

**`agents/edax_agent.py`** — `Agent` 実装（薄いアダプタ）:

```python
class EdaxAgent(Agent):
    def __init__(self, engine: Optional[EdaxEngine] = None,
                 fallback: Optional[Agent] = None) -> None: ...
        # engine 未指定なら共有シングルトンを取得
        # fallback 未指定なら MCTS（案 A 実装後は NegamaxAgent）
    def play(self, game) -> Optional[Tuple[int, int]]: ...
        # 8x8 以外 → fallback.play(game)
        # エンジン不可用 → EdaxNotAvailableError（API 層が 503 に変換）
        # 不正な着手 → EdaxProtocolError（API 層が 500 に変換）
```

**`server/api_server.py`** の変更:

- `VALID_AGENT_TYPES`（行 51）に `"edax"` を追加、`_select_agent()`（行 72-82）に分岐を追加
  （`EdaxAgent` はシングルトン engine を共有するため毎回 new で問題ない）。
- `play()` のエージェント実行 try ブロックで `EdaxNotAvailableError` を捕捉し
  503 Service Unavailable を返す分岐を追加する。

### 3.4 8x8 以外の盤面: 内部フォールバック（採用）

**採用: エージェント内で代替エージェントにフォールバックする。**

- GUI 側 `ApiAgent.play()` は HTTP エラー時に `None` を返す実装
  （`agents/api_agent.py` 行 111-128）のため、400 を返すと「パス」と誤解釈されゲームが壊れる。
- ユーザー体験としても「edax 選択時も 10x10 で遊べる」方が一貫する。
- 実装: `_select_agent` ではなく `EdaxAgent.play()` 内で `game.get_board_size() != 8` なら
  フォールバックエージェントに委譲し、レスポンスは正常 200。サーバーログに WARNING を出す。
- フォールバック先: 実装時点で `NegamaxAgent`（案 A）が存在すればそれを既定とし、
  なければ `MonteCarloTreeSearchAgent`。

（400 を返す案は API の純粋性では勝るが、クライアント改修が必要になるため不採用。）

### 3.5 設定と運用

環境変数（`server/api_server.py` の既存 `os.getenv` パターンに合わせる）:

| 変数 | デフォルト | 意味 |
|---|---|---|
| `EDAX_PATH` | `""`（未設定） | エンジンバイナリの絶対パス。未設定/実行不可なら edax 無効 |
| `EDAX_LEVEL` | `12` | 思考レベル（探索深さ）。5 秒予算内で安全な値 |
| `EDAX_MOVE_TIME` | `3.5` | 1 手の最大思考秒数（クライアント 5 秒 − HTTP/起動マージン） |
| `EDAX_TIMEOUT` | `4.0` | サーバー側の応答待ち打ち切り秒数 |

- **バイナリ未導入時**: `agent_type=edax` のリクエストに **503 Service Unavailable**
  （detail: "edax engine is not available"）。判定は `EdaxEngine.is_available()`。
  GUI は `None` → パス扱いになるが、設定ミスはサーバーログで気付ける。
- **GPL v3 の扱い**: Edax のバイナリ・ソースとも本リポジトリに**同梱しない**。
  外部プロセスとして起動する限り、本体コードへの GPL 伝播はない（プロセス境界での利用）。
  `scripts/setup_edax.sh`（クローン → ビルド → `eval.dat` 配置 → `EDAX_PATH` の案内表示）で
  各自導入する。成果物は `out/edax/` 等の gitignore 配下に置く。
- **GUI 登録**: `config/agents_config.py` の `AGENT_DEFINITIONS` に
  `{'id': <次番号>, 'class': ApiAgent, 'display_name': 'API (Edax)', 'params': {'api_url': 'http://127.0.0.1:5001/play', 'agent_type': 'edax'}}` を追加。
- **Docker**: `Dockerfile` をマルチステージ化。builder ステージで `git clone` + `make` +
  `eval.dat` 取得、最終ステージへ `/opt/edax/{bin/edax,data/eval.dat}` をコピーし
  `ENV EDAX_PATH=/opt/edax/bin/edax`。GPL バイナリのイメージ同梱は可（配布時はイメージの
  ラベル/README にライセンス表記を記載する）。
- **warmup（任意）**: 初回リクエストのみ起動コスト（1-2 秒）が乗るため、サーバー起動時に
  `is_available()` が真なら lazy 起動を先行実行する startup フックを推奨する。

## 4. テスト計画

- **`tests/agents/test_edax_engine.py`**（単体・バイナリ不要）:
  - `board_to_edax` / `coord_to_rowcol` / `rowcol_to_coord` の純粋関数テスト
    （初期盤面、各色、pass）。
  - `popen` 注入のフェイクプロセス（スクリプト化した stdout）で: 正常応答、クラッシュ → 再起動リトライ、
    タイムアウト → kill、`is_available` の各分岐、`shutdown` の冪等性。
- **`tests/agents/test_edax_agent.py`**: engine をモック注入。正常着手、pass → `None`、
  非 8x8 → fallback 呼び出し検証、不正座標 → 例外。
- **`tests/server/test_api_server.py` 追加分**: TestClient + `monkeypatch` で `EdaxEngine` をモック。
  edax 正常 200、未導入 503、非 8x8 でフォールバック 200。
- **`tests/integration/test_edax_integration.py`**:
  `pytest.mark.skipif(not os.getenv("EDAX_PATH") or not os.path.exists(...), reason="edax binary not installed")`。
  実バイナリで初期局面の `/play` を叩き、合法手が返ることのみ確認（1-2 ケース、レベル低めで高速化）。
- **CI への影響最小化**: CI では `EDAX_PATH` 未設定のまま → 統合テストは skip、単体は全部走る。
  カバレッジ目標は popen 注入モックで担保できる（実バイナリ不要で全分岐に到達可能）。
  任意で「Edax ビルド + 統合テスト」を別ジョブ（continue-on-error または手動トリガ）として後日追加する。

## 5. リスクと対策

| リスク | 対策 |
|---|---|
| プロセスリーク | `atexit` + `shutdown()`。uvicorn reload 時は lazy 再起動で自然回復。テストでは fixture で shutdown を強制 |
| 5 秒以内に応答できない | `EDAX_MOVE_TIME=3.5` + `EDAX_TIMEOUT=4.0` の二重ガード。タイムアウト時は kill → 再起動して 500（次手で回復）。初回起動コストは startup warmup で回避 |
| 文字化け・プロトコル差異 | `encoding="utf-8", errors="replace"` + 正規表現パース + 合法手検証で防御。Egaroucid 等への将来差し替えも正規表現が吸収する |
| 並行リクエスト競合 | `threading.Lock` で直列化。ロック保持時間は `EDAX_TIMEOUT` が上限 |
| `eval.dat` 不在で弱い/起動失敗 | setup スクリプトで必ず配置。`is_available` はパスのみ判定し、初回 `go` 失敗で 503 に落ちる。起動バナーに warning があればログ出力 |
| GPL ライセンス | バイナリ・ソースとも本リポジトリに含めない（スクリプトで取得）。Docker イメージ同梱時はライセンス表記 |

## 6. 変更ファイル一覧と実装順序

| 順 | ファイル | 変更 |
|---|---|---|
| 1 | `agents/edax_engine.py` | **新規**: EdaxEngine + 変換関数 + 例外 |
| 2 | `tests/agents/test_edax_engine.py` | **新規**: 単体テスト（モック） |
| 3 | `agents/edax_agent.py` | **新規**: EdaxAgent（フォールバック含む） |
| 4 | `tests/agents/test_edax_agent.py` | **新規**: 単体テスト |
| 5 | `server/api_server.py` | `VALID_AGENT_TYPES` / `_select_agent` / 503 ハンドリング / （任意）startup warmup |
| 6 | `tests/server/test_api_server.py` | edax 分岐テスト追加 |
| 7 | `config/agents_config.py` | 'API (Edax)' 追加 |
| 8 | `scripts/setup_edax.sh` | **新規**: ビルド・`eval.dat` 導入スクリプト |
| 9 | `tests/integration/test_edax_integration.py` | **新規**: skipif 付き実バイナリテスト |
| 10 | `Dockerfile` / `README.md` | マルチステージで Edax 組込み、導入手順・環境変数の文書化 |

ステップ 1-2 → 3-4 → 5-6 が依存連鎖で、7-10 は並行可能。各新規ファイルは既存スタイル
（型注釈 + 日本語 docstring、ruff / mypy 準拠）に従う。

## 7. 案 A（Negamax）との関係

本案と [Negamax エージェント（案 A）](./2026-06-13-negamax-agent-design.md) は排他ではなく積み重ね可能:

- まず**案 A（Negamax）**を実装する。依存ゼロ・全盤面サイズ対応・テスト容易。
- 最強を求める場合に**本案（Edax）**を追加し、非 8x8 盤面のフォールバック先を
  `NegamaxAgent` にすることで、全盤面サイズで一貫して強い構成になる。
