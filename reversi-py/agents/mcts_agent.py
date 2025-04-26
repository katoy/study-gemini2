# agents/mcts_agent.py
import random
import math
import time
import copy # ゲーム状態のコピーに使用
from .base_agent import Agent
from board import Board # Boardクラスをインポート

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
        random.shuffle(self.untried_moves) # 探索の偏りを減らすためシャッフル

    def ucb1(self, exploration_weight=1.41):
        """UCB1スコアを計算する"""
        if self.visits == 0:
            # 未訪問ノードは優先度を高くする（無限大とする）
            return float('inf')
        # UCB1 = (勝利数 / 訪問回数) + C * sqrt(log(親の総訪問回数) / 自分の訪問回数)
        # ここでの「勝利数」は、このノードからプレイアウトした結果、
        # このノードの手番プレイヤーが勝利した回数とする
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
        # result は、このノードの手番プレイヤーから見た結果 (1:勝ち, 0:負け, 0.5:引き分け)
        self.wins += result

    def is_fully_expanded(self):
        """全ての子ノードが展開済みか判定する"""
        return len(self.untried_moves) == 0

    def is_terminal_node(self):
        """ゲーム終了状態か判定する"""
        # 両プレイヤーに有効な手がない場合
        return not self.board.get_valid_moves(-1) and not self.board.get_valid_moves(1)

class MonteCarloTreeSearchAgent(Agent):
    """モンテカルロ木探索エージェント"""
    def __init__(self, iterations=100, exploration_weight=1.41, time_limit_ms=1000):
        """
        Args:
            iterations (int): シミュレーションの最大繰り返し回数.
            exploration_weight (float): UCB1の探索パラメータC.
            time_limit_ms (int): 思考時間の制限(ミリ秒). iterationsより優先される.
        """
        self.iterations = iterations
        self.exploration_weight = exploration_weight
        self.time_limit_ms = time_limit_ms

    def play(self, game):
        """MCTSを実行して最善の手を選択する"""
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None
        if len(valid_moves) == 1:
            return valid_moves[0] # 有効な手が1つなら探索不要

        # ルートノードを作成 (現在のゲーム状態をコピー)
        root_board = copy.deepcopy(game.board)
        root = Node(root_board, game.turn)

        start_time = time.time()
        elapsed_time_ms = 0
        iteration_count = 0

        # 時間制限または繰り返し回数に達するまで探索
        try:
            while elapsed_time_ms < self.time_limit_ms and iteration_count < self.iterations:
                node = self._select(root)
                if node is None: # 選択で問題発生 or 探索完了?
                    break

                winner = self._check_terminal_state(node)
                if winner is None and not node.is_terminal_node():
                    node = self._expand(node)
                    if node is None: # 展開できなかった場合 (ありえないはずだが念のため)
                        node = root # ルートに戻るか、親に戻るべきか？ 親に戻るのが自然
                        if node.parent:
                             node = node.parent

                # シミュレーション (展開されたノード or 選択された終端ノードから)
                if node: # nodeがNoneでないことを確認
                     winner = self._simulate(node)

                # バックプロパゲーション
                if node: # nodeがNoneでないことを確認
                     self._backpropagate(node, winner)

                iteration_count += 1
                elapsed_time_ms = (time.time() - start_time) * 1000
        except Exception as e:
            print(f"MCTS search interrupted by exception: {e}")

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
        return current_node # 終端ノードまたは未展開ノード

    def _expand(self, node):
        """ノードを展開する"""
        return node.expand()

    def _simulate(self, node):
        """ランダムプレイアウトを実行し、勝者を返す"""
        current_board = copy.deepcopy(node.board)
        current_turn = node.turn
        original_turn = node.turn # シミュレーション開始時の手番を記録

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

        # ゲーム終了、勝敗判定
        black_count, white_count = current_board.count_stones()
        if black_count > white_count:
            winner = -1
        elif white_count > black_count:
            winner = 1
        else:
            winner = 0

        # シミュレーション開始時のプレイヤー視点での結果を返す
        if original_turn == -1:  # Black's perspective
            if winner == -1:  # Black wins
                return 1.0
            elif winner == 1:  # White wins
                return 0.0
            else:  # Draw
                return 0.5
        elif original_turn == 1:  # White's perspective
            if winner == 1:  # White wins
                return 1.0
            elif winner == -1:  # Black wins
                return 0.0
            else:  # Draw
                return 0.5

    def _backpropagate(self, node, result):
        """結果をルートまで伝播させる"""
        current_node = node
        current_result = result
        while current_node is not None:
            # 親ノードの手番プレイヤーから見た結果に変換して更新
            # (現在のノードの手番プレイヤーが勝ったなら、親は負けたことになる)
            current_node.update(current_result)
            current_result = 1.0 - current_result # 親視点の結果に反転
            current_node = current_node.parent

    def _check_terminal_state(self, node):
        """ノードが終端状態かチェックし、勝者を返す (シミュレーション不要な場合)"""
        if node.is_terminal_node():
            black_count, white_count = node.board.count_stones()
            if black_count == white_count: return 0.5
            winner = -1 if black_count > white_count else 1
            # このノードの手番プレイヤー視点での結果を返す
            return 1.0 if winner == node.turn else 0.0
        return None # 終端状態ではない
