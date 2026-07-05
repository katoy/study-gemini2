# AlphaZero エージェントで Negamax-3K / 6K に勝率 95% 以上を達成する計画

作成日: 2026-07-05

## Context

これまで v7〜v9 の訓練で Negamax-3K / Negamax-6K（`NegamaxAgent(time_limit_ms=3000/6000)`）への勝率向上を試みてきたが、
実績は v7_dual_negamax の min 44%（50 局）、v8 の瞬間最高 min 80%（20 局・その後崩壊）、v9 は min 25% に低迷。
訓練のみでの 95% 到達は実績上遠く、コストも約 94〜97 時間 / 200 イテレーションかかる。

一方、調査で大きな未活用の伸びしろが判明した:

- 相手の Negamax は持ち時間固定（3 秒 / 6 秒）で、空きマス 12 以下は完全読み切り（`agents/negamax_agent.py`）
- AlphaZero エージェントは推論時 200 シミュレーションのみで終盤ソルバー未使用。時間制限もない

**方針（ユーザー承認済み）**: 推論時の強化（終盤完全読み切り + MCTS シミュレーション数増加）を軸にし、
足りない場合のみ 1 日以内の追加訓練で補う。

**合格判定（ユーザー承認済み）**: 共通評価モジュール `evaluate_against_negamax()`（先後交互・ペア設計）で
Negamax-3K / 6K 各 100 局、**それぞれ 95 勝以上**。

## 調査で確定した事実（設計の根拠）

- `AlphaZeroAgent.play()` は `agents/alpha_zero_agent.py:110-135`。合法手チェック（L124、`negamax_agent` の `_valid_moves` を流用済み）→ `self._mcts.run()` → 最多訪問手。
- `NegamaxAgent` の完全読み切り: `__init__(time_limit_ms, max_depth=60, endgame_empties=12, ...)`（`agents/negamax_agent.py:300-306`）、
  `play()` L341-343 で `empties <= endgame_empties` なら石差読み切りモード。終局スコア = 石差 × 10000 なので
  「勝ち > 引分 > 負け」の順序が自動成立し、評価判定 `stone_diff > 0`（`training/alphazero/evaluation.py:116`）と整合。
  時間切れ時も反復深化の best-so-far を返す anytime 設計（`_SearchTimeout`、L288, L349-365）。
- 実測評価時間（`logs/baseline_screening_v8.log`、sims=200）: 20 局 vs 3K ≈ 25 分、vs 6K ≈ 43 分。
- 候補ネットワーク: `models/alpha_zero_nega6000_v8.pth`（min 80% @20 局）と `models/alpha_zero_nega6000_v7_dual_negamax.pth`（min 44% @50 局）。

## 実装ステップ

### Step 0: 計画ドキュメントをプロジェクトに保存

本計画を `docs/superpowers/plans/2026-07-05-alphazero-95percent-plan.md` としてコピーしてコミット。

### Step 1: AlphaZeroAgent に終盤ソルバー委譲を追加

対象: `agents/alpha_zero_agent.py`

- `__init__`（L40-45）と `from_net`（L86-93）に引数追加:
  - `endgame_empties: int = 0`（0 = 無効。既存挙動を完全維持する後方互換デフォルト）
  - `endgame_time_limit_ms: int = 10000`
  - 有効時に `self._solver = NegamaxAgent(time_limit_ms=endgame_time_limit_ms, endgame_empties=endgame_empties)` を生成
- `play()`（L110-135）の合法手チェック直後に割り込み:
  - `empties <= endgame_empties` なら `self._solver.play(game)` に委譲（パス処理・時間管理はソルバー側に内蔵済み）
  - それ以外は従来どおり MCTS
- 新規クラス・新規ファイルは作らない（`server/api_server.py` の `_select_agent()` はコンストラクタ引数の違いだけで
  バリアントを構成する規約のため）。ソルバーは import 委譲（コピー・抽出はしない）。
- 閾値デフォルトは **12**（相手 Negamax 自身のデフォルトで、同じ純 Python 実装が 3〜6 秒で読み切れている実績。
  10 秒予算なら確実に完走圏）。スクリーニングで 14 も比較。

検証: 新規単体テスト（Step 2）+ 既存テスト green。

### Step 2: 単体テスト追加

対象: `tests/agents/test_alpha_zero_agent.py`（既存規約: `@pytest.mark.skipif(not TORCH_AVAILABLE, ...)`）

新クラス `TestAlphaZeroAgentEndgameSolver`:
1. `test_solver_disabled_by_default` — 引数なしで `_solver is None`（後方互換）
2. `test_endgame_uses_solver_not_mcts` — 空きマス ≤ 閾値で `NegamaxAgent.play` が呼ばれ `MCTS.run` は呼ばれない（monkeypatch）
3. `test_midgame_uses_mcts_not_solver` — 初期局面ではソルバー不使用
4. `test_endgame_solver_picks_winning_move` — 終盤局面で正着を返す（`tests/agents/test_negamax_agent.py:186-203` の局面構築パターンを流用）
5. `test_endgame_pass_returns_none` — 終盤で合法手なし → `None`
6. `test_from_net_passes_solver_options` — `from_net(..., endgame_empties=12)` でソルバー構成

### Step 3: 共通評価モジュールへのパススルー

対象: `training/alphazero/evaluation.py`

- `evaluate_against_negamax()`（L33-42）に `endgame_empties: int = 0`, `endgame_time_limit_ms: int = 10000` を追加し、
  L70 の `AlphaZeroAgent.from_net(...)` へ伝搬。
- 追随修正: `tests/training/test_evaluation.py:16` の `mock_from_net` に `**kwargs` を追加。

### Step 4: 評価スクリプトの argparse 拡張

対象: `scripts/evaluate_baseline_3k6k.py`

- `EVAL_SIMULATIONS = 200`（L41）を `--sims` に、追加で `--solver-empties`（デフォルト 0 = off）、
  `--solver-time-ms`、`--variants {3k,6k,both}`、`--seed` を追加し、`evaluate_against_negamax()` 呼び出し（L84-91）へ伝搬。
- docstring の「n_simulations=150 固定」という実装との乖離（L9）も同時に修正。

検証（スモーク）:
```bash
uv run python scripts/evaluate_baseline_3k6k.py --model models/alpha_zero_nega6000_v8.pth \
  --games 2 --sims 10 --solver-empties 12
```

### Step 5: 段階スクリーニング → 100 局最終判定

評価プロトコル厳守: 逐次実行・他の重いプロセスと同時に走らせない（CPU 負荷で Negamax の実効強さが変わる）。

- **Stage A**（~2.5 h）: {v8, v7_dual} × sims 200 × solver-empties 12、各 20 局 vs 3K/6K → ベースモデルを 1 本に絞る
- **Stage B**（~2 h、Stage A の min 勝率 < 90% のときのみ）: 勝者モデル × sims 800（必要なら solver-empties 14 も）、20〜30 局
- **最終判定**: 勝ち構成で `--games 100` を 3K・6K 各々に実行し、**各 95 勝以上**を確認
  （所要目安: sims200+solver で 3K ≈ 2.2 h / 6K ≈ 3.8 h、sims800 なら ≈ 4 h / 5.5 h）
- 20 局スクリーニングは「構成間の比較」専用（19/20 でも 95%CI 下限 ~75%）。合格判定は必ず 100 局で行う。

### Step 6: 合格構成のエージェント登録

- `server/api_server.py`: `VALID_AGENT_TYPES`（L55-60）に `"alphazero_solver"` を追加し、`_select_agent()` に分岐追加
  （既存例: `alphazero_nega6000_v9` L137-141 / `alphazero_nega6000_hybrid` L142-146 と同パターン）。
  環境変数: `ALPHAZERO_SOLVER_MODEL` / `ALPHAZERO_SOLVER_N_SIMULATIONS` / `ALPHAZERO_SOLVER_ENDGAME_EMPTIES` / `ALPHAZERO_SOLVER_TIME_LIMIT_MS`
  （デフォルトはスクリーニング勝者の構成）
- `config/agents_config.py`: `AGENT_DEFINITIONS` に id 16 を追加（既存例 L144-161）。表示名は `AlphaZero-Solver`（仮）。
  `tests/config/test_agents.py` は定義駆動なので自動カバー。
- サーバーテスト: `tests/server/test_api_server.py` に agent_type テストと env var テストを既存パターンで追加。

### Step 7（フォールバック、Step 5 で不合格の場合のみ): 1 日以内の追加訓練 v10

ベース: `scripts/train_extend_nega6000_v9.py` を `train_extend_nega6000_v10.py` にコピー
（v9 には warm-start 直後の best_score 初期化 L244-252、リプレイバッファ L259-261、min 勝率更新時のみ best 保存 L332-336 が既にある）。

変更点:
1. **訓練時評価を本番構成と一致させる**（最重要）: 評価経路に `endgame_empties=12` を渡す。
   NN の仕事を「終盤 12 マス手前までの優勢確保」に緩和し、選抜のミスマッチを解消する
2. **早期終了（patience=3）**: 直近 3 回の eval で best 更新なしなら break（v8/v9 の崩壊後の時間浪費を防ぐ）
3. warm_start をスクリーニング勝者に、保存名を v10 系に変更。lr は 5e-5 維持（崩壊するなら 2e-5）
4. 上限 `--iters 25`（1 iter ≈ 30-40 分 + eval ≈ 2.4 h × 5 回 ≈ 24 h 以内）

テスト: `tests/training/test_train_extend_nega6000_v9.py` をコピーし、patience ロジックのテストを追加。
訓練後は Step 5 の最終判定（100 局 × 2）に戻る。

## 検証（全体）

```bash
# 単体テスト・リント・型
uv run pytest tests/agents/test_alpha_zero_agent.py tests/training/test_evaluation.py \
  tests/server/test_api_server.py tests/config/test_agents.py -q
uv run ruff check . && uv run mypy agents/alpha_zero_agent.py training/alphazero/evaluation.py

# 最終判定（合格 = 各 95/100 勝以上）
uv run python scripts/evaluate_baseline_3k6k.py --model <勝者モデル> \
  --games 100 --sims <勝者sims> --solver-empties <勝者N> --seed 42
```

## リスクと対策

| リスク | 対策 |
|---|---|
| 純 Python ソルバーの時間爆発（empties=12 でも悪形は遅い） | anytime 設計で合法手は必ず返る。`endgame_time_limit_ms=10000` で上限制御。スクリーニングで 1 手最大時間をログ確認 |
| sims 800 でも 6K に届かない | ソルバーとの複合が本命。Stage A/B で on/off の寄与を分離測定。それでも不足なら Step 7 の v10 訓練 |
| 評価の統計的不確かさ（過去に 0〜100% のブレを観測） | 合格判定は必ず 100 局・`--seed` 固定。スクリーニングは比較専用 |
| CPU 負荷で Negamax の実効強さが変動 | 評価は逐次・単独実行。訓練と評価を同時に走らせない |
| 既存エージェント・テストへの回帰 | `endgame_empties=0` デフォルトで完全後方互換 |
| 訓練プロセスの silent kill（過去に頻発） | 長時間ジョブは nohup + ログ tee + 定期監視。best チェックポイントを毎 eval 保存 |

## 所要時間見積り

- 実装 + テスト（Step 1-4, 6）: 2〜3 時間
- Stage A スクリーニング: ~2.5 時間
- （必要時）Stage B: ~2 時間
- 最終判定 100 局 × 2: 6〜10 時間
- （不合格時のみ）v10 訓練: 最大 24 時間 → 再判定

## 変更対象ファイル一覧

- `agents/alpha_zero_agent.py` — ソルバー委譲（中核）
- `training/alphazero/evaluation.py` — パススルー引数
- `scripts/evaluate_baseline_3k6k.py` — argparse 拡張
- `server/api_server.py` / `config/agents_config.py` — エージェント登録
- `tests/agents/test_alpha_zero_agent.py` / `tests/training/test_evaluation.py` / `tests/server/test_api_server.py` — テスト
- （フォールバック時）`scripts/train_extend_nega6000_v10.py` / `tests/training/test_train_extend_nega6000_v10.py`
