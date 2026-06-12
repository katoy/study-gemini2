# agents/mcts_agent.py
import copy  # ゲーム状態のコピーに使用
import logging
import math
import random
import time
from typing import Optional, Tuple, TYPE_CHECKING

from .base_agent import Agent

if TYPE_CHECKING:
    from game import Game

logger = logging.getLogger(__name__)

class Node:
    """モンテカルロ木探索のノード"""
    def __init__(self, board, turn, parent=None, move=None):
        self.board = board # Boardオブジェクトのコピー
        self.turn = turn   # このノードの手番プレイヤー
        self.parent = parent
        self.move = move # このノードに至った手 (row, col)
        self.children = []
        self.wins = 0
        self.visits = 0
        # このノードの状態で有効な手を取得（展開用）
        self.untried_moves = self.board.get_valid_moves(self.turn)
        if not self.untried_moves:
            # 手番プレイヤーに合法手がない（パス）場合、相手に手番を渡して
            # 探索を継続できるようにする。両者とも合法手がなければ終端ノード。
            opponent_moves = self.board.get_valid_moves(-self.turn)
            if opponent_moves:
                self.turn = -self.turn
                self.untried_moves = opponent_moves
        random.shuffle(self.untried_moves) # 探索の偏りを減らすためシャッフル

    def ucb1(self, exploration_weight=1.41):
        """UCB1スコアを計算する"""
        if self.visits == 0:
            # 未訪問ノードは優先度を高くする（無限大とする）
            return float('inf')
        # UCB1 = (勝利数 / 訪問回数) + C * sqrt(log(親の総訪問回数) / 自分の訪問回数)
        # ここでの「勝利数」は、このノードへの着手を選んだプレイヤー（親ノードの
        # 手番プレイヤー）が勝利した回数とする。親は自分が勝ちやすい子を選ぶため、
        # この視点で保持することで select_child の最大化が正しくなる
        return (self.wins / self.visits) + exploration_weight * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )

    def select_child(self, exploration_weight=1.41):
        """UCB1スコアが最も高い子ノードを選択する"""
        best_score = -1
        best_child = None
        for child in self.children:
            score = child.ucb1(exploration_weight)
            if score > best_score:
                best_score = score
                best_child = child
        return best_child

    def expand(self):
        """未試行の手から一つ選び、新しい子ノードを生成して返す"""
        if not self.untried_moves:
            return None # 展開できる手がない

        move = self.untried_moves.pop()
        new_board = copy.deepcopy(self.board)
        new_board.place_stone(move[0], move[1], self.turn)
        next_turn = -self.turn
        child_node = Node(new_board, next_turn, parent=self, move=move)
        self.children.append(child_node)
        return child_node

    def update(self, result):
        """訪問回数と勝利数を更新する"""
        self.visits += 1
        # result は、このノードへの着手を選んだプレイヤー（親ノードの手番）から
        # 見た結果 (1:勝ち, 0:負け, 0.5:引き分け)
        self.wins += result

    def is_fully_expanded(self):
        """全ての子ノードが展開済みか判定する"""
        return len(self.untried_moves) == 0

    def is_terminal_node(self):
        """ゲーム終了状態か判定する"""
        # 両プレイヤーに有効な手がない場合
        return not self.board.get_valid_moves(-1) and not self.board.get_valid_moves(1)

class MonteCarloTreeSearchAgent(Agent):
    """モンテカルロ木探索エージェント."""

    def __init__(self, iterations: int = 100, exploration_weight: float = 1.41, time_limit_ms: int = 1000) -> None:
        """Monte Carlo Tree Search エージェントを初期化します。

        Args:
            iterations: シミュレーションの最大繰り返し回数。
            exploration_weight: UCB1 の探索パラメータ（C）。
            time_limit_ms: 思考時間の制限（ミリ秒）。iterations より優先されます。
        """
        self.iterations = iterations
        self.exploration_weight = exploration_weight
        self.time_limit_ms = time_limit_ms

    def play(self, game: 'Game') -> Optional[Tuple[int, int]]:
        """MCTS を実行して最善の手を選択します。

        Args:
            game: 現在のゲーム状態。

        Returns:
            (row, col) のタプル、または合法手がない場合は None。
        """
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None
        if len(valid_moves) == 1:
            return valid_moves[0] # 有効な手が1つなら探索不要

        # ルートノードを作成 (現在のゲーム状態をコピー)
        root_board = copy.deepcopy(game.board)
        root = Node(root_board, game.turn)

        start_time = time.time()
        elapsed_time_ms = 0.0
        iteration_count = 0

        # 時間制限または繰り返し回数に達するまで探索
        try:
            while elapsed_time_ms < self.time_limit_ms and iteration_count < self.iterations:
                node = self._select(root)
                if node is None: # 選択で問題発生 or 探索完了?
                    break

                # 終端ノードでなければ展開してからプレイアウトする
                winner = self._check_terminal_state(node)
                if winner is None:
                    expanded = self._expand(node)
                    if expanded is not None:
                        node = expanded
                    winner = self._simulate(node)

                # バックプロパゲーション
                self._backpropagate(node, winner)

                iteration_count += 1
                elapsed_time_ms = (time.time() - start_time) * 1000
        except Exception:
            # 探索途中の例外は致命的ではないため、ログに記録してそれまでの
            # 探索結果から着手を選ぶ（例外は握りつぶさず必ず記録する）
            logger.exception("MCTS search interrupted by exception")

        # 探索終了後、最も訪問回数が多い手を選択
        best_move = None
        max_visits = -1
        # print(f"--- MCTS ({game.turn}) Iterations: {iteration_count}, Time: {elapsed_time_ms:.2f} ms ---")
        for child in root.children:
            # print(f"Move: {child.move}, Wins: {child.wins}, Visits: {child.visits}, UCB1: {child.ucb1()}")
            if child.visits > max_visits:
                max_visits = child.visits
                best_move = child.move

        # print(f"Selected Move: {best_move}")
        return best_move if best_move is not None else random.choice(valid_moves) # フォールバック

    def _select(self, node):
        """ルートから葉ノードまでUCB1で選択"""
        current_node = node
        while not current_node.is_terminal_node():
            if not current_node.is_fully_expanded():
                # 未展開の手があれば、そのノードを選択対象とする
                return current_node
            else:
                # 全て展開済みなら、UCB1スコア最大の子供を選択
                current_node = current_node.select_child(self.exploration_weight)
                if current_node is None: # 子がいない場合 (終端ノードだった?)
                    return node # 元のノードを返す (あるいはNone?) -> 親を返すのが適切か
        return current_node  # pragma: no cover

    def _expand(self, node):
        """ノードを展開する"""
        return node.expand()

    def _simulate(self, node):
        """ランダムプレイアウトを実行し、勝者 (-1: 黒, 1: 白, 0: 引き分け) を返す"""
        current_board = copy.deepcopy(node.board)
        current_turn = node.turn

        while True:
            valid_moves = current_board.get_valid_moves(current_turn)
            if not valid_moves:
                # パス
                current_turn *= -1
                valid_moves = current_board.get_valid_moves(current_turn)
                if not valid_moves:
                    # 両者パス -> ゲーム終了
                    break
            # ランダムに手を選択
            move = random.choice(valid_moves)
            current_board.place_stone(move[0], move[1], current_turn)
            current_turn *= -1

        # ゲーム終了、勝敗判定（絶対的な勝者を返す）
        black_count, white_count = current_board.count_stones()
        if black_count > white_count:
            return -1
        elif white_count > black_count:
            return 1
        return 0

    def _backpropagate(self, node, winner):
        """勝者 (-1/1/0) をルートまで伝播させる。

        各ノードの wins は「そのノードへの着手を選んだプレイヤー（親ノードの
        手番）」視点で記録する。パスにより手番が連続するノードがあっても、
        絶対的な勝者から各ノードごとに視点を計算するため正しく更新できる。
        """
        current_node = node
        while current_node is not None:
            # 視点プレイヤー: 親の手番（ルートは自身の手番。値は選択に使われない）
            perspective = (
                current_node.parent.turn if current_node.parent is not None
                else current_node.turn
            )
            if winner == 0:
                result = 0.5
            else:
                result = 1.0 if winner == perspective else 0.0
            current_node.update(result)
            current_node = current_node.parent

    def _check_terminal_state(self, node):
        """ノードが終端状態かチェックし、勝者 (-1/1/0) を返す。終端でなければ None。"""
        if node.is_terminal_node():
            black_count, white_count = node.board.count_stones()
            if black_count == white_count:
                return 0
            return -1 if black_count > white_count else 1
        return None # 終端状態ではない
