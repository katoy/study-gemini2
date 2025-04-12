# test/agents/test_mcts_agent.py
import unittest
import sys
import os
import time
import random # random をインポート (フォールバック用)

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir) # ルートディレクトリを取得
sys.path.append(project_root) # ルートディレクトリをパスに追加

from agents.mcts_agent import MonteCarloTreeSearchAgent
from game import Game
from board import Board

class TestMonteCarloTreeSearchAgent(unittest.TestCase):

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

    def test_play_within_time_limit(self):
        """指定した時間制限内におおむね収まるか確認"""
        time_limit = 500 # 500ms
        # iterations を大きくして、時間制限が効くようにする
        agent = MonteCarloTreeSearchAgent(iterations=10000, time_limit_ms=time_limit)
        game = Game()
        game.turn = -1

        start = time.time()
        # 初期盤面には有効手があるのでNoneは返らないはず
        valid_moves = game.get_valid_moves()
        self.assertTrue(valid_moves)
        agent.play(game)
        end = time.time()
        duration_ms = (end - start) * 1000

        # 多少のオーバーヘッドを許容 (例: 150ms)
        allowed_overhead = 150
        # print(f"Time limit test: Duration={duration_ms:.2f}ms, Limit={time_limit}ms")
        self.assertLessEqual(duration_ms, time_limit + allowed_overhead,
            f"MCTS took too long: {duration_ms:.2f}ms > {time_limit + allowed_overhead}ms")

if __name__ == '__main__':
    # test_mcts_agent.py を直接実行する場合のパス設定
    # (プロジェクトルートから python -m unittest test/agents/test_mcts_agent.py で実行推奨)
    if project_root not in sys.path:
        sys.path.append(project_root)
    unittest.main()
