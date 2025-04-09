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
        """
        agent = GainAgent()
        board = Board()
        # テスト用の盤面を設定
        board.board = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, -1, 1, 0, 0, 0], # 黒(-1), 白(1)
            [0, 0, 0, 1, 1, 0, 0, 0], # 白(1), 白(1)
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        game = Game()
        game.board = board  # 作成した盤面を Game オブジェクトに設定
        game.turn = -1      # 手番を黒(-1)に設定

        # GainAgent に手を選択させる
        move = agent.play(game)

        # この盤面での有効な手を取得
        valid_moves = game.get_valid_moves()

        # --- テストコード内で最大獲得数と候補手を計算 ---
        max_gain_in_test = -1
        move_gains_in_test = []
        if valid_moves: # 有効な手がある場合のみ計算
            for vm in valid_moves:
                # GainAgent と同じ方法で gain を計算 (get_flipped_stones を使用)
                flipped_stones = game.board.get_flipped_stones(vm[0], vm[1], game.turn)
                gain = len(flipped_stones)
                move_gains_in_test.append((vm, gain))
                if gain > max_gain_in_test:
                    max_gain_in_test = gain

            # 最大獲得数を持つ手のリストをテストコード内で作成
            expected_best_moves = [m for m, g in move_gains_in_test if g == max_gain_in_test]
        else:
            expected_best_moves = []
        # ---------------------------------------------

        # アサーション
        if not valid_moves:
            self.assertIsNone(move, "No valid moves, agent should return None")
        else:
            # 1. 返された手が有効な手か確認
            self.assertIn(move, valid_moves,
                          f"GainAgent returned {move}, which is not a valid move: {valid_moves}")

            # 2. 返された手が最大獲得数の手のいずれかであることを確認
            self.assertTrue(expected_best_moves, "Calculation in test failed to find best moves.") # テスト自体の計算確認
            self.assertIn(move, expected_best_moves,
                          f"GainAgent returned {move} (gain={len(game.board.get_flipped_stones(move[0], move[1], game.turn))}), "
                          f"which is not among the moves with max gain ({max_gain_in_test}): {expected_best_moves}")

    # --- 他のテストケースが必要であればここに追加 ---
    # 例: 白番のテスト、獲得数が異なる場合のテスト、有効な手がない場合のテストなど
    def test_play_returns_none_when_no_valid_moves(self):
        """有効な手がない場合にNoneを返すことをテストする"""
        agent = GainAgent()
        game = Game()
        # 全て黒で埋められた盤面（白番で有効手なし）
        game.board.board = [[-1 for _ in range(8)] for _ in range(8)]
        game.turn = 1 # 白番
        move = agent.play(game)
        self.assertIsNone(move, "Agent should return None when there are no valid moves")


if __name__ == '__main__':
    unittest.main()
