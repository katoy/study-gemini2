# 設計書: Negamax エージェント（案 A — 純 Python・依存ゼロの強い API プレイヤー）

- 作成日: 2026-06-13
- ステータス: 設計のみ（未実装）
- 関連設計: [外部エンジン (Edax) 統合設計](./2026-06-13-edax-agent-design.md)（案 B）

## 1. 背景と動機

現在の API サーバー最強エージェントは `agents/mcts_agent.py` の `MonteCarloTreeSearchAgent` である。
既定パラメータは iterations=100、time_limit_ms=1000、UCB1 定数 C=1.41 で、ロールアウトは完全ランダム、
ノード展開ごとに `copy.deepcopy` を行うため探索効率が低く、強さの天井が低い。

本設計は、アルファベータ枝刈り付き Negamax 探索 + ヒューリスティック評価関数 + 反復深化 + 終盤完全読み切り
を備えた新エージェント `NegamaxAgent` を追加し、現 MCTS に安定して勝てる API プレイヤーを提供する。

### 現 MCTS との比較

| 観点 | NegamaxAgent（本案） | 現 MCTS | MCTS 強化案 | 外部エンジン (Edax) |
|---|---|---|---|---|
| 強さの期待値 | 高（中盤 5-7 手読み + 終盤 10-14 マス完全読み） | 低（100 反復・ランダムロールアウト） | 中（純 Python のロールアウト速度が天井） | 最強（世界トップ級） |
| 実装コスト | 中（新規 1 ファイル + 登録 + テスト） | — | 小〜中（deepcopy 排除で結局大改修） | 中〜大（バイナリ管理・プロセス統合） |
| 依存・保守性 | 純 Python・依存ゼロ | 純 Python | 純 Python | 外部バイナリ（GPL v3）依存 |
| 可変盤面 (4-16) | 対応（重みテーブルをサイズ非依存生成） | 対応 | 対応 | 8x8 専用（フォールバック必要） |
| 5 秒タイムアウト適合 | 反復深化で設計的に保証 | 適合（ただし弱い） | 適合 | 適合（起動コスト管理が必要） |
| 決定論的テスト | 容易（乱択なし・深さ固定で完全再現） | 困難（random 依存） | 困難 | 困難 |

純 Python の deepcopy ベース MCTS は 1 秒で数百プレイアウト程度しか回らない。一方 Negamax は
make/unmake 方式（後述）で 1 ノードあたりのコストを大幅に下げられ、move ordering と組み合わせた
アルファベータ枝刈りで実効分岐数を絞れるため、同じ時間予算で圧倒的に深く読める。

## 2. 仕様

### 2.1 クラスとファイル配置

- 新規ファイル: `agents/negamax_agent.py`
- クラス: `NegamaxAgent(Agent)`（`agents/base_agent.py` の `Agent` を継承）
- API での識別子: `agent_type = "negamax"`
- 既存パターン踏襲: モジュール docstring（日本語）、`TYPE_CHECKING` での `Game` インポート、
  `play(game) -> Optional[Tuple[int, int]]` シグネチャ

```python
class NegamaxAgent(Agent):
    def __init__(
        self,
        time_limit_ms: int = 3000,
        max_depth: int = 60,
        endgame_empties: int = 12,
    ) -> None: ...
```

- `time_limit_ms`: 思考時間の上限（ミリ秒）。クライアント `ApiAgent` の HTTP タイムアウト 5 秒に対し、
  HTTP 往復 + FastAPI スレッドプール + 時刻チェック粒度の余裕として 2 秒を確保した既定値 3000。
- `max_depth`: 探索深さの上限。テストで `max_depth=3, time_limit_ms=10**9` のように固定すると
  完全に決定論的な動作になる（テスト容易性の鍵）。
- `endgame_empties`: 終盤ソルバーに切り替える空きマス数の閾値。

### 2.2 内部探索: make/unmake 方式（deepcopy 排除）

MCTS が行う `Board` の `copy.deepcopy` はノードあたりのコストが大きすぎるため、
エージェント内部に軽量な探索専用ロジックを実装する。

- `play()` 冒頭で `[row[:] for row in game.get_board()]` により盤面を 1 回だけコピー。
- `_apply(board, move, turn) -> List[Tuple[int, int]]`: 着手して反転した石のリストを返す。
- `_undo(board, move, flipped, turn)`: 反転リストを使って同一リストを元に戻す。
- 探索中は単一の 2 次元リストを破壊的に使い回す（再帰の行き帰りで apply/undo が対になる）。
- 合法手生成・反転判定は `board.py` の方向走査ロジック（`_get_flipped_in_direction` 相当）と
  同等のものをモジュール内プライベート関数として実装する。`Board` クラスは変更しない。
  `game.board` の公開 API（`get_valid_moves` 等）はルート局面の合法手取得にのみ使用する。

### 2.3 評価関数

Negamax 値は常に「手番側から見たスコア」とし、符号反転は negamax の再帰で処理する。
構成要素はすべて手番差分（自分 − 相手）:

1. **位置重みテーブル**: サイズ非依存に生成（2.4 節）。
2. **mobility**: 合法手数の差。
3. **角占有**: 角の石数差 × 大きい係数。
4. **確定石（近似）**: 各角から辺に沿って連続する自色石を数える簡易安定石カウント。
   厳密な安定石判定は実装しない（角周辺だけで効果が大きい）。
5. **石差**: 終盤のみ有効。

**ゲームフェーズ判定**: `fill_ratio = 総石数 / (n * n)` で 3 段階に分ける。

| 項目 | 序盤 (< 0.33) | 中盤 (0.33–0.70) | 終盤 (> 0.70) |
|---|---|---|---|
| 位置重み | 1.0 | 1.0 | 0.3 |
| mobility | 8 | 6 | 2 |
| 角 | 25 | 30 | 30 |
| 確定石 | 10 | 15 | 20 |
| 石差 | 0 | 0 | 5 |

係数は初期値であり、`scripts/benchmark_agents.py`（5 章）での対戦結果を見て調整する。

**終局ノード**は `(自石 − 相手石) × 10000` の確定スコアとし、ヒューリスティック値と
確実に区別できる桁にする（必勝/必敗の判定がぶれない）。

### 2.4 可変盤面サイズ (4-16) 対応: 重みテーブルのサイズ非依存生成

固定 8x8 テーブルではなく、マスの「役割」から `_build_weight_table(n)` で生成する:

| 役割 | 重み | 判定方法 |
|---|---|---|
| 角 | +100 | 座標が角 |
| X マス（角の斜め隣） | -50 | 最寄り角からチェビシェフ距離 1 の対角位置 |
| C マス（角の縦横隣） | -20 | 角に隣接する辺マス |
| その他の辺 | +10 | 外周 |
| 辺の 1 つ内側 | -2 | 外周から 1 マス内側 |
| 中央部 | 0 | 上記以外 |

- 役割判定は `min(座標, n - 1 - 座標)` ベースの最寄り角距離と「辺か否か」で行い、
  どのサイズでも一貫させる。
- `functools.lru_cache`（またはモジュールレベル dict）で `n` ごとにキャッシュする。
- n=4 では X/C マスが中央初期配置と重なるが、判定が破綻しないことを単体テストで保証する
  （4, 6, 8, 16 でテーブルの 4 回回転対称をテスト）。

### 2.5 探索と時間管理

- **反復深化**: depth=1 から 1 ずつ深くする。各深さの完了ごとに最善手を確定保存する。
- **デッドライン**: `deadline = start + time_limit_ms / 1000`。negamax 内で一定ノード数
  （例: 512 ノード）ごとに時刻をチェックし、超過時は専用例外 `_SearchTimeout` を送出。
  `play()` が捕捉し、**最後に完走した深さ**の最善手を返す。
- **次深さの開始判定**: 残り時間が経過時間より少ない（= 予算の 50% を消費済み）なら
  次の深さに入らない。深さ +1 は通常 3-5 倍の時間がかかるため。
- **早期終了**: 完走した深さ ≥ 空きマス数なら完全読み切り済みとして即終了する
  （4x4 統合テストや終盤の高速化）。
- **終盤ソルバー**: 空きマス ≤ `endgame_empties`（既定 12。n > 8 の盤では計算量を考慮して
  10 に減らす等のサイズ連動も可）になったら評価関数を石差のみに切り替えて
  `depth = 空きマス数` で読み切る。同一の negamax コードを流用するため別実装は不要。
  時間切れ時は通常どおり反復深化の途中結果にフォールバックする。
- **move ordering**: 子ノードを位置重みテーブル値の降順でソート（角優先 → 枝刈り効率が大幅向上）。
  前深さの最善手を先頭に置く（簡易 PV move）。

### 2.6 パス処理

negamax 内で手番側に合法手がない場合:

- 相手にも合法手がない → 終局として確定スコアを返す。
- 相手に合法手がある → `-negamax(board, depth, -beta, -alpha, -turn, passed=True)` で
  **深さを消費せず**手番交代する。`passed` フラグで二重パスの無限再帰を防止する
  （`mcts_agent.py` の `Node.__init__` のパス処理と同じ思想）。
- `play()` 自体はルートに合法手がなければ既存エージェント同様 `None` を返す。

### 2.7 決定論

乱択を一切使わない。同点の手は探索順（位置重み降順 → row-major）で最初のものを採用する。
`max_depth` を固定し時間制限を実質無効化すれば、完全に再現可能な動作になる。

## 3. 変更ファイル一覧（実装フェーズ用）

| ファイル | 変更内容 |
|---|---|
| `agents/negamax_agent.py` | **新規**: NegamaxAgent 本体（探索・評価・重みテーブル） |
| `server/api_server.py` | import 追加（行 39-47 の try ブロック）、`VALID_AGENT_TYPES`（行 51）に `"negamax"` 追加、`_select_agent()`（行 72-82）に分岐追加。時間は `NegamaxAgent(time_limit_ms=int(os.getenv("NEGAMAX_TIME_LIMIT_MS", "3000")))` とし CI で短縮可能にする |
| `config/agents_config.py` | `AGENT_DEFINITIONS` に `{'id': 5, 'class': ApiAgent, 'display_name': 'API (Negamax)', 'params': {'api_url': 'http://127.0.0.1:5001/play', 'agent_type': 'negamax'}}` を追加 |
| `tests/agents/test_negamax_agent.py` | **新規**: 単体テスト（4 章） |
| `tests/server/test_api_server.py` | `test_play_agent_type_negamax` 追加（既存の mcts テストパターン踏襲。`NEGAMAX_TIME_LIMIT_MS` を短く設定して高速化） |
| `tests/integration/test_api_integration.py` | 全エージェント種別ループに `"negamax"` 追加。`tests/integration/conftest.py` のサーバープロセス起動に `NEGAMAX_TIME_LIMIT_MS=200` 程度の env を渡して CI を遅くしない |
| `scripts/benchmark_agents.py` | **新規**: 強さ検証スクリプト（CI 対象外、5 章） |
| `README.md` | エージェント一覧・構成図の更新 |

## 4. テスト計画（カバレッジ 100% 目標）

`tests/agents/test_negamax_agent.py` に以下を実装する:

1. **基本契約**: 合法手なし → `None` / 合法手 1 つ → 探索せず即返す / 返り値が常に合法手。
2. **戦術検証**（`max_depth` 固定 + 時間∞で決定論的）:
   - 角が取れる局面で角を選ぶ。
   - X マスに打つと次手で角を取られる局面を回避する。
3. **終盤ソルバー**: 4x4 や 6x6 で空きマス数手の局面を構築して完全読みし、石差を最大化する必勝手を選ぶ。
4. **パス処理**: 探索中に一方がパスになる局面で正しい手を返す / 二重パス（終局）の評価。
5. **時間管理**: `time_limit_ms=1` で即座に（depth 1 の結果で）合法手を返す /
   `_SearchTimeout` 経路のカバレッジ / 次深さ開始判定の分岐は `unittest.mock.patch("time.monotonic")`
   で両分岐を踏む。
6. **重みテーブル**: 4/6/8/16 サイズで生成成功、90 度回転対称、角 > 辺 > X マスの符号関係、キャッシュ動作。
7. **評価関数**: フェーズ 3 段階それぞれの係数選択分岐 / 終局スコア分岐。
8. **完全読み切り早期終了**: 空きマス数より深く完走したらループを抜ける分岐。

決定論の工夫: コンストラクタ引数で深さ・時間を完全制御、乱択なし、時刻依存分岐はモックで固定。

## 5. 強さの検証

`scripts/benchmark_agents.py`（新規・手動実行用）:

- `Game` + `NegamaxAgent` vs `MonteCarloTreeSearchAgent` をサーバーを介さず直接対戦させる。
- 先手/後手を交互に N 局（既定 20）、MCTS 側は `random.seed(i)` で再現可能にする。
- 勝敗・石差・平均思考時間を表形式で出力。`--time-limit-ms`、`--board-size`、`--games` オプションを持つ。
- **受け入れ基準**: time_limit_ms=1000 の Negamax が既定 MCTS（iterations=100, time_limit_ms=1000）に
  勝率 80% 以上。未達なら 2.3 節の係数を調整する。
- CI には含めない（`scripts/ci_check.sh` 変更なし）。実行方法と結果は docs に記録する。

## 6. 実装順序

1. `agents/negamax_agent.py`（make/unmake 探索 + 重みテーブル + 評価 + 反復深化）— TDD で
   `tests/agents/test_negamax_agent.py` と並行して進める。
2. `server/api_server.py` 登録 + `tests/server/test_api_server.py` 追加。
3. `tests/integration/test_api_integration.py` + conftest の env 設定。
4. `config/agents_config.py`（GUI 選択肢）。
5. `scripts/benchmark_agents.py` で対 MCTS 検証、係数チューニング。
6. README/docs 更新、`ruff` / `mypy` / カバレッジ確認（`scripts/ci_check.sh`）。

## 7. リスクと対策

| リスク | 対策 |
|---|---|
| 純 Python の探索速度が遅い | make/unmake で deepcopy 排除、move ordering による枝刈り効率化、時刻チェックのノード数間引き |
| 16x16 など大盤面で深く読めない | 深さ 3-4 程度に留まるが、反復深化により常に時間内で可能な最深の結果を返すため要件（5 秒以内・全サイズ動作）は満たす |
| 評価係数の初期値が不適切 | benchmark スクリプトでの対戦結果に基づき調整（受け入れ基準: 対 MCTS 勝率 80% 以上） |

## 8. 案 B（外部エンジン）との関係

本案と [Edax 統合（案 B）](./2026-06-13-edax-agent-design.md) は排他ではなく積み重ね可能:

- まず**本案（Negamax）**を実装する。依存ゼロ・全盤面サイズ対応・テスト容易で、本プロジェクトの
  制約（uv / ruff / mypy / カバレッジ 100% 目標・可変盤面）すべてに適合する。
- 最強を求める場合は案 B を追加し、Edax の非 8x8 盤面フォールバック先を本エージェントにする。
