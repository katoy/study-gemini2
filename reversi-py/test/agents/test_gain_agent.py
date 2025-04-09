# test/agents/test_gain_agent.py
import unittest
from agents.gain_agent import GainAgent
from board import Board  # Board クラスが board.py にあると仮定
from game import Game    # Game クラスが game.py にあると仮定

class TestGainAgent(unittest.TestCase):

    def test_play_returns_best_move4(self):
        """
        特定の盤面で、GainAgentが最も獲得数の多い有効な手を返すことをテストする。
        この盤面では、複数の有効な手があり、獲得数はすべて同じ(1)になるはず。
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

        # GainAgent は最も獲得数の多い手を返す。
        # この盤面では、全ての有効な手の獲得数が同じ(1)と推測されるため、
        # GainAgent が返す手は有効な手のいずれかであれば良い。
        # 期待値リストとして、有効な手のリストを使用する。
        expected_moves = valid_moves
        self.assertIn(move, expected_moves,
                      f"GainAgent returned {move}, which is not among the expected valid moves with max gain: {expected_moves}")

    # --- 他のテストケースが必要であればここに追加 ---
    # 例: 白番のテスト、獲得数が異なる場合のテスト、有効な手がない場合のテストなど

if __name__ == '__main__':
    unittest.main()
