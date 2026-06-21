# AlphaZero-N6K 継続訓練（石差最大化）設計書

**作成日**: 2026-06-22
**目的**: AlphaZero-N6K が TranspositionNegamaxAgent に対して、より大きな石差（平均 30 石以上）で勝利できるよう継続訓練する

---

## 背景

現在の `alpha_zero_nega6000.pth` は Negamax(6000ms) に対して **勝率 100%** を達成済み。しかし TranspositionNegamax(3000ms) との対決ベンチマークでは平均石差 **-21 石** にとどまっている。

「勝つこと」は学習できているが「大差をつけること」はまだ学習できていない状態。継続訓練でこれを改善する。

---

## 設計方針

### アプローチ

`train_stage2_nega6000.py` をベースに継続訓練スクリプト `train_stage3_nega6000_continue.py` を作成。
訓練ループは変更せず、`TrainConfig` のパラメータのみ調整する。

### パラメータ変更

| パラメータ | 現在値 | 新値 | 変更理由 |
|---|---|---|---|
| `warm_start` | `alpha_zero_stage1_nega500.pth` | `alpha_zero_nega6000.pth` | 最良モデルから継続（後退なし） |
| `n_simulations` | 30 | 50 | 読みを深く → より確実な大差を狙う |
| `c_puct` | 1.0 | 1.5 | 広い探索 → 局所最適（僅差勝ち）を回避 |
| `temp_moves` | 8 | 5 | 序盤の確率的手を減らし確定的大差へ |
| `games_per_iter` | 8 | 16 | 学習データ倍増 → value head 精度向上 |
| `batch_size` | 128 | 256 | データ増加に合わせてバッチも拡大 |
| `lr` | 1e-4 | 5e-5 | 継続訓練は小さい学習率で安定収束 |
| `n_iters` | 80 | 100 | より多くのイテレーションで確実に学習 |
| `best_model` | `alpha_zero_nega6000.pth` | `alpha_zero_nega6000_v2.pth` | 現在モデルを破壊しない |

### 保存先

- 新モデル: `models/alpha_zero_nega6000_v2.pth`
- ログ: `training_nega6000_v2.log`

---

## GUI への統合

訓練完了後、新モデルを GUI・API から選択できるよう登録する。

- `server/api_server.py`: `alphazero_nega6000_v2` エージェントタイプを追加
- `config/agents_config.py`: `AlphaZero-N6Kv2` を ID 12 として追加

---

## 成功基準

- `alpha_zero_nega6000_v2.pth` が生成されている
- ベンチマーク実行時、TranspositionNegamax(3000ms) に対して平均 30 石以上の差で勝利

```bash
uv run python scripts/benchmark_agents.py \
  --agent transposition \
  --opponent alphazero_n6k_v2 \
  --games 5 \
  --time-limit-ms 500
```

---

## 訓練時間の見積もり

- 1 イテレーション: 約 60〜90 分（games_per_iter=16、n_simulations=50）
- 100 イテレーション: **約 100〜150 時間**
- 目標勝率（95%）を早期に達成した場合は自動終了
