# tests/agents/test_random_agent.py
import unittest
from agents.random_agent import RandomAgent
from game import Game

class TestRandomAgent(unittest.TestCase):
    def test_play_returns_valid_move(self):
        agent = RandomAgent()
        game = Game()
        game.board.board = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, -1, 1, 0, 0, 0],
            [0, 0, 0, 1, -1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        game.turn = -1
        move = agent.play(game)
        self.assertIn(move, game.get_valid_moves())

    def test_play_returns_none_when_no_valid_moves(self):
        agent = RandomAgent()
        game = Game()
        game.board.board = [
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
        ]
        game.turn = 1
        move = agent.play(game)
        self.assertIsNone(move)

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
        """RandomAgentが盤面に実際に手を打つことを確認するテスト"""
        self._test_play_makes_a_move_on_the_board(RandomAgent)

if __name__ == '__main__':
    unittest.main()
