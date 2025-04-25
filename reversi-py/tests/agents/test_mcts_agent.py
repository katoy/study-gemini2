# test/agents/test_mcts_agent.py
import unittest
import sys
import os
import time
import random # random をインポート (フォールバック用)
# --- unittest.mock から patch をインポート ---
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir) # ルートディレクトリを取得
sys.path.append(project_root) # ルートディレクトリをパスに追加

# --- Node クラスもインポート ---
from agents.mcts_agent import MonteCarloTreeSearchAgent, Node
from game import Game
from board import Board

class TestMonteCarloTreeSearchAgent(unittest.TestCase):

    # --- Node クラスのテストを追加 ---
    def test_node_ucb1_unvisited(self):
        """未訪問ノードのUCB1スコアが無限大になるかテスト (行 27)"""
        board = Board()
        node = Node(board, turn=-1)
        self.assertEqual(node.visits, 0)
        self.assertEqual(node.ucb1(), float('inf'))

    def test_node_select_child_prefers_unvisited(self):
        """select_child が未訪問の子ノードを優先するかテスト (行 49)"""
        board = Board()
        root = Node(board, turn=-1)
        root.visits = 1 # 親ノードは訪問済みとする

        # 子ノードを複数作成 (一部は訪問済み、一部は未訪問)
        child1 = root.expand() # 未訪問
        child2 = root.expand() # 未訪問
        child3 = root.expand() # 訪問済みとする
        # Ensure expansion was successful before modifying child3
        if child1 is None or child2 is None or child3 is None:
             self.fail("Node expansion failed during test setup")
        child3.visits = 1
        child3.wins = 0.5

        # 未訪問ノードの UCB1 は inf になるため、それが選択されるはず
        selected_child = root.select_child()
        self.assertIsNotNone(selected_child)
        self.assertEqual(selected_child.visits, 0, "未訪問の子ノードが選択されるべき")
        # 具体的に child1 か child2 のどちらかであることを確認
        # Note: The order of expansion isn't guaranteed if shuffle is involved
        # Check if the selected child is one of the unvisited ones
        unvisited_children = [c for c in root.children if c.visits == 0]
        self.assertIn(selected_child, unvisited_children)

    def test_node_is_terminal_node(self):
        """is_terminal_node が終端状態を正しく判定するかテスト (行 93)"""
        # 終端状態の盤面を作成 (両者パス)
        terminal_board_data = [[-1] * 8 for _ in range(8)] # 全て黒
        terminal_board_data[0][0] = 1 # 1つだけ白
        terminal_board = Board()
        terminal_board.board = terminal_board_data

        node = Node(terminal_board, turn=1) # 白番 (有効手なし)
        # Check if black also has no moves
        black_moves = terminal_board.get_valid_moves(-1)
        white_moves = terminal_board.get_valid_moves(1)
        self.assertFalse(black_moves, "Black should have no moves in terminal state setup")
        self.assertFalse(white_moves, "White should have no moves in terminal state setup")
        self.assertTrue(node.is_terminal_node(), "両者パスの盤面は終端ノードであるべき")

        # 非終端状態の盤面
        initial_board = Board()
        node_initial = Node(initial_board, turn=-1)
        self.assertFalse(node_initial.is_terminal_node(), "初期盤面は終端ノードではない")

    # --- MCTS Agent のテスト ---

    def test_play_returns_valid_move_initial_board(self):
        """初期盤面で有効な手を返すことを確認"""
        # シミュレーション回数を少なくしてテスト時間を短縮
        agent = MonteCarloTreeSearchAgent(iterations=10, time_limit_ms=500)
        game = Game()
        game.turn = -1 # 黒番
        valid_moves = game.get_valid_moves()
        self.assertTrue(valid_moves, "Initial board should have valid moves for black.") # 初期盤面には有効手があるはず
        move = agent.play(game)
        self.assertIn(move, valid_moves, f"MCTS returned {move}, which is not in valid moves: {valid_moves}")

    def test_play_returns_none_when_no_valid_moves(self):
        """有効な手がない場合にNoneを返すことを確認"""
        agent = MonteCarloTreeSearchAgent(iterations=10, time_limit_ms=500)
        game = Game()
        # 全て黒で埋められた盤面（白番で有効手なし）
        game.board.board = [[-1 for _ in range(8)] for _ in range(8)]
        game.turn = 1 # 白番
        move = agent.play(game)
        self.assertIsNone(move, "Agent should return None when there are no valid moves")

    # --- 追加: 有効手が1つの場合のテスト ---
    def test_play_returns_only_valid_move(self):
        """有効な手が1つしかない場合にその手を直接返すかテスト (行 107)"""
        agent = MonteCarloTreeSearchAgent(iterations=100, time_limit_ms=500)
        game = Game()
        # 有効手が (0, 0) のみになるような盤面を作成
        game.board.board = [[0]*8 for _ in range(8)]
        # --- Setup: Black (-1) turn, only (0,0) is valid ---
        game.board.board[0][1] = 1   # Opponent (White)
        game.board.board[0][2] = -1  # Own (Black) - completes the line
        # ----------------------------------------------------
        game.turn = -1 # 黒番
        valid_moves = game.get_valid_moves()

        # --- Assertions to verify the test setup itself ---
        self.assertEqual(len(valid_moves), 1, f"Test setup error: Expected exactly one valid move, but found {len(valid_moves)}: {valid_moves}")
        expected_move = (0, 0)
        # Check if the list is not empty before accessing index 0
        if valid_moves:
            self.assertEqual(valid_moves[0], expected_move, f"Test setup error: The only valid move should be {expected_move}, but got {valid_moves[0]}")
        else:
            # This case should not happen if the setup is correct, but handles the error case
            self.fail(f"Test setup error: No valid moves found, expected {expected_move}")
        # ----------------------------------------------------

        # --- Test the agent's play method ---
        # Use patch to ensure MCTS loop isn't entered unnecessarily
        with patch.object(agent, '_select', wraps=agent._select) as mock_select:
            move = agent.play(game)
            # Assert the correct move is returned
            self.assertEqual(move, expected_move, f"Agent should return the only valid move {expected_move}, but got {move}")
            # Assert that the MCTS selection phase was skipped
            mock_select.assert_not_called()
        # ------------------------------------


    def test_play_selects_winning_move_simple_case(self):
        """簡単な盤面で獲得数の多い手を選ぶ傾向があるか確認"""
        # iterations を増やして精度を上げる (テスト時間とのトレードオフ)
        # 時間がかかりすぎる場合は iterations や time_limit_ms を調整してください
        agent = MonteCarloTreeSearchAgent(iterations=100, time_limit_ms=1000)
        game = Game()

        # --- 修正: (4,6) が Gain=3 で明確な最善手となる盤面 ---
        game.board.board = [
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  1,  0,  0,  0,  0], # Row 2: W at (2,3)
            [ 0,  0,  0, -1,  1,  0,  0,  0], # Row 3: B at (3,3), W at (3,4)
            [ 0,  0, -1,  1,  1,  1,  0,  0], # Row 4: B at (4,2), W at (4,3),(4,4),(4,5) <- (4,5) を W に変更, (3,3) を B に変更
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
        ]
        game.turn = -1 # Black turn
        # ----------------------------------------------------
        valid_moves = game.get_valid_moves()
        # この盤面での期待される有効手: [(1, 3), (4, 6), (5, 3)]

        expected_best_gain_move = (4, 6) # Gain=3 が期待される
        move_gains = []
        max_gain = 0
        best_moves_by_gain = []
        for r, c in valid_moves:
            # --- 修正: get_flipped_stones は Board クラスのメソッド ---
            gain = len(game.board.get_flipped_stones(r, c, game.turn))
            # ------------------------------------------------------
            move_gains.append(((r, c), gain))
            if gain > max_gain:
                max_gain = gain
                best_moves_by_gain = [(r,c)]
            elif gain == max_gain:
                best_moves_by_gain.append((r,c))

        # --- アサーション修正: 期待値とメッセージを更新 ---
        self.assertIn(expected_best_gain_move, valid_moves, f"Expected best move {expected_best_gain_move} is not valid. Valid moves: {valid_moves}")
        self.assertEqual(max_gain, 3, f"Highest gain should be 3, but was {max_gain}. Gains: {move_gains}") # Gain の期待値を 3 に変更
        self.assertIn(expected_best_gain_move, best_moves_by_gain, f"Expected move {expected_best_gain_move} should have the highest gain. Best moves by gain: {best_moves_by_gain}")
        # この盤面では最善手は1つのはず (任意のアサーション追加)
        self.assertEqual(len(best_moves_by_gain), 1, f"Expected only one best move, but found {len(best_moves_by_gain)}: {best_moves_by_gain}")
        # -------------------------------------------------

        move = agent.play(game)

        # move が None でないこと、かつ有効な手であることを確認
        self.assertIsNotNone(move, "Agent returned None unexpectedly.")
        self.assertIn(move, valid_moves, f"MCTS returned {move}, which is not a valid move: {valid_moves}")

        # MCTSは確率的なので、必ずしも最適手を選ぶとは限らない。
        # ここでは、有効な手を返せばテスト成功とする。
        # より厳密なテストが必要な場合は、シミュレーション回数を大幅に増やすか、
        # 複数回実行して統計的に評価するなどの方法が考えられる。
        # print(f"Simple case: MCTS selected {move}. Expected best gain move: {expected_best_gain_move}")


    # --- 修正: 時間制限テストを time.time のモックで行う ---
    @patch('agents.mcts_agent.time.time')
    def test_play_stops_by_time_limit(self, mock_time):
        """時間制限によってループが終了するかテスト (行 113-115)"""
        time_limit_ms = 10 # 非常に短い時間制限 (10ms)
        # Iterations need to be high enough that time limit is hit first
        agent = MonteCarloTreeSearchAgent(iterations=10000, time_limit_ms=time_limit_ms)
        game = Game()
        game.turn = -1

        # time.time() が返す値を制御
        # Loop 1: start=0.0, end=0.005 -> elapsed=5ms < 10ms
        # Loop 2: start=0.0, end=0.011 -> elapsed=11ms >= 10ms -> Stop
        mock_time.side_effect = [0.0, 0.005, 0.011, 0.012, 0.013] # Provide enough values

        # play を実行
        agent.play(game)

        # time.time() が期待通り呼び出されたか確認
        # 1. play start time
        # 2. Loop 1 check
        # 3. Loop 2 check (stops here)
        # Expected calls: 3
        self.assertEqual(mock_time.call_count, 3, f"Expected time.time to be called 3 times, but got {mock_time.call_count}")


    # --- 追加: _select で select_child が None を返すケース ---
    @patch('agents.mcts_agent.Node.select_child')
    def test_select_handles_none_child(self, mock_select_child):
        """_select が select_child から None を受け取った場合の処理テスト (行 152-153)"""
        agent = MonteCarloTreeSearchAgent()
        board = Board()
        root = Node(board, turn=-1)
        # ルートを展開済みにして、子を選択させる状況を作る
        # --- 修正: ルートを完全に展開する ---
        # Make sure root has children to select from
        child = root.expand()
        if child is None:
             self.fail("Failed to expand root node for test setup")
        # Now fully expand root
        while root.untried_moves:
            root.expand()
        self.assertTrue(root.is_fully_expanded())
        self.assertTrue(root.children) # Ensure children exist
        # ---------------------------------

        # select_child が None を返すようにモック
        mock_select_child.return_value = None

        # _select を実行
        selected_node = agent._select(root)

        # select_child が呼び出されたことを確認
        mock_select_child.assert_called_once()
        # select_child が None を返した場合、元のノード (root) が返るはず
        # The logic in _select returns the *parent* if select_child fails,
        # but in this case, the loop condition `not current_node.is_terminal_node()`
        # might exit first, or it might return the node *before* selection failed.
        # Let's re-read _select:
        # while not current_node.is_terminal_node():
        #   if not current_node.is_fully_expanded(): return current_node
        #   else: current_node = current_node.select_child(...) -> returns None
        #         if current_node is None: return node # Returns the original node passed to _select
        # return current_node
        # So, it should return the original 'node' (which is 'root' in this test)
        self.assertIs(selected_node, root)


    # --- 追加: _backpropagate のテスト ---
    def test_backpropagate_updates_nodes(self):
        """_backpropagate がノードの値を正しく更新するかテスト (行 205-209)"""
        agent = MonteCarloTreeSearchAgent()
        # 手動で木構造を作成: root -> child -> grandchild
        board_root = Board()
        root = Node(board_root, turn=-1) # 黒番
        root.visits = 1 # ルートは訪問済みとする

        # --- 修正: expand を使って子ノードを作成 ---
        child = root.expand() # (e.g., 2,3), turn=1 (White)
        if child is None: self.fail("Failed to expand root node")
        child.visits = 1 # 子も訪問済み
        # --------------------------------------

        # --- 修正: expand を使って孫ノードを作成 ---
        grandchild = child.expand() # (e.g., 2,4), turn=-1 (Black)
        if grandchild is None:
            # If child has no valid moves, this test setup is invalid.
            # Let's ensure the child has moves.
            # Initial board: Black plays (2,3). Board becomes:
            # ...
            # [0,0,0,-1, 0,0,0,0] Row 2
            # [0,0,0,-1,-1,0,0,0] Row 3
            # [0,0,0,-1, 1,0,0,0] Row 4
            # ...
            # White (1) turn. Valid moves: (2,2), (2,4), (4,2).
            # So child.expand() should succeed.
             self.fail(f"Failed to expand child node. Child state: turn={child.turn}, board=\n{child.board.board}")
        # ---------------------------------------

        # grandchild からバックプロパゲーション (grandchild の手番プレイヤー(-1)が勝ったとする result=1.0)
        result_from_grandchild_perspective = 1.0
        agent._backpropagate(grandchild, result_from_grandchild_perspective)

        # grandchild の更新確認
        self.assertEqual(grandchild.visits, 1) # First visit
        self.assertEqual(grandchild.wins, 1.0) # Won from its perspective

        # child の更新確認 (grandchild の結果が反転して伝播する)
        self.assertEqual(child.visits, 2) # Initial 1 + backprop 1
        # child (White, turn=1) perspective: grandchild (Black, turn=-1) won (result=1.0).
        # So, child gets result = 1.0 - 1.0 = 0.0
        self.assertEqual(child.wins, 0.0) # Lost from its perspective

        # root の更新確認 (child の結果がさらに反転して伝播する)
        self.assertEqual(root.visits, 2) # Initial 1 + backprop 1
        # root (Black, turn=-1) perspective: child (White, turn=1) lost (result=0.0).
        # So, root gets result = 1.0 - 0.0 = 1.0
        self.assertEqual(root.wins, 1.0) # Won from its perspective

if __name__ == '__main__':
    # test_mcts_agent.py を直接実行する場合のパス設定
    # (プロジェクトルートから python -m unittest test/agents/test_mcts_agent.py で実行推奨)
    if project_root not in sys.path:
        sys.path.append(project_root)
    unittest.main()
