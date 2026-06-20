#!/usr/bin/env python3
"""訓練進捗のリアルタイム監視スクリプト。

モデルファイルのタイムスタンプと出力から進捗を追跡します。
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def monitor_training():
    """訓練プロセスを監視して進捗を表示。"""
    print("\n" + "=" * 70)
    print("AlphaZero フェーズ 2 訓練監視開始")
    print("=" * 70 + "\n")

    model_path = Path("models/alpha_zero_nega3000.pth")
    start_time = datetime.now()
    initial_mtime = model_path.stat().st_mtime if model_path.exists() else None

    try:
        # 訓練プロセスを開始
        process = subprocess.Popen(
            [sys.executable, "scripts/train_stage2_nega3000.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        current_iter = 0
        best_win_rate = 0.0

        # 出力をリアルタイムで表示
        for line in process.stdout:
            print(line, end="", flush=True)

            # イテレーション番号を追跡
            if "イテレーション" in line and "/" in line:
                try:
                    parts = line.split("イテレーション")[1].split("/")
                    current = int(parts[0].strip())
                    current_iter = current
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    print(f"  ⏱ 経過時間: {elapsed:.1f} 分", file=sys.stderr)
                except (ValueError, IndexError):
                    pass

            # 勝率を追跡
            if "vs Negamax" in line and "%" in line:
                try:
                    rate_str = line.split("%")[0].split(":")[-1].strip()
                    rate = float(rate_str)
                    if rate > best_win_rate:
                        best_win_rate = rate
                        print(f"  🏆 最高勝率更新: {rate:.1f}%", file=sys.stderr)
                except (ValueError, IndexError):
                    pass

            # モデル保存を追跡
            if "✅ モデル保存" in line:
                current_mtime = model_path.stat().st_mtime if model_path.exists() else None
                if current_mtime and (initial_mtime is None or current_mtime > initial_mtime):
                    print("  💾 モデルチェックポイント保存完了", file=sys.stderr)
                    initial_mtime = current_mtime

            # 目標達成を検出
            if "目標達成" in line:
                print("\n🎉 訓練完了！\n", file=sys.stderr)
                break

        # プロセスの終了コードを確認
        return_code = process.wait()

        total_time = (datetime.now() - start_time).total_seconds() / 60
        print("\n" + "=" * 70)
        print("訓練終了")
        print(f"  総実行時間: {total_time:.1f} 分")
        print(f"  最終イテレーション: {current_iter}")
        print(f"  最高勝率: {best_win_rate:.1f}%")
        print(f"  終了コード: {return_code}")
        print("=" * 70 + "\n")

        return return_code == 0

    except KeyboardInterrupt:
        print("\n\n⚠️  訓練が中断されました")
        return False
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False


if __name__ == "__main__":
    success = monitor_training()
    sys.exit(0 if success else 1)
