"""マルチステージ訓練：段階的に強い相手に対応していく。

フェーズ 1: Negamax(500ms) で高勝率（95%+）を達成
フェーズ 2: Negamax(3000ms) で最終的に 90% を達成
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run_phase(phase_num: int, script_name: str, description: str) -> bool:
    """各フェーズを実行して成功を確認。"""
    print(f"\n{'='*70}")
    print(f"フェーズ {phase_num}: {description}")
    print(f"{'='*70}\n")

    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        print(f"エラー: {script_path} が見つかりません")
        return False

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode == 0


def main() -> None:
    print(f"\n{'='*70}")
    print("マルチステージ訓練開始")
    print(f"{'='*70}")

    phases = [
        (1, "train_stage1_nega500.py", "Negamax(500ms) で事前訓練"),
        (2, "train_stage2_nega3000.py", "Negamax(3000ms) で最終訓練"),
    ]

    for phase_num, script_name, description in phases:
        if not run_phase(phase_num, script_name, description):
            print(f"\nフェーズ {phase_num} が失敗しました")
            return

    print(f"\n{'='*70}")
    print("🎉 全フェーズ完了！")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
