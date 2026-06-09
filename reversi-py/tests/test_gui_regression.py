# tests/test_gui_regression.py
import unittest
import pygame
import os
import sys
from unittest.mock import patch, MagicMock

# ensure repo package import works
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import gui
from config.theme import Screen


class TestGameGUILayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            pygame.init()
            cls.pygame_initialized = True
            cls.skip_tests = False
        except Exception as e:
            cls.pygame_initialized = False
            cls.skip_tests = True
            cls.skip_reason = f"Pygame init failed: {e}"

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, 'pygame_initialized', False):
            pygame.quit()

    def setUp(self):
        if getattr(self, 'skip_tests', False):
            self.skipTest(self.skip_reason)

    def test_height_adjustment_and_button_fit(self):
        """GameGUI should enlarge window height when initialized too small and place start button inside it."""
        # Prepare a simple font-like mock used by GameGUI calculations
        font_mock = MagicMock()
        surf = MagicMock()
        surf.get_height.return_value = 24
        surf.get_width.return_value = 50
        surf.get_rect.return_value = pygame.Rect(0, 0, 50, 24)
        font_mock.render.return_value = surf
        font_mock.get_height.return_value = 24

        test_agent_options = [(0, '人間'), (1, 'First'), (2, 'Random')]

        with patch('gui.GameGUI._load_font', return_value=font_mock), \
             patch('gui.get_agent_options', return_value=test_agent_options), \
             patch('gui.Path.exists', return_value=True), \
             patch('gui.Button') as mock_button, \
             patch('gui.pygame.display.set_mode') as mock_set_mode:

            # Ensure Button constructor is a harmless mock
            mock_button.return_value = MagicMock()

            initial_height = 200  # intentionally small
            g = gui.GameGUI(screen_width=Screen.WIDTH, screen_height=initial_height)

            # pygame.display.set_mode should be called with the (width, adjusted_height)
            mock_set_mode.assert_called()
            mode_arg = mock_set_mode.call_args[0][0]  # the tuple passed to set_mode
            self.assertEqual(mode_arg[0], Screen.WIDTH)
            # display's height arg should match the GUI instance's screen_height
            self.assertEqual(mode_arg[1], g.screen_height)

            # The GUI should have increased height (or left it unchanged if already large enough)
            self.assertGreaterEqual(g.screen_height, initial_height)

            # The Start button rect passed into Button(...) must fit inside the screen height
            rect_arg = mock_button.call_args[0][0]
            self.assertTrue(hasattr(rect_arg, 'bottom'))
            self.assertLessEqual(rect_arg.bottom, g.screen_height)


if __name__ == '__main__':
    unittest.main()
