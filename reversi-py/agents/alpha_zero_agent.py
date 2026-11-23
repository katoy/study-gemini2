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

from .alphazero.mcts import MCTS, PASS_ACTION
from .base_agent import Agent
from .negamax_agent import NegamaxAgent
from .networks.othello_net import OthelloNNet

_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from game import Game

# デフォルトの学習済みモデルパス（AlphaZero-Minimax80）
DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "models" / "alpha_zero_minimax80_best.pth"


class AlphaZeroAgent(Agent):
    """MCTS + PyTorch CNN のエージェント。

    Args:
        n_simulations: MCTS シミュレーション数。
        model_path: 学習済みモデルのパス（オプション）。
                   指定がない場合は models/alpha_zero_minimax80_best.pth を使用。
        board_size: 盤面サイズ（デフォルト 8）。
    """

    def __init__(
        self,
        n_simulations: int = 50,
        model_path: Optional[str] = None,
        board_size: int = 8,
        endgame_empties: int = 0,
        endgame_time_limit_ms: int = 10000,
    ) -> None:
        self._n_simulations = n_simulations
        self._board_size = board_size
        self._endgame_empties = endgame_empties
        self._solver: Optional[NegamaxAgent] = None
        self._net = OthelloNNet(board_size=board_size)
        self._net.eval()

        # モデルパスの優先順位: 指定パス → デフォルトパス
        model_to_load = model_path or str(DEFAULT_MODEL_PATH)

        # 学習済みモデルを読み込む
        loaded = False
        for path_to_try in [model_to_load, str(DEFAULT_MODEL_PATH)]:
            if not path_to_try:
                continue
            try:
                _logger.info(f"モデルロード試行: {path_to_try}")
                checkpoint = torch.load(str(path_to_try), map_location='cpu')
                # checkpoint が dict の場合は 'model_state' キーを試す
                if isinstance(checkpoint, dict) and 'model_state' in checkpoint:
                    self._net.load_state_dict(checkpoint['model_state'])
                elif isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
                    self._net.load_state_dict(checkpoint['state_dict'])
                else:
                    # 直接 state_dict として読み込む
                    self._net.load_state_dict(checkpoint)
                _logger.info(f"✅ モデル正常ロード: {path_to_try}")
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

        # 終盤ソルバーの初期化（endgame_empties > 0 の場合のみ）
        if endgame_empties > 0:
            self._solver = NegamaxAgent(
                time_limit_ms=endgame_time_limit_ms,
                endgame_empties=endgame_empties,
            )

    @classmethod
    def from_net(
        cls,
        net: OthelloNNet,
        n_simulations: int = 50,
        c_puct: float = 1.0,
        board_size: int = 8,
        endgame_empties: int = 0,
        endgame_time_limit_ms: int = 10000,
    ) -> "AlphaZeroAgent":
        """学習済み net オブジェクトから直接エージェントを生成（ファイルロードをスキップ）。

        arena 評価などでファイル I/O を省きたい場合に使用。
        """
        agent = cls.__new__(cls)
        agent._n_simulations = n_simulations
        agent._board_size = board_size
        agent._endgame_empties = endgame_empties
        agent._net = net
        agent._mcts = MCTS(
            net=net,
            n_simulations=n_simulations,
            c_puct=c_puct,
            board_size=board_size,
        )
        # 終盤ソルバーの初期化（endgame_empties > 0 の場合のみ）
        if endgame_empties > 0:
            agent._solver = NegamaxAgent(
                time_limit_ms=endgame_time_limit_ms,
                endgame_empties=endgame_empties,
            )
        else:
            agent._solver = None
        return agent

    def play(self, game: "Game") -> Optional[tuple[int, int]]:
        """MCTS（PUCT 探索）で最善手を選択して返す。

        終盤ソルバーが有効で、空きマス数が閾値以下の場合は委譲する。

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

        # 終盤ソルバーへの委譲
        if self._solver is not None:
            empties = sum(row.count(0) for row in board)
            if empties <= self._endgame_empties:
                return self._solver.play(game)

        # MCTS で訪問数を計算し、最大訪問数の手を選択
        counts = self._mcts.run(board, turn)
        best_action = max(counts, key=lambda a: counts[a])

        if best_action == PASS_ACTION:
            return None

        r, c = divmod(best_action, self._board_size)
        return (r, c)
