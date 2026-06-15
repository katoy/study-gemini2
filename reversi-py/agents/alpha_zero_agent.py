"""AlphaZero スタイル AI（MCTS + PyTorch CNN）。

MCTS 探索にニューラルネットワークの policy/value を統合したエージェント。
デフォルトで学習済みモデルを使用します。
"""
import logging
import random
from pathlib import Path
from typing import TYPE_CHECKING, Optional

try:
    import torch
except ImportError:
    raise ImportError("PyTorch is required for AlphaZeroAgent")

_logger = logging.getLogger(__name__)

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
    """MCTS + PyTorch CNN のエージェント。

    Args:
        n_simulations: MCTS シミュレーション数。
        model_path: 学習済みモデルのパス（オプション）。
                   指定がない場合は models/alpha_zero_8x8_best.pth.tar を使用。
        board_size: 盤面サイズ（デフォルト 8）。
    """

    def __init__(
        self,
        n_simulations: int = 50,
        model_path: Optional[str] = None,
        board_size: int = 8,
    ) -> None:
        self._n_simulations = n_simulations
        self._board_size = board_size
        self._net = OthelloNNet(board_size=board_size)
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
            except (FileNotFoundError, RuntimeError, EOFError, OSError, KeyError) as e:
                _logger.warning("モデルロード失敗: %s (%s)", path_to_try, e)
                continue

        if not loaded:
            _logger.warning("全モデルのロードに失敗。未学習モデルで続行します。")

    def _board_to_tensor(self, board: list[list[int]], turn: int) -> torch.Tensor:
        """盤面をテンソルに変換（OthelloNNet 形式・現在プレイヤーの視点）。

        alpha-zero-general の OthelloNNet は、現在のプレイヤーの視点で盤面を見るように訓練されています。
        つまり、現在のプレイヤーの石を +1、相手の石を -1 として表現します。

        Args:
            board: 盤面（0=空, -1=黒, 1=白）。
            turn: 手番プレイヤー（-1=黒, 1=白）。

        Returns:
            (1, 1, 8, 8) のテンソル。値は -1（相手）, 0（空）, 1（現在プレイヤー）。
        """
        # 現在プレイヤーの視点に盤面を変換
        board_array = []
        for row in board:
            board_row = []
            for cell in row:
                if cell == 0:
                    board_row.append(0)  # 空
                elif cell == turn:
                    board_row.append(1)  # 現在プレイヤーの石
                else:
                    board_row.append(-1)  # 相手の石
            board_array.append(board_row)

        board_tensor = torch.tensor(board_array, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        return board_tensor

    def play(self, game: "Game") -> Optional[tuple[int, int]]:
        """与えられたゲーム状態で最善手を返す。

        ネットワークで policy を評価して、合法手の中で最高スコアの手を選択。
        """
        board = game.board.board
        turn = game.turn

        # 合法手取得
        moves = _valid_moves(board, self._board_size, turn)
        if not moves:
            return None

        # ネットワークで policy を評価
        board_tensor = self._board_to_tensor(board, turn)
        with torch.no_grad():
            policy_logits, _ = self._net(board_tensor)

        # 合法手の中で policy スコアが最大のものを選択
        # OthelloNNet は board_size^2 + 1 個の出力（各マス + パス）を返す
        policy_probs = torch.softmax(policy_logits[0], dim=0).cpu().numpy()
        best_move: Optional[tuple[int, int]] = None
        best_score: float = -1.0

        for r, c in moves:
            action_idx = r * self._board_size + c
            if action_idx < len(policy_probs):
                score = float(policy_probs[action_idx])
                if score > best_score:
                    best_score = score
                    best_move = (r, c)

        return best_move if best_move else random.choice(moves)
