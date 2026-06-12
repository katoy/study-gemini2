# tests/test_ai_logging.py
import unittest
import logging
import pygame
import os
import sys
from unittest.mock import MagicMock

# ensure repo package import works
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from main import App
from game import Game

class TestAILogging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            pygame.init()
            cls.pygame_initialized = True
        except Exception:
            cls.pygame_initialized = False

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, 'pygame_initialized', False):
            pygame.quit()

    def test_ai_log_includes_player_and_agent_name(self):
        # Create real Game and dummy GUI
        game = Game()
        gui_mock = MagicMock()
        app = App(game, gui_mock)

        # Set both players to AI ids (use definitions 1 and 1 for simplicity)
        app.black_player_id = 1
        app.white_player_id = 1
        app.game.set_players(app.black_player_id, app.white_player_id)

        # Prepare game state for AI move
        # Set turn to black (-1) and stub valid moves and place_stone
        app.game.turn = -1
        app.game.get_valid_moves = MagicMock(return_value=[(2, 3)])
        def place_stone(row, col):
            # simulate successful placement
            return True
        app.game.place_stone = MagicMock(side_effect=place_stone)

        # Capture logs
        logger = logging.getLogger()
        old_level = logger.level
        logger.setLevel(logging.INFO)
        log_capture = []
        class ListHandler(logging.Handler):
            def emit(self, record):
                log_capture.append(self.format(record))
        handler = ListHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)

        try:
            # apply AI move
            app._apply_ai_move((2, 3))
        finally:
            logger.removeHandler(handler)
            logger.setLevel(old_level)

        # Check that a log was recorded and contains color and agent name
        self.assertTrue(any('Black' in msg and 'First' in msg for msg in log_capture), f"Logs: {log_capture}")

if __name__ == '__main__':
    unittest.main()
