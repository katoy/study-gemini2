# tests/agents/test_base_agent.py
import unittest
from agents.base_agent import Agent
from game import Game

class TestBaseAgent(unittest.TestCase):
    def test_play_not_implemented(self):
        agent = Agent()
        game = Game()
        with self.assertRaises(NotImplementedError):
            agent.play(game)

if __name__ == '__main__':
    unittest.main()
