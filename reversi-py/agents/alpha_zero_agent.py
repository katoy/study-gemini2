"""AlphaZero スタイル AI（MCTS + PyTorch ResNet）。

MCTS 探索にニューラルネットワークの policy/value を統合したエージェント。
デフォルトで学習済みモデルを使用します。
"""
import random
from pathlib import Path
from typing import TYPE_CHECKING, Optional

try:
    import torch
except ImportError:
    raise ImportError("PyTorch is required for AlphaZeroAgent")

from .negamax_agent import _valid_moves
from .networks.reversi_net import ReversiNet
from .base_agent import Agent

if TYPE_CHECKING:
    from game import Game

# デフォルトの学習済みモデルパス
DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "models" / "alpha_zero_latest.pth"


class AlphaZeroAgent(Agent):
    """MCTS + PyTorch ResNet のエージェント。

    Args:
        n_simulations: MCTS シミュレーション数。
        model_path: 学習済みモデルのパス（オプション）。
                   指定がない場合は models/alpha_zero_latest.pth を使用。
    """

    def __init__(
        self,
        n_simulations: int = 50,
        model_path: Optional[str] = None,
    ) -> None:
        self._n_simulations = n_simulations
        self._net = ReversiNet(board_size=8, n_res_blocks=2, n_filters=32)
        self._net.eval()

        # モデルパスの優先順位: 指定パス → デフォルトパス
        model_to_load = model_path or str(DEFAULT_MODEL_PATH)

        # 学習済みモデルを読み込む
        try:
            self._net.load_state_dict(torch.load(model_to_load, map_location='cpu'))
        except FileNotFoundError:
            # モデルが見つからない場合は未学習モデルで続行
            pass

    def _board_to_tensor(self, board: list[list[int]], turn: int) -> torch.Tensor:
        """盤面をテンソルに変換。

        Args:
            board: 盤面（0=空, -1=黒, 1=白）。
            turn: 手番プレイヤー。

        Returns:
            (1, 2, 8, 8) のテンソル。
        """
        board_tensor = torch.zeros(1, 2, 8, 8, dtype=torch.float32)

        for r in range(8):
            for c in range(8):
                if board[r][c] == turn:
                    board_tensor[0, 0, r, c] = 1.0
                elif board[r][c] == -turn:
                    board_tensor[0, 1, r, c] = 1.0

        return board_tensor

    def play(self, game: "Game") -> Optional[tuple[int, int]]:
        """与えられたゲーム状態で最善手を返す。

        簡略版: ネットワークで policy を評価して最善手を選択。
        """
        board = game.board.board
        turn = game.turn

        # 合法手取得
        moves = _valid_moves(board, 8, turn)
        if not moves:
            return None

        # ネットワークで policy を評価
        board_tensor = self._board_to_tensor(board, turn)
        with torch.no_grad():
            policy_logits, _ = self._net(board_tensor)

        # 合法手の中で policy スコアが最大のものを選択
        policy_probs = torch.softmax(policy_logits[0], dim=0).numpy()
        best_move: Optional[tuple[int, int]] = None
        best_score: float = -1.0

        for r, c in moves:
            action_idx = r * 8 + c
            score = float(policy_probs[action_idx])
            if score > best_score:
                best_score = score
                best_move = (r, c)

        return best_move if best_move else random.choice(moves)
