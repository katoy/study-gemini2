"""AlphaZero の簡易学習スクリプト。

自己対戦とネットワーク訓練を数イテレーション実行。
学習済みモデルを保存します。
"""
import sys
from pathlib import Path

# Python パスを調整（reversi-py から実行される想定）
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from agents.networks.reversi_net import ReversiNet
from agents.gain_agent import GainAgent
from game import Game


def generate_self_play_data(n_games: int = 5) -> tuple:
    """自己対戦でデータを生成。

    Returns:
        (盤面テンソル, 戦術ターゲット, 価値ターゲット)
    """
    states = []
    values = []

    gain_agent = GainAgent()

    for game_idx in range(n_games):
        game = Game(board_size=8)
        game_states = []

        while not game.game_over:
            # 現在の盤面をテンソルに変換
            board_tensor = board_to_tensor(game.board.board, game.turn)
            game_states.append((board_tensor, game.turn))

            # GainAgent で着手
            move = gain_agent.play(game)
            if move is not None:
                game.place_stone(move[0], move[1])
            game.switch_turn()
            game.check_game_over()

        # ゲーム結果から価値を計算
        black, white = game.board.count_stones()
        game_result = 1.0 if black > white else (-1.0 if black < white else 0.0)

        # 各盤面に価値を割り当て
        for board_state, turn in game_states:
            # turn 側の価値
            value = game_result if turn == -1 else -game_result
            states.append(board_state)
            values.append(value)

    return torch.cat(states), torch.tensor(values, dtype=torch.float32)


def board_to_tensor(board: list, turn: int) -> torch.Tensor:
    """盤面をテンソルに変換。"""
    tensor = torch.zeros(1, 2, 8, 8, dtype=torch.float32)

    for r in range(8):
        for c in range(8):
            if board[r][c] == turn:
                tensor[0, 0, r, c] = 1.0
            elif board[r][c] == -turn:
                tensor[0, 1, r, c] = 1.0

    return tensor


def train_one_iteration(net: ReversiNet, optimizer: optim.Optimizer, device: str) -> None:
    """1 イテレーション訓練。"""
    print("📊 Self-play data generation...")
    board_tensors, values = generate_self_play_data(n_games=5)

    board_tensors = board_tensors.to(device)
    values = values.to(device).unsqueeze(1)

    dataset = TensorDataset(board_tensors, values)
    loader = DataLoader(dataset, batch_size=4, shuffle=True)

    net.train()
    criterion = nn.MSELoss()

    total_loss = 0.0
    for board_batch, value_batch in loader:
        optimizer.zero_grad()

        # ネットワークの出力
        _, value_pred = net(board_batch)

        # 価値損失
        loss = criterion(value_pred, value_batch)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    avg_loss = total_loss / len(loader)
    print(f"  Loss: {avg_loss:.4f}")


def main() -> None:
    """AlphaZero 簡易訓練メイン。"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🎮 AlphaZero Training (device: {device})")

    # モデル初期化
    net = ReversiNet(board_size=8, n_res_blocks=2, n_filters=32)
    net = net.to(device)

    optimizer = optim.Adam(net.parameters(), lr=1e-3)

    # 訓練ディレクトリ作成
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)

    # 簡易訓練（10 イテレーション）
    n_iterations = 10
    for iteration in range(n_iterations):
        print(f"\n🔄 Iteration {iteration + 1}/{n_iterations}")
        train_one_iteration(net, optimizer, device)

        # チェックポイント保存
        checkpoint_path = model_dir / f"alpha_zero_iter{iteration:03d}.pth"
        torch.save(net.state_dict(), checkpoint_path)
        print(f"  ✅ Saved: {checkpoint_path}")

    # 最新版を保存
    latest_path = model_dir / "alpha_zero_latest.pth"
    torch.save(net.state_dict(), latest_path)
    print(f"\n✅ Training complete! Latest model: {latest_path}")


if __name__ == "__main__":
    main()
