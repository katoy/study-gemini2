# tests/test_main_logging_throttle.py
import unittest
from unittest.mock import MagicMock, patch

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import main
from main import App

class TestMainLoggingThrottle(unittest.TestCase):
    def test_throttling_filter_attached_in_run(self):
        # Create minimal game and gui mocks
        game_mock = MagicMock()
        gui_mock = MagicMock()
        # ensure set_players exists
        game_mock.set_players = MagicMock()

        app = App(game_mock, gui_mock)

        # Prevent pygame.quit/sys.exit side effects and intercept logging.getLogger
        mock_logger = MagicMock()
        with patch('main.logging.getLogger', return_value=mock_logger), \
             patch('main.pygame.quit'), \
             patch('main.sys.exit'):
            # Stop the main loop immediately
            app.running = False
            app.run()

        # Ensure addFilter was called (attached our ThrottlingFilter)
        mock_logger.addFilter.assert_called()
        # The argument should be an instance of main.ThrottlingFilter
        arg = mock_logger.addFilter.call_args[0][0]
        self.assertTrue(hasattr(arg, 'filter'))


if __name__ == '__main__':
    unittest.main()
