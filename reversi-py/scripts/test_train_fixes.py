"""修正内容をテストするための短い訓練スクリプト（3 イテレーションのみ）"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from agents.networks.othello_net import OthelloNNet
from agents.gain_agent import GainAgent
from agents.negamax_agent import NegamaxAgent
from agents.alpha_zero_agent import AlphaZeroAgent
from game import Game


def board_to_tensor(board: list, turn: int) -> torch.Tensor:
    """盤面をテンソルに変換（プレイヤーの視点）。"""
    board_array = []
    for row in board:
        board_row = []
        for cell in row:
            if cell == 0:
                board_row.append(0)
            elif cell == turn:
                board_row.append(1)
            else:
                board_row.append(-1)
        board_array.append(board_row)

    tensor = torch.tensor(board_array, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
    return tensor


def generate_self_play_data(n_games: int = 20) -> tuple:
    """自己対戦データ生成（GainAgent vs GainAgent）"""
    board_tensors = []
    values = []

    gain_agent = GainAgent()

    for game_idx in range(n_games):
        game = Game(board_size=8)
        game_states = []

        while not game.game_over:
            board_tensor = board_to_tensor(game.board.board, game.turn)
            game_states.append((board_tensor, game.turn))

            move = gain_agent.play(game)
            if move:
                game.place_stone(move[0], move[1])

            game.switch_turn()
            game.check_game_over()

        black, white = game.board.count_stones()
        game_result = 1.0 if black > white else (-1.0 if black < white else 0.0)

        for board_state, turn in game_states:
            value = game_result if turn == -1 else -game_result
            board_tensors.append(board_state)
            values.append(value)

        if (game_idx + 1) % 10 == 0:
            print(f"    生成: {game_idx + 1}/{n_games}")

    return torch.cat(board_tensors), torch.tensor(values, dtype=torch.float32)


def test_vs_negamax(n_games: int = 3) -> float:
    """Negamax に対してテスト（3 ゲームのみ）。"""
    print(f"\n  ゲームテスト（{n_games} ゲーム）")

    alphazero = AlphaZeroAgent(n_simulations=50)
    negamax = NegamaxAgent(time_limit_ms=100)

    wins = 0

    for game_num in range(n_games):
        game = Game(board_size=8)

        while not game.game_over:
            if game.turn == 1:
                move = alphazero.play(game)
            else:
                move = negamax.play(game)

            if move:
                game.place_stone(move[0], move[1])

            game.switch_turn()
            game.check_game_over()

        black, white = game.board.count_stones()
        if white > black:
            wins += 1
            print(f"    G{game_num + 1}: {black:2d}-{white:2d} OK")
        else:
            print(f"    G{game_num + 1}: {black:2d}-{white:2d} NG")

    win_rate = wins / n_games
    print(f"\n  勝率: {win_rate*100:.1f}% ({wins}/{n_games})")
    return win_rate


def main() -> None:
    """修正テスト（3 イテレーション）"""
    device = "cpu"
    print(f"\n{'='*70}")
    print(f"修正テスト: BatchNorm エラー解決確認")
    print(f"{'='*70}")
    print(f"目標: イテレーション 3 を完了できるか確認\n")

    net = OthelloNNet(board_size=8)
    net = net.to(device)

    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)

    checkpoint_path = model_dir / "alpha_zero_8x8_best.pth.tar"
    if checkpoint_path.exists():
        print(f"既存モデルをロード: {checkpoint_path.name}\n")
        checkpoint = torch.load(str(checkpoint_path), map_location=device)
        net.load_state_dict(checkpoint['state_dict'])

    optimizer = optim.Adam(net.parameters(), lr=1e-4)

    best_win_rate = 0.6
    max_iterations = 3

    for iteration in range(max_iterations):
        print(f"\n{'='*70}")
        print(f"イテレーション {iteration + 1}/{max_iterations}")
        print(f"{'='*70}")

        print(f"\n  データ生成中...")
        board_tensors, values = generate_self_play_data(n_games=20)

        board_tensors = board_tensors.to(device)
        values = values.to(device).unsqueeze(1)

        dataset = TensorDataset(board_tensors, values)
        batch_size = 64
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=True)

        print(f"  データセットサイズ: {len(dataset)}, バッチ数: {len(loader)}")

        net.eval()
        criterion = nn.MSELoss()
        total_loss = 0.0

        for board_batch, value_batch in loader:
            optimizer.zero_grad()
            _, value_pred = net(board_batch)
            loss = criterion(value_pred, value_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(loader) if len(loader) > 0 else 0.0
        print(f"  訓練完了 - Loss: {avg_loss:.6f}")

        win_rate = test_vs_negamax(n_games=3)

        if win_rate > best_win_rate:
            best_win_rate = win_rate
            model_path = model_dir / f"test_best_{iteration:03d}.pth"
            torch.save(net.state_dict(), str(model_path))
            print(f"ベストモデル更新: {model_path.name}")

    print(f"\n{'='*70}")
    print(f"テスト完了！BatchNorm エラーなく実行成功")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
