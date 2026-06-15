"""AlphaZero MCTS（PUCT 探索）。

推論・学習の両方で使用する統一 MCTS 実装。
make/unmake プリミティブを使い、入力 board を破壊しない。
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

import torch

from agents.alphazero.encoding import board_to_tensor
from agents.negamax_agent import _apply, _flips_for_move, _undo, _valid_moves

if TYPE_CHECKING:
    pass

# パス着手のアクションインデックス（8*8 = 64）
PASS_ACTION: int = 64


class MCTSNode:
    """MCTS 探索ノード。

    value/Q はすべてそのノードの手番視点（自分の勝ちが +1）。
    """

    __slots__ = ("turn", "prior", "visit_count", "value_sum", "children", "is_terminal")

    def __init__(self, turn: int, prior: float) -> None:
        self.turn = turn                          # 着手するプレイヤー（絶対色 ±1）
        self.prior = prior                        # P(s, a)：親が付けた事前確率
        self.visit_count: int = 0                 # N(s, a)
        self.value_sum: float = 0.0               # ΣV（手番視点）
        self.children: dict[int, "MCTSNode"] = {}
        self.is_terminal: bool = False

    @property
    def q(self) -> float:
        """手番視点の平均価値 Q(s, a)。"""
        if self.visit_count == 0:
            return 0.0
        return self.value_sum / self.visit_count


def node_terminal_value(board: list[list[int]], turn: int) -> float:
    """終局盤面の価値を手番視点で返す（+1=勝ち, -1=負け, 0=引分）。"""
    black = sum(cell == -1 for row in board for cell in row)
    white = sum(cell == 1 for row in board for cell in row)
    diff = (black - white) if turn == -1 else (white - black)
    if diff > 0:
        return 1.0
    if diff < 0:
        return -1.0
    return 0.0


class MCTS:
    """PUCT ベースの MCTS（AlphaZero スタイル）。

    Args:
        net: OthelloNNet（forward が (policy_logits, value) を返すもの）。
        n_simulations: 1 手あたりのシミュレーション数。
        c_puct: 探索係数（大きいほど探索重視）。
        board_size: 盤面サイズ（デフォルト 8）。
        dirichlet_alpha: Dirichlet ノイズ α（学習時ルートに加える）。
        dirichlet_eps: Dirichlet ノイズ混合率（0.0 で無効）。
    """

    def __init__(
        self,
        net: object,
        n_simulations: int = 50,
        c_puct: float = 1.0,
        board_size: int = 8,
        dirichlet_alpha: float = 0.3,
        dirichlet_eps: float = 0.0,
    ) -> None:
        self._net = net
        self._n_simulations = n_simulations
        self._c_puct = c_puct
        self._board_size = board_size
        self._dirichlet_alpha = dirichlet_alpha
        self._dirichlet_eps = dirichlet_eps

    def run(self, board: list[list[int]], turn: int) -> dict[int, int]:
        """MCTS 探索を実行し、着手ごとの訪問数を返す。

        Args:
            board: 現在の盤面（破壊しない）。
            turn: 現在の手番（絶対色 ±1）。

        Returns:
            {action_idx: visit_count} の辞書。
        """
        # 作業用盤面は 1 つ（ディープコピーは最初の 1 回のみ）
        work = [row[:] for row in board]
        root = MCTSNode(turn=turn, prior=1.0)
        self._expand(root, work, turn)

        if self._dirichlet_eps > 0.0:
            self._add_dirichlet_noise(root)

        for _ in range(self._n_simulations):
            self._simulate(root, work, turn)

        return {a: c.visit_count for a, c in root.children.items()}

    def _simulate(
        self, root: MCTSNode, work: list[list[int]], root_turn: int
    ) -> None:
        """1 シミュレーション（selection → expansion → backup + unmake）。"""
        path: list[tuple[MCTSNode, int, list, int]] = []
        node, turn = root, root_turn

        # Selection: PUCT で葉まで降下
        while node.children and not node.is_terminal:
            action, child = self._select_child(node)
            if action == PASS_ACTION:
                flips: list = []
            else:
                r, c = divmod(action, self._board_size)
                flips = _flips_for_move(work, self._board_size, r, c, turn)
                _apply(work, (r, c), flips, turn)
            path.append((child, action, flips, turn))
            node, turn = child, -turn

        # Expansion / 終局評価
        if node.is_terminal:
            value = node_terminal_value(work, turn)
        else:
            value = self._expand(node, work, turn)

        leaf_turn = turn

        # Backup: 符号反転しながらルートへ伝播、unmake で盤面を巻き戻す
        for child, action, flips, mover_turn in reversed(path):
            v = value if child.turn == leaf_turn else -value
            child.visit_count += 1
            child.value_sum += v
            if action != PASS_ACTION:
                _undo(work, (divmod(action, self._board_size)), flips, mover_turn)

        root.visit_count += 1

    def _expand(self, node: MCTSNode, work: list[list[int]], turn: int) -> float:
        """葉ノードを展開してネット評価値（手番視点）を返す。"""
        moves = _valid_moves(work, self._board_size, turn)
        opponent_moves = _valid_moves(work, self._board_size, -turn)

        if not moves and not opponent_moves:
            node.is_terminal = True
            return node_terminal_value(work, turn)

        pi, v = self._evaluate(work, turn)

        if not moves:
            # パスのみ（相手に手番を渡す）
            node.children[PASS_ACTION] = MCTSNode(turn=-turn, prior=1.0)
        else:
            legal = [r * self._board_size + c for r, c in moves]
            s = sum(pi[a] for a in legal) or 1.0
            for a in legal:
                node.children[a] = MCTSNode(turn=-turn, prior=float(pi[a] / s))

        return v

    def _evaluate(self, work: list[list[int]], turn: int) -> tuple[list[float], float]:
        """ネットワークで盤面を評価し (policy 確率列, value) を返す。"""
        tensor = board_to_tensor(work, turn)
        self._net.eval()  # type: ignore[attr-defined]
        with torch.no_grad():
            logits, value = self._net(tensor)  # type: ignore[operator]
        pi = torch.softmax(logits[0], dim=0).cpu().tolist()
        v = float(value.item())
        return pi, v

    def _select_child(self, node: MCTSNode) -> tuple[int, MCTSNode]:
        """PUCT スコアが最大の子を選ぶ。"""
        sqrt_total = math.sqrt(max(node.visit_count, 1))
        best_score = float("-inf")
        best_action = -1
        best_child: Optional[MCTSNode] = None

        for action, child in node.children.items():
            u = self._c_puct * child.prior * sqrt_total / (1 + child.visit_count)
            # child.q は child 手番視点 → 親視点は符号反転
            score = -child.q + u
            if score > best_score:
                best_score = score
                best_action = action
                best_child = child

        assert best_child is not None
        return best_action, best_child

    def _add_dirichlet_noise(self, root: MCTSNode) -> None:
        """ルートの prior に Dirichlet ノイズを加える（学習時のみ）。"""
        import numpy as np
        actions = list(root.children.keys())
        if not actions:
            return
        noise = np.random.dirichlet([self._dirichlet_alpha] * len(actions))
        for action, n in zip(actions, noise):
            child = root.children[action]
            child.prior = (
                (1 - self._dirichlet_eps) * child.prior + self._dirichlet_eps * float(n)
            )
