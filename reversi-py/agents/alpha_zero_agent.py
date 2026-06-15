"""AlphaZero スタイル AI（MCTS + PyTorch CNN）。

PUCT 探索（MCTS）にニューラルネットワークの policy/value を統合したエージェント。
デフォルトで学習済みモデルを使用します。
"""
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

try:
    import torch
except ImportError:
    raise ImportError("PyTorch is required for AlphaZeroAgent")

_logger = logging.getLogger(__name__)

from .alphazero.mcts import MCTS, PASS_ACTION
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

        self._mcts = MCTS(
            net=self._net,
            n_simulations=n_simulations,
            board_size=board_size,
        )

    @classmethod
    def from_net(
        cls,
        net: OthelloNNet,
        n_simulations: int = 50,
        c_puct: float = 1.0,
        board_size: int = 8,
    ) -> "AlphaZeroAgent":
        """学習済み net オブジェクトから直接エージェントを生成（ファイルロードをスキップ）。

        arena 評価などでファイル I/O を省きたい場合に使用。
        """
        agent = cls.__new__(cls)
        agent._n_simulations = n_simulations
        agent._board_size = board_size
        agent._net = net
        agent._mcts = MCTS(
            net=net,
            n_simulations=n_simulations,
            c_puct=c_puct,
            board_size=board_size,
        )
        return agent

    def play(self, game: "Game") -> Optional[tuple[int, int]]:
        """MCTS（PUCT 探索）で最善手を選択して返す。

        Args:
            game: 現在のゲーム状態。

        Returns:
            最善手 (row, col)。合法手がない場合は None。
        """
        board = game.board.board
        turn = game.turn

        # 合法手なし → パス
        from .negamax_agent import _valid_moves
        if not _valid_moves(board, self._board_size, turn):
            return None

        # MCTS で訪問数を計算し、最大訪問数の手を選択
        counts = self._mcts.run(board, turn)
        best_action = max(counts, key=lambda a: counts[a])

        if best_action == PASS_ACTION:
            return None

        r, c = divmod(best_action, self._board_size)
        return (r, c)
