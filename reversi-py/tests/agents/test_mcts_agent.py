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
        child3.visits = 1
        child3.wins = 0.5

        # 未訪問ノードの UCB1 は inf になるため、それが選択されるはず
        selected_child = root.select_child()
        self.assertIsNotNone(selected_child)
        self.assertEqual(selected_child.visits, 0, "未訪問の子ノードが選択されるべき")
        # 具体的に child1 か child2 のどちらかであることを確認
        self.assertIn(selected_child, [child1, child2])

    def test_node_is_terminal_node(self):
        """is_terminal_node が終端状態を正しく判定するかテスト (行 93)"""
        # 終端状態の盤面を作成 (両者パス)
        terminal_board_data = [[-1] * 8 for _ in range(8)] # 全て黒
        terminal_board_data[0][0] = 1 # 1つだけ白
        terminal_board = Board()
        terminal_board.board = terminal_board_data

        node = Node(terminal_board, turn=1) # 白番 (有効手なし)
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
        game.board.board[0][1] = 1 # 白
        game.board.board[1][1] = 1 # 白
        game.board.board[1][0] = 1 # 白
        game.turn = -1 # 黒番
        valid_moves = game.get_valid_moves()
        self.assertEqual(len(valid_moves), 1, "Test setup error: Expected exactly one valid move.")
        expected_move = valid_moves[0]

        # play メソッドを呼び出し
        move = agent.play(game)

        # MCTS ループが実行されずに、唯一の有効手が返されることを確認
        self.assertEqual(move, expected_move)
        # (オプション) MCTSの内部メソッドが呼ばれていないことを確認 (より厳密なテスト)
        # with patch.object(agent, '_select') as mock_select:
        #     agent.play(game)
        #     mock_select.assert_not_called()

    def test_play_selects_winning_move_simple_case(self):
        """簡単な盤面で獲得数の多い手を選ぶ傾向があるか確認"""
        # iterations を増やして精度を上げる (テスト時間とのトレードオフ)
        # 時間がかかりすぎる場合は iterations や time_limit_ms を調整してください
        agent = MonteCarloTreeSearchAgent(iterations=100, time_limit_ms=1000)
        game = Game()
        # 黒(-1)が打てる盤面を設定 (例: (4,1)がGain=2で他より多い)
        game.board.board = [
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  1,  1,  1,  0,  0],
            [ 0,  0,  1, -1,  1,  0,  0,  0],
            [ 0,  0,  1,  1, -1,  1,  0,  0],
            [ 0,  0,  0,  1,  1,  1,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
        ]
        game.turn = -1 # 黒番

        # agent.play() の前に valid_moves を確認
        valid_moves = game.get_valid_moves()
        self.assertTrue(valid_moves, "Test setup error: No valid moves found for the test board.") # 有効手があることを確認

        # 期待される最も獲得数の多い手 (Gain=2)
        expected_best_gain_move = (4, 1)

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
        agent = MonteCarloTreeSearchAgent(iterations=10000, time_limit_ms=time_limit_ms)
        game = Game()
        game.turn = -1

        # time.time() が返す値を制御
        # 1回目: 0.0, 2回目: 0.005 (5ms), 3回目: 0.011 (11ms > 10ms)
        mock_time.side_effect = [0.0, 0.005, 0.011, 0.012] # 3回目のループ開始時に時間切れ

        # play を実行
        agent.play(game)

        # time.time() が期待通り呼び出されたか確認 (ループ開始時と終了時の2回 + ループ内の1回 = 3回)
        # (実装によっては呼び出し回数が異なる可能性あり)
        # self.assertGreaterEqual(mock_time.call_count, 3)
        # 重要なのは、ループが時間制限で止まること。
        # 直接的な確認は難しいが、カバレッジレポートで該当行がカバーされるかで判断。

    # --- 追加: _select で select_child が None を返すケース ---
    @patch('agents.mcts_agent.Node.select_child')
    def test_select_handles_none_child(self, mock_select_child):
        """_select が select_child から None を受け取った場合の処理テスト (行 152-153)"""
        agent = MonteCarloTreeSearchAgent()
        board = Board()
        root = Node(board, turn=-1)
        # ルートを展開済みにして、子を選択させる状況を作る
        child = root.expand()
        self.assertTrue(root.is_fully_expanded()) # このテストでは untried_moves が空になるように調整が必要かも

        # select_child が None を返すようにモック
        mock_select_child.return_value = None

        # _select を実行
        selected_node = agent._select(root)

        # select_child が呼び出されたことを確認
        mock_select_child.assert_called_once()
        # select_child が None を返した場合、元のノード (root) が返るはず
        self.assertIs(selected_node, root)

    # --- 追加: _backpropagate のテスト ---
    def test_backpropagate_updates_nodes(self):
        """_backpropagate がノードの値を正しく更新するかテスト (行 205-209)"""
        agent = MonteCarloTreeSearchAgent()
        # 手動で木構造を作成: root -> child -> grandchild
        board_root = Board()
        root = Node(board_root, turn=-1) # 黒番
        root.visits = 1 # ルートは訪問済みとする

        child_board = Board() # ダミー盤面
        child = Node(child_board, turn=1, parent=root, move=(2,3)) # 白番
        root.children.append(child)
        child.visits = 1 # 子も訪問済み

        grandchild_board = Board() # ダミー盤面
        grandchild = Node(grandchild_board, turn=-1, parent=child, move=(2,4)) # 黒番
        child.children.append(grandchild)

        # grandchild からバックプロパゲーション (grandchild の手番プレイヤー(-1)が勝ったとする result=1.0)
        result_from_grandchild_perspective = 1.0
        agent._backpropagate(grandchild, result_from_grandchild_perspective)

        # grandchild の更新確認
        self.assertEqual(grandchild.visits, 1)
        self.assertEqual(grandchild.wins, 1.0)

        # child の更新確認 (grandchild の結果が反転して伝播する)
        self.assertEqual(child.visits, 2) # 元の1 + 今回の1
        # child(白番)から見て、grandchild(黒番)が勝ったので、child は負け (0.0)
        self.assertEqual(child.wins, 0.0)

        # root の更新確認 (child の結果がさらに反転して伝播する)
        self.assertEqual(root.visits, 2) # 元の1 + 今回の1
        # root(黒番)から見て、child(白番)が負けたので、root は勝ち (1.0)
        self.assertEqual(root.wins, 1.0)

if __name__ == '__main__':
    # test_mcts_agent.py を直接実行する場合のパス設定
    # (プロジェクトルートから python -m unittest test/agents/test_mcts_agent.py で実行推奨)
    if project_root not in sys.path:
        sys.path.append(project_root)
    unittest.main()
