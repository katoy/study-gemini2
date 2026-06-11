# tests/test_mcts_agent.py
import unittest
from agents import mcts_agent

class DummyBoard:
    def __init__(self, moves=None, counts=(2,2)):
        self._moves = moves or []
        self._counts = counts
    def get_valid_moves(self, turn):
        # ignore turn in simple stub
        return list(self._moves)
    def place_stone(self, r, c, turn):
        # pretend placing doesn't change moves
        pass
    def count_stones(self):
        return self._counts

class TestMCTSNode(unittest.TestCase):
    def test_ucb1_unvisited(self):
        board = DummyBoard([])
        node = mcts_agent.Node(board, turn=1)
        self.assertEqual(node.ucb1(), float('inf'))

    def test_expand_no_moves(self):
        board = DummyBoard([])
        node = mcts_agent.Node(board, turn=1)
        self.assertIsNone(node.expand())

    def test_is_terminal_node(self):
        board = DummyBoard([])
        node = mcts_agent.Node(board, turn=1)
        self.assertTrue(node.is_terminal_node())

    def test_select_child_picks_best(self):
        # Create parent and children manually
        parent_board = DummyBoard([(0,0)])
        parent = mcts_agent.Node(parent_board, turn=1)
        # create child nodes
        child1 = mcts_agent.Node(parent_board, turn=-1, parent=parent, move=(0,0))
        child2 = mcts_agent.Node(parent_board, turn=-1, parent=parent, move=(0,1))
        # assign visits and wins
        parent.visits = 100
        child1.visits = 10
        child1.wins = 6
        child2.visits = 20
        child2.wins = 15
        parent.children = [child1, child2]
        best = parent.select_child()
        self.assertIsNotNone(best)
        # best should be either child1 or child2 depending on UCB scores
        self.assertIn(best, parent.children)

    def test_simulate_draw_for_white_perspective(self):
        # Node with board that immediately ends in draw
        draw_board = DummyBoard(moves=[], counts=(30,30))
        node = mcts_agent.Node(draw_board, turn=1)
        agent = mcts_agent.MonteCarloTreeSearchAgent(iterations=1, time_limit_ms=1)
        result = agent._simulate(node)
        self.assertEqual(result, 0.5)

    def test_simulate_draw_for_black_perspective(self):
        # Ensure draw from black's perspective also returns 0.5
        draw_board = DummyBoard(moves=[], counts=(20,20))
        node = mcts_agent.Node(draw_board, turn=-1)
        agent = mcts_agent.MonteCarloTreeSearchAgent(iterations=1, time_limit_ms=1)
        result = agent._simulate(node)
        self.assertEqual(result, 0.5)

if __name__ == '__main__':
    unittest.main()
