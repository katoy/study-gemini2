# test/agents/test_gain_agent.py
import unittest
import random # random をインポート (シード固定用、任意)
from agents.gain_agent import GainAgent # TempGame は不要
from board import Board
from game import Game

# デバッグのために乱数シードを固定したい場合は、ここで設定 (任意)
# random.seed(42)

class TestGainAgent(unittest.TestCase):

    def test_play_returns_best_move4(self):
        """
        特定の盤面で、GainAgentが最も獲得数の多い有効な手を返すことをテストする。
        (最大獲得数の手が1つのケース)
        """
        agent = GainAgent()
        board = Board()
        # テスト用の盤面を設定 (黒番で (1,3) が gain=2 で最大) # コメント修正
        board.board = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1,-1, 0, 0, 0],
            [0, 0, 0,-1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        game = Game()
        game.board = board
        game.turn = -1 # 黒番

        move = agent.play(game)
        valid_moves = game.get_valid_moves()

        max_gain_in_test = -1
        move_gains_in_test = []
        if valid_moves:
            for vm in valid_moves:
                flipped_stones = game.board.get_flipped_stones(vm[0], vm[1], game.turn)
                gain = len(flipped_stones)
                move_gains_in_test.append((vm, gain))
                if gain > max_gain_in_test:
                    max_gain_in_test = gain
            expected_best_moves = [m for m, g in move_gains_in_test if g == max_gain_in_test]
        else:
            expected_best_moves = []

        if not valid_moves:
            self.assertIsNone(move, "No valid moves, agent should return None")
        else:
            self.assertIn(move, valid_moves)
            self.assertTrue(expected_best_moves)
            self.assertIn(move, expected_best_moves)
            # このケースでは最大獲得数の手は1つのはず
            self.assertEqual(len(expected_best_moves), 1, f"Expected only one best move, but found: {expected_best_moves}")
            # --- 修正: 期待値を (1, 3) に変更 ---
            self.assertEqual(move, (1, 3), f"Expected (1, 3) as the best move, but got {move}") # 具体的な手も確認
            # ------------------------------------

    # --- 追加: 最大獲得数の手が複数ある場合のテスト ---
    def test_play_returns_one_of_best_moves_when_multiple(self):
        """
        最大獲得数の手が複数ある場合に、そのいずれかを返すことをテストする。
        """
        agent = GainAgent()
        board = Board()
        # テスト用の盤面を設定 (黒番で gain=1 の手が複数ある) # コメント修正
        board.board = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 1,-1, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        game = Game()
        game.board = board
        game.turn = -1 # 黒番

        move = agent.play(game)
        valid_moves = game.get_valid_moves()

        max_gain_in_test = -1
        move_gains_in_test = []
        if valid_moves:
            for vm in valid_moves:
                flipped_stones = game.board.get_flipped_stones(vm[0], vm[1], game.turn)
                gain = len(flipped_stones)
                move_gains_in_test.append((vm, gain))
                if gain > max_gain_in_test:
                    max_gain_in_test = gain
            expected_best_moves = [m for m, g in move_gains_in_test if g == max_gain_in_test]
        else:
            expected_best_moves = []

        if not valid_moves:
            self.assertIsNone(move, "No valid moves, agent should return None")
        else:
            self.assertIn(move, valid_moves)
            self.assertTrue(expected_best_moves)
            # このケースでは最大獲得数の手は複数あるはず
            self.assertGreater(len(expected_best_moves), 1, f"Expected multiple best moves, but found only: {expected_best_moves}")
            # --- 修正: 期待される候補リストを実際の最善手リストに変更 ---
            # 盤面と is_valid_move の結果に基づき、Gain=1 の手が最善手となる
            expected_candidates = [(1, 3), (3, 1), (3, 5), (5, 3), (5, 5)]
            # -----------------------------------------------------
            self.assertListEqual(sorted(expected_best_moves), sorted(expected_candidates), f"Calculated best moves {expected_best_moves} do not match expected {expected_candidates}")
            # 返された手が候補のいずれかであることを確認
            self.assertIn(move, expected_best_moves,
                          f"GainAgent returned {move}, which is not among the best moves: {expected_best_moves}")
    # -------------------------------------------------

    def test_play_returns_none_when_no_valid_moves(self):
        """有効な手がない場合にNoneを返すことをテストする"""
        agent = GainAgent()
        game = Game()
        # 全て黒で埋められた盤面（白番で有効手なし）
        game.board.board = [[-1 for _ in range(8)] for _ in range(8)]
        game.turn = 1 # 白番
        move = agent.play(game)
        self.assertIsNone(move, "Agent should return None when there are no valid moves")


    def _test_play_makes_a_move_on_the_board(self, agent_class):
        """エージェントが盤面に実際に手を打つことを確認するテスト"""
        import copy
        agent = agent_class()
        game = Game()
        game.set_players(4, 0)  # 黒を指定されたエージェント、白を人間に設定
        initial_board = game.board.get_board()
        valid_moves = game.get_valid_moves()

        move = agent.play(game)

        self.assertIsNotNone(move, f"{agent_class.__name__}は有効な手を返す必要があります")
        self.assertIn(move, valid_moves, f"{agent_class.__name__}は有効な手を返す必要があります")

        # 盤面が更新されていることを確認
        updated_board = copy.deepcopy(game.board.board)
        # 実際に石が置かれているか確認
        row, col = move
        game.board.board[row][col] = -1
        self.assertNotEqual(initial_board, updated_board, f"{agent_class.__name__}は盤面を更新する必要があります")

    def test_play_makes_a_move_on_the_board(self):
        """GainAgentが盤面に実際に手を打つことを確認するテスト"""
        self._test_play_makes_a_move_on_the_board(GainAgent)

if __name__ == '__main__':
    unittest.main()
