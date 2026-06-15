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
from .networks.othello_net import OthelloNNet
from .base_agent import Agent

if TYPE_CHECKING:
    from game import Game

# デフォルトの学習済みモデルパス
# 優先順位：alpha_zero_8x8_best.pth.tar > alpha_zero_latest.pth
DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "models" / "alpha_zero_8x8_best.pth.tar"
FALLBACK_MODEL_PATH = Path(__file__).parent.parent / "models" / "alpha_zero_latest.pth"


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
        self._net = OthelloNNet(board_size=8)
        self._net.eval()

        # モデルパスの優先順位: 指定パス → デフォルトパス → フォールバック
        model_to_load = model_path or str(DEFAULT_MODEL_PATH)

        # 学習済みモデルを読み込む
        loaded = False
        for path_to_try in [model_to_load, str(DEFAULT_MODEL_PATH), str(FALLBACK_MODEL_PATH)]:
            if not path_to_try:
                continue
            try:
                checkpoint = torch.load(str(path_to_try), map_location='cpu')
                # checkpoint が dict の場合は 'model_state' キーを試す
                if isinstance(checkpoint, dict) and 'model_state' in checkpoint:
                    self._net.load_state_dict(checkpoint['model_state'])
                elif isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
                    self._net.load_state_dict(checkpoint['state_dict'])
                else:
                    # 直接 state_dict として読み込む
                    self._net.load_state_dict(checkpoint)
                loaded = True
                break
            except Exception:
                continue

        # モデルが見つからない場合は未学習モデルで続行

    def _board_to_tensor(self, board: list[list[int]], turn: int) -> torch.Tensor:
        """盤面をテンソルに変換（OthelloNNet 形式）。

        Args:
            board: 盤面（0=空, -1=黒, 1=白）。
            turn: 手番プレイヤー（未使用、OthelloNNet は盤面状態のみを使用）。

        Returns:
            (1, 1, 8, 8) のテンソル。値は -1（黒）, 0（空）, 1（白）。
        """
        board_tensor = torch.tensor(board, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        return board_tensor

    def play(self, game: "Game") -> Optional[tuple[int, int]]:
        """与えられたゲーム状態で最善手を返す。

        ネットワークで policy を評価して、合法手の中で最高スコアの手を選択。
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
        # OthelloNNet は 65 個の出力（64 マス + パス）を返す
        policy_probs = torch.softmax(policy_logits[0], dim=0).cpu().numpy()
        best_move: Optional[tuple[int, int]] = None
        best_score: float = -1.0

        for r, c in moves:
            action_idx = r * 8 + c
            if action_idx < len(policy_probs):
                score = float(policy_probs[action_idx])
                if score > best_score:
                    best_score = score
                    best_move = (r, c)

        return best_move if best_move else random.choice(moves)
