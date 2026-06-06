# tests/test_gui_width.py
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


class TestGameGUIWidth(unittest.TestCase):
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

    def test_allow_width_shrink_fits_ui(self):
        """When allow_width_shrink=True the computed/shrunk width must still
        leave room for buttons and player-setting columns (no clipping).
        """
        # simple font mock: render returns a surface-like object with width/height
        font_mock = MagicMock()
        surf = MagicMock()
        surf.get_width.return_value = 100
        surf.get_height.return_value = 24
        surf.get_rect.return_value = pygame.Rect(0, 0, 100, 24)
        font_mock.render.return_value = surf
        font_mock.get_height.return_value = 24

        test_agent_options = [(0, '人間'), (1, 'First'), (2, 'Random'), (3, 'Gain')]

        with patch('gui.GameGUI._load_font', return_value=font_mock), \
             patch('gui.get_agent_options', return_value=test_agent_options), \
             patch('gui.Path.exists', return_value=True), \
             patch('gui.pygame.display.set_mode') as mock_set_mode:

            mock_set_mode.return_value = MagicMock()

            g = gui.GameGUI(screen_width=Screen.WIDTH, screen_height=Screen.HEIGHT, allow_width_shrink=True)

            # All primary buttons should fit horizontally inside the window
            for args in [
                dict(is_start_button=True),
                dict(is_start_button=False, game_over=False, is_reset_button=False, is_quit_button=False),
                dict(is_start_button=False, game_over=False, is_reset_button=True, is_quit_button=False),
                dict(is_start_button=False, game_over=False, is_reset_button=False, is_quit_button=True),
                dict(is_start_button=False, game_over=False, is_reset_button=False, is_quit_button=False, is_settings_button=False, is_undo_button=True),
            ]:
                rect = g._calculate_button_rect(**args)
                self.assertGreaterEqual(rect.left, 0)
                self.assertLessEqual(rect.right, g.screen_width)

            # Player-setting right column should fit inside window with side padding
            board_rect = g._calculate_board_rect()
            left_margin = board_rect.left
            white_player_label_x = g.screen_width // 2 + Screen.RADIO_BUTTON_MARGIN
            # estimate widest label
            max_label_width = max(font_mock.render(name).get_width() for _, name in test_agent_options)
            label_right = white_player_label_x + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN + max_label_width
            self.assertLessEqual(label_right + Screen.SIDE_PADDING, g.screen_width)


if __name__ == '__main__':
    unittest.main()
