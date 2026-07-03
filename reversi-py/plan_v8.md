# AlphaZero-N6K v9 訓練計画 — Negamax-3K/6K 勝率 95% 達成

## Context

**目標:** AlphaZero エージェントが Negamax-3000ms・Negamax-6000ms の両方に対して勝率 95% 以上（合格判定: MCTS **n_simulations=200**、開口ランダム化つき 50 ゲーム評価）。

**経緯:** v2〜v8 の 7 バージョンにわたる自己対戦訓練が目標未達。v8 は loss 5.2〜6.2 で横ばい、IT10 評価で 3K 2% / 6K 20%（gap 93%）。

**今回の調査で確定した根本原因（3 つ）:**

1. **リプレイバッファなし** (`scripts/train_extend_nega6000_v8.py:286`) — 毎イテレーション `buffer = []` にリセット。約 720 サンプル・batch_size=256・`drop_last=True` で **1 イテレーションあたり勾配更新わずか 2 回**。約 7 分の自己対戦に対し学習がほぼ進まない。loss 横ばいの直接原因。
2. **評価対局の多様性欠如** (`train_extend_nega6000_v8.py:147-185`) — 先手/後手交代のみで開口ランダム化なし。AlphaZero（argmax）も Negamax もほぼ決定的なため、50 ゲームが数種類の棋譜の繰り返しになり勝率が信頼できない。過去の「0%↔100%」の揺れ、「3K に 2% なのに 6K に 50%」という強さ逆転はこの測定不良で説明がつく。**歴代の評価結果はすべて信頼できない**ため、真のベースラインの再測定が必要。
3. **`best_score` が再起動で 0.0 にリセット** (`train_extend_nega6000_v8.py:278`) — 再開のたびに最初の評価が無条件で best モデルを上書き。

**戦略:** ゲート付き段階戦略。①測定を修正 → ②真のベースラインを確定 → ③結果に応じて自己対戦修正版（Route A）か蒸留ハイブリッド（Route B）に分岐。

---

## Phase 0: 現状停止と整理（10 分）

- [ ] `pgrep -fl "train_extend"` で実行中の訓練プロセスを確認し、あれば停止（直近確認では停止済みの可能性が高い）
- [ ] `training_nega6000_v8_continued.log` を `logs/` などにアーカイブ（または命名を変えて退避）
- [ ] この計画（plan_v8.md）をコミット

## Phase 1: 共通評価モジュールの作成（最重要・約 1 時間）

**新規:** `training/alphazero/evaluation.py` ＋ `tests/training/test_evaluation.py`

評価ロジックを訓練スクリプトから分離した共通モジュールにする（「評価が訓練用パラメータを流用していた」過去のバグの再発防止）。既存の `training/alphazero/`（checkpoint.py, losses.py）のパターンに従う。

主要 API:

```python
def evaluate_against_negamax(
    net, *, n_games, time_limit_ms, n_simulations=200,
    opening_random_plies=4, seed=None, board_size=8,
) -> EvalResult:  # win_rate, mean_stone_diff, per-game 記録
```

- **開口ランダム化:** 各ペアの冒頭 `opening_random_plies` 手（既定 4 手）を合法手から一様ランダムに選択
- **ペア設計:** 同一開口で先手/後手を入れ替えた 2 ゲームを 1 ペアとして実施（50 ゲーム = 25 開口 × 2 色）。分散を大幅に削減
- 勝率に加えて平均石差も返す（95% 到達前の進捗が石差で見える）
- テスト: 開口が異なるペアで棋譜が異なること、色入れ替えの正しさ、勝率計算（軽量にするため Negamax はモック or time_limit_ms を極小化）
- `ruff check` / `mypy` 通過を確認

## Phase 2: 真のベースライン確定 ✅ 完了

**修正:** `scripts/evaluate_baseline_3k6k.py` を Phase 1 のモジュール使用に更新 ✅

- [x] 候補モデルを 4 つに絞る：alpha_zero_nega6000.pth / v6_improved_loss / v7_dual_negamax / v8
- [x] **スクリーニング実行完了** (2026-07-03 06:40～13:24)：ログは `logs/baseline_screening.log`

### スクリーニング結果

| モデル | 3K勝率 | 6K勝率 | **min** | 備考 |
|--------|--------|--------|---------|------|
| v0（無印） | 45% | 40% | 40% | ❌ |
| v6_improved_loss | 30% | 65% | 30% | ❌ |
| **v7_dual_negamax** | **60%** | **40%** | **40%** | 🥇 最良 |
| v8 | 55% | 20% | 20% | ❌ |

**ゲート G1 判定:** 最良モデル = v7_dual_negamax、min 勝率 B = 40%
- B = 40% < 60% → **🔀 Route B（蒸留ハイブリッド）を選択**

## Phase 3-A: v9 自己対戦訓練スクリプト（Route A の場合）

**新規:** `scripts/train_extend_nega6000_v9.py`（v8 ベース）＋ `tests/training/test_train_extend_nega6000_v9.py`（v7 用テストのパターンに従う）

v8 からの変更点:

| 項目 | v8 | v9 | 理由 |
|---|---|---|---|
| リプレイバッファ | なし（毎回破棄） | **直近 10 イテレーション分を保持**（deque、約 7,000 サンプル） | 学習信号を 50 倍以上に |
| エポック | 1 周（2 ステップ） | バッファ全体を **4 エポック** | 同上 |
| warm_start | v8_latest（劣化系譜） | **Phase 2 の最良モデル** | 劣化した系譜を捨てる |
| lr | 1e-4 | **5e-5** | 良いモデルからの fine-tune |
| games_per_iter | 12 | 16 | データ量確保 |
| 評価 | 内蔵関数・sims=150・開口固定 | **共通モジュール・sims=200・開口ランダム 30 ゲーム**（15 開口 × 2 色）・5 イテレーションごと | 合格判定と同条件 |
| best_score 初期値 | 0.0 固定 | **訓練開始時に warm_start モデルを 1 回評価して設定** | 上書きバグ修正 |
| その他 | — | temp_moves=6, c_puct=1.5, batch=256 は据え置き | 変更点を絞る |

- 早期終了: 両勝率 ≥ 95%
- `ruff` / `mypy` / テスト通過後にコミットし、nohup でバックグラウンド起動（**単一プロセス厳守**。過去に多重起動でリソース競合の事故あり）

**ゲート G2（訓練中の撤退基準）:** 4 回連続の評価（20 イテレーション）で min 勝率がベースライン B から改善しなければ停止し、Route B へ切替。

## Phase 3-B: 蒸留ハイブリッド（Route B - ゲート発動） ✅ 準備完了

**新規:** `scripts/train_distillation_hybrid_v7.py`

v7 モデル（min勝率 40%）から Negamax-6K 教師による蒸留訓練で 60% 達成を目指す。

### 実装内容

- ✅ 教師 = Negamax-6K（固定）
- ✅ warm_start = v7 モデル（alpha_zero_nega6000_v7_dual_negamax.pth）
- ✅ 共通評価モジュール使用（デュアル評価：3K・6K）
- ✅ min 勝率 ≥ 60% 達成で自動終了・最良モデル保存
- ✅ ゲート達成時に「Route B → Phase 3-A に接続可能」メッセージ出力

### 実行手順

```bash
nohup uv run python scripts/train_distillation_hybrid_v7.py > training_hybrid_v7.log 2>&1 &
```

**目標:** min(3K, 6K) ≥ 60% → Phase 3-A へ接続

## Phase 4: 最終検証とエージェント登録

- [ ] **最終判定:** 最良モデルを 50 ゲーム × {3K, 6K}、sims=200、開口ランダム化で測定 → **両方 ≥ 95% で合格**
- [ ] モデル登録（`docs/superpowers/plans/2026-06-22-alphazero-n6k-continue-training.md` の Task 3/4 と同じパターン）:
  - `server/api_server.py`: `VALID_AGENT_TYPES` と `_select_agent` に `alphazero_nega6000_v9` を追加
  - `config/agents_config.py`: `AGENT_DEFINITIONS` に表示名を追加
  - `scripts/benchmark_agents.py`: `--opponent` 選択肢に追加
- [ ] 全体検証: `uv run pytest --ignore=tests/integration -q`、`ruff check`、`mypy . --ignore-missing-imports`
- [ ] コミット

## 検証方法

- **各フェーズ:** 変更ファイルの `ruff` / `mypy` / 対応する pytest を通す
- **評価モジュール:** `uv run pytest tests/training/test_evaluation.py -q`
- **訓練監視:** `tail -f training_nega6000_v9.log` ＋ 5 イテレーションごとの評価値（勝率と平均石差）で判断。既存の check スクリプト類のパターンを流用
- **最終成功基準:** sims=200・開口ランダム化・50 ゲームで 3K ≥ 95% かつ 6K ≥ 95%

## リスクと備え

- **95%（特に 6K）が現ネット容量で到達不能な可能性** — ゲート G2 で早期に検知し Route B へ。それでも頭打ちなら、実測データつきで報告し、sims 増（400）やネット拡張を提案する（黙って回し続けない）
- **評価の所要時間**（6K 戦は 1 ゲーム約 4 分）— 評価は 5 イテレーションごと・30 ゲームに抑え、最終判定のみ 50 ゲーム
- **測定中の CPU 負荷汚染** — 評価中は訓練・他の重いプロセスを止める（`evaluate_baseline_3k6k.py` のプロトコル注記に準拠）
