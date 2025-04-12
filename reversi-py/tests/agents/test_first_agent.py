# tests/agents/test_first_agent.py
import unittest
from agents.first_agent import FirstAgent
from game import Game

class TestFirstAgent(unittest.TestCase):
    def test_play_returns_first_valid_move(self):
        agent = FirstAgent()
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
        agent = FirstAgent()
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

if __name__ == '__main__':
    unittest.main()
