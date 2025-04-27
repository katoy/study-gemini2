# test/agents/test_mcts_agent.py
import unittest
import sys
import os
import time
import random # random をインポート (フォールバック用)
# --- unittest.mock から patch をインポート ---
from unittest.mock import patch, MagicMock
import math # UCB1 計算用に math をインポート

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir) # ルートディレクトリを取得
sys.path.append(project_root) # ルートディレクトリをパスに追加

# --- Node クラスもインポート ---
from agents.mcts_agent import MonteCarloTreeSearchAgent, Node
from game import Game
from board import Board

from unittest.mock import patch

@patch('agents.api_agent.requests.post')
class TestMonteCarloTreeSearchAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_post = MagicMock()
        cls.mock_post.return_value.status_code = 200
        cls.mock_post.return_value.json.return_value = {'move': None}
        TestMonteCarloTreeSearchAgent.mock_post = cls.mock_post

    def setUp(self):
        pass

    # --- Node クラスのテストを追加 ---
    def test_node_ucb1_unvisited(self, mock_post):
        """未訪問ノードのUCB1スコアが無限大になるかテスト (行 27)"""
        board = Board()
        node = Node(board, turn=-1)
        self.assertEqual(node.visits, 0)

        # select_child の動作で確認するアプローチを採用
        root = Node(board, turn=-1)
        root.visits = 1
        unvisited_child = root.expand()
        if unvisited_child is None: self.fail("Expansion failed")

        # 訪問済みの子を作成
        visited_child = root.expand()
        if visited_child is None: self.fail("Expansion failed")
        visited_child.visits = 1
        visited_child.wins = 0.5

        # 未訪問の子が選択されることを確認 (無限大スコアのため)
        selected = root.select_child()
        self.assertIs(selected, unvisited_child)


    def test_node_select_child_prefers_unvisited(self, mock_post):
        """select_child が未訪問の子ノードを優先するかテスト (行 49 前半)"""
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
        unvisited_children = [c for c in root.children if c.visits == 0]
        self.assertIn(selected_child, unvisited_children)

    # --- 追加: 行 49 (shuffle) をカバーするテスト ---
    def test_node_select_child_chooses_best_ucb1_among_visited(self, mock_post):
        """select_child が訪問済みの子の中から最もUCB1スコアが高いものを選ぶかテスト (行 49 カバー)"""
        board = Board()
        root = Node(board, turn=-1)
        root.visits = 10 # 親ノードは複数回訪問済みとする

        child1 = root.expand()
        child2 = root.expand()
        child3 = root.expand()
        child4 = root.expand()
        if child1 is None or child2 is None or child3 is None or child4 is None:
             self.fail("Node expansion failed during test setup")

        child1.visits = 3
        child1.wins = 2
        child2.visits = 5
        child2.wins = 1
        child3.visits = 2
        child3.wins = 1.5
        child4.visits = 4
        child4.wins = 3

        self.assertTrue(root.is_fully_expanded())
        for child in root.children:
            self.assertGreater(child.visits, 0)

        C = math.sqrt(2)
        log_parent_visits = math.log(root.visits)
        best_score = -float('inf')
        expected_best_children = []

        for child in root.children:
            exploit = child.wins / child.visits
            explore = C * math.sqrt(log_parent_visits / child.visits)
            score = exploit + explore
            if score > best_score:
                best_score = score
                expected_best_children = [child]
            elif score == best_score:
                expected_best_children.append(child)

        self.assertEqual(len(expected_best_children), 1, f"Expected exactly one best child, but found {len(expected_best_children)}")
        expected_best_child = expected_best_children[0]

        selected_child = root.select_child()

        self.assertIsNotNone(selected_child)
        self.assertIs(selected_child, expected_best_child, f"Expected child {expected_best_child.move} with highest UCB1, but got {selected_child.move}")

    # --- 追加: 行 49 (shuffle) をカバーするテスト (UCB1同点の場合) ---
    @patch('agents.mcts_agent.random.shuffle')
    def test_node_select_child_shuffles_equally_best_visited(self, mock_shuffle, mock_post):
        """select_child がUCB1スコアが同点の訪問済みの子をシャッフルするかテスト (行 49 カバー)"""
        mock_board_root = MagicMock(spec=Board)
        mock_board_root.get_valid_moves.return_value = []
        root = Node(board=mock_board_root, turn=-1, parent=None, move=None)
        root.visits = 10

        mock_board_child = MagicMock(spec=Board)
        mock_board_child.get_valid_moves.return_value = []
        child1 = Node(board=mock_board_child, turn=1, parent=root, move=(3, 5))
        child1.visits = 2
        child1.wins = 1

        child2 = Node(board=mock_board_child, turn=1, parent=root, move=(5, 3))
        child2.visits = 2
        child2.wins = 1

        child3 = Node(board=mock_board_child, turn=1, parent=root, move=(5, 5))
        child3.visits = 2
        child3.wins = 1

        child4 = Node(board=mock_board_child, turn=1, parent=root, move=(1, 1))
        child4.visits = 3
        child4.wins = 1

        root.children = [child1, child2, child3, child4]
        root.untried_moves = []

        shuffle_calls_before = mock_shuffle.call_count

        selected_child = root.select_child(exploration_weight=1.0)

        shuffle_calls_after = mock_shuffle.call_count

        expected_shuffled_children = [child1, child2, child3]

        self.assertEqual(shuffle_calls_after, shuffle_calls_before,
                         "random.shuffle should not be called within select_child in the current implementation.")

        self.assertIs(selected_child, child1, "Current implementation should return the first best child found.")

    def test_node_is_terminal_node(self, mock_post):
        """is_terminal_node が終端状態を正しく判定するかテスト (行 93)"""
        terminal_board_data = [[-1] * 8 for _ in range(8)]
        terminal_board_data[0][0] = 1
        terminal_board = Board()
        terminal_board.board = terminal_board_data

        node = Node(terminal_board, turn=1)
        black_moves = terminal_board.get_valid_moves(-1)
        white_moves = terminal_board.get_valid_moves(1)
        self.assertFalse(black_moves, "Black should have no moves in terminal state setup")
        self.assertFalse(white_moves, "White should have no moves in terminal state setup")
        self.assertTrue(node.is_terminal_node(), "両者パスの盤面は終端ノードであるべき")

        initial_board = Board()
        node_initial = Node(initial_board, turn=-1)
        self.assertFalse(node_initial.is_terminal_node(), "初期盤面は終端ノードではない")

    # --- MCTS Agent のテスト ---

    def test_play_returns_valid_move_initial_board(self, mock_post):
        """初期盤面で有効な手を返すことを確認"""
        agent = MonteCarloTreeSearchAgent(iterations=10, time_limit_ms=500)
        game = Game()
        game.turn = -1
        valid_moves = game.get_valid_moves()
        self.assertTrue(valid_moves, "Initial board should have valid moves for black.")
        move = agent.play(game)
        self.assertIn(move, valid_moves, f"MCTS returned {move}, which is not in valid moves: {valid_moves}")

    def test_play_returns_none_when_no_valid_moves(self, mock_post):
        """有効な手がない場合にNoneを返すことを確認"""
        agent = MonteCarloTreeSearchAgent(iterations=10, time_limit_ms=500)
        game = Game()
        game.board.board = [[-1 for _ in range(8)] for _ in range(8)]
        game.turn = 1
        move = agent.play(game)
        self.assertIsNone(move, "Agent should return None when there are no valid moves")

    # --- 有効手が1つの場合のテスト (行 107 カバー) ---
    def test_play_returns_only_valid_move(self, mock_post):
        """有効な手が1つしかない場合にその手を直接返すかテスト (行 107)"""
        agent = MonteCarloTreeSearchAgent(iterations=100, time_limit_ms=500)
        game = Game()
        game.board.board = [[0]*8 for _ in range(8)]
        game.board.board[0][1] = 1
        game.board.board[0][2] = -1
        game.turn = -1
        valid_moves = game.get_valid_moves()

        self.assertEqual(len(valid_moves), 1, f"Test setup error: Expected exactly one valid move, but found {len(valid_moves)}: {valid_moves}")
        expected_move = (0, 0)
        if valid_moves:
            self.assertEqual(valid_moves[0], expected_move, f"Test setup error: The only valid move should be {expected_move}, but got {valid_moves[0]}")
        else:
            self.fail(f"Test setup error: No valid moves found, expected {expected_move}")

        with patch.object(agent, '_select', wraps=agent._select) as mock_select, \
             patch.object(agent, '_expand', wraps=agent._expand) as mock_expand, \
             patch.object(agent, '_simulate', wraps=agent._simulate) as mock_simulate, \
             patch.object(agent, '_backpropagate', wraps=agent._backpropagate) as mock_backpropagate:
            move = agent.play(game)
            self.assertEqual(move, expected_move, f"Agent should return the only valid move {expected_move}, but got {move}")
            mock_select.assert_not_called()
            mock_expand.assert_not_called()
            mock_simulate.assert_not_called()
            mock_backpropagate.assert_not_called()

    def test_play_selects_winning_move_simple_case(self, mock_post):
        """簡単な盤面で獲得数の多い手を選ぶ傾向があるか確認"""
        agent = MonteCarloTreeSearchAgent(iterations=100, time_limit_ms=1000)
        game = Game()

        game.board.board = [
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  1,  0,  0,  0,  0],
            [ 0,  0,  0, -1,  1,  0,  0,  0],
            [ 0,  0, -1,  1,  1,  1,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
        ]
        game.turn = -1
        valid_moves = game.get_valid_moves()

        expected_best_gain_move = (4, 6)
        move_gains = []
        max_gain = 0
        best_moves_by_gain = []
        for r, c in valid_moves:
            gain = len(game.board.get_flipped_stones(r, c, game.turn))
            move_gains.append(((r, c), gain))
            if gain > max_gain:
                max_gain = gain
                best_moves_by_gain = [(r,c)]
            elif gain == max_gain:
                best_moves_by_gain.append((r,c))

        self.assertIn(expected_best_gain_move, valid_moves, f"Expected best move {expected_best_gain_move} is not valid. Valid moves: {valid_moves}")
        self.assertEqual(max_gain, 3, f"Highest gain should be 3, but was {max_gain}. Gains: {move_gains}")
        self.assertIn(expected_best_gain_move, best_moves_by_gain, f"Expected move {expected_best_gain_move} should have the highest gain. Best moves by gain: {best_moves_by_gain}")
        self.assertEqual(len(best_moves_by_gain), 1, f"Expected only one best move, but found {len(best_moves_by_gain)}: {best_moves_by_gain}")

        move = agent.play(game)

        self.assertIsNotNone(move, "Agent returned None unexpectedly.")
        self.assertIn(move, valid_moves, f"MCTS returned {move}, which is not a valid move: {valid_moves}")

    # --- 時間制限テスト (行 113-115 カバー) ---
    @patch('agents.mcts_agent.time.time')
    def test_play_stops_by_time_limit(self, mock_time, mock_post):
        """時間制限によってループが終了するかテスト (行 113-115)"""
        time_limit_ms = 10
        agent = MonteCarloTreeSearchAgent(iterations=10000, time_limit_ms=time_limit_ms)
        game = Game()
        game.turn = -1

        mock_time.side_effect = [0.0, 0.005, 0.011, 0.012, 0.013] # 5回呼ぶように変更

        agent.play(game)

        self.assertGreaterEqual(mock_time.call_count, 3, f"Expected time.time to be called at least 3 times, but got {mock_time.call_count}")

    # --- _select で select_child が None を返すケース (行 153 カバー) ---
    @patch('agents.mcts_agent.Node.select_child')
    def test_select_handles_none_child(self, mock_select_child, mock_post):
        """_select が select_child から None を受け取った場合の処理テスト (行 153)"""
        agent = MonteCarloTreeSearchAgent()
        board = Board()
        root = Node(board, turn=-1)
        child = root.expand()
        if child is None:
             self.fail("Failed to expand root node for test setup")
        while root.untried_moves:
            root.expand()
        self.assertTrue(root.is_fully_expanded())
        self.assertTrue(root.children)

        mock_select_child.return_value = None

        selected_node = agent._select(root)

        mock_select_child.assert_called_once()
        self.assertIs(selected_node, root)

    # --- _backpropagate のテスト (行 205-209 カバー) ---
    def test_backpropagate_updates_nodes(self, mock_post):
        """_backpropagate がノードの値を正しく更新するかテスト (行 205-209)"""
        agent = MonteCarloTreeSearchAgent()
        board_root = Board()
        root = Node(board_root, turn=-1)
        root.visits = 1

        child = root.expand()
        if child is None: self.fail("Failed to expand root node")
        child.visits = 1

        grandchild = child.expand()
        if grandchild is None:
             self.fail(f"Failed to expand child node. Child state: turn={child.turn}, board=\n{child.board.board}")

        result_from_grandchild_perspective = 1.0
        agent._backpropagate(grandchild, result_from_grandchild_perspective)

        self.assertEqual(grandchild.visits, 1)
        self.assertEqual(grandchild.wins, 1.0)

        self.assertEqual(child.visits, 2)
        self.assertEqual(child.wins, 0.0)

        self.assertEqual(root.visits, 2)
        self.assertEqual(root.wins, 1.0)

    # --- Node.expand() が None を返すケースのテスト ---
    def test_node_expand_returns_none_when_no_untried_moves(self, mock_post):
        """Node.expand が未試行の手がない場合に None を返すかテスト"""
        board = Board()
        node = Node(board, turn=-1)
        while node.untried_moves:
            node.expand()
        self.assertTrue(node.is_fully_expanded())
        self.assertIsNone(node.expand(), "expand() should return None when no untried moves are left")

    # --- _simulate() 内で両者パスになった場合の勝敗判定のテスト ---
    def test_simulate_handles_both_players_passing(self, mock_post):
        """_simulate が両者パスの場合に勝敗を正しく判定するかテスト"""
        agent = MonteCarloTreeSearchAgent()
        board = Board()
        board.board = [[-1] * 8 for _ in range(8)]
        board.board[0][0] = 1
        node = Node(board, turn=1)

        result = agent._simulate(node)
        black_count, white_count = node.board.count_stones()
        if black_count > white_count:
            self.assertEqual(result, 0.0, "黒が多い場合、白視点では負け (0.0) になるはず")
        elif white_count > black_count:
            self.assertEqual(result, 1.0, "白が多い場合、白視点では勝ち (1.0) になるはず")
        else:
            self.assertEqual(result, 0.5, "同数の場合、引き分け (0.5) になるはず")

    # --- _check_terminal_state() が終端状態を正しく判定し、勝者を返すテスト ---
    def test_check_terminal_state_returns_winner(self, mock_post):
        """_check_terminal_state が終端状態で勝者を正しく返すかテスト"""
        agent = MonteCarloTreeSearchAgent()
        board = Board()
        board.board = [[-1] * 8 for _ in range(8)]
        node = Node(board, turn=1)
        result = agent._check_terminal_state(node)
        self.assertEqual(result, 0.0, "黒勝ちの場合、白視点では負け (0.0) になるはず")

        board = Board()
        board.board = [[1] * 8 for _ in range(8)]
        node = Node(board, turn=-1)
        result = agent._check_terminal_state(node)
        self.assertEqual(result, 0.0, "白勝ちの場合、黒視点では負け (0.0) になるはず")

        board = Board()
        board.board = [[0] * 8 for _ in range(8)]
        node = Node(board, turn=-1)
        result = agent._check_terminal_state(node)
        self.assertEqual(result, 0.5, "引き分けの場合、0.5を返すはず")

    # --- play() 内で _select() が None を返す場合のテスト ---
    @patch('agents.mcts_agent.MonteCarloTreeSearchAgent._select')
    def test_play_handles_select_returning_none(self, mock_select, mock_post):
        """play() が _select() から None を受け取った場合に適切に処理するかテスト"""
        agent = MonteCarloTreeSearchAgent(iterations=10, time_limit_ms=500)
        game = Game()
        game.turn = -1
        mock_select.return_value = None
        move = agent.play(game)
        valid_moves = game.get_valid_moves()
        self.assertIn(move, valid_moves, "_select() が None を返した場合、ランダムな有効手が返されるはず")

    # --- play() 内で例外が発生した場合のテスト ---
    @patch('agents.mcts_agent.MonteCarloTreeSearchAgent._select')
    def test_play_handles_exceptions_during_search(self, mock_select, mock_post):
        """play() が探索中に例外が発生した場合に適切に処理するかテスト"""
        agent = MonteCarloTreeSearchAgent(iterations=10, time_limit_ms=500)
        game = Game()
        game.turn = -1
        mock_select.side_effect = Exception("Test exception")
        move = agent.play(game)
        valid_moves = game.get_valid_moves()
        self.assertIn(move, valid_moves, "例外発生時、ランダムな有効手が返されるはず")
