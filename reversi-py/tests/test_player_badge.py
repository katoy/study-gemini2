# tests/test_player_badge.py
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
from config.theme import Screen, Color


class TestPlayerBadgeRendering(unittest.TestCase):
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

    def test_both_ai_badges_fit_and_render(self):
        # Minimal font mock that returns a surface-like object
        font_mock = MagicMock()
        surf = pygame.Surface((120, 24), pygame.SRCALPHA)
        # Use real Surface methods (get_width/get_height/get_rect) provided by pygame
        font_mock.render.return_value = surf
        font_mock.get_height.return_value = surf.get_height()

        test_agent_options = [(0, '人間'), (1, 'First'), (2, 'Random')]

        # Make display.set_mode return a real surface to allow drawing
        with patch('gui.GameGUI._load_font', return_value=font_mock), \
             patch('gui.get_agent_options', return_value=test_agent_options), \
             patch('gui.Path.exists', return_value=True), \
             patch('gui.pygame.display.set_mode', return_value=pygame.Surface((Screen.WIDTH, Screen.HEIGHT))):

            g = gui.GameGUI(screen_width=Screen.WIDTH, screen_height=Screen.HEIGHT)
            # Create a fake game with both agents present
            game = MagicMock()
            game.agents = {-1: object(), 1: object()}

            # call draw_player_settings; should not raise
            player_settings_top = g._calculate_player_settings_top()
            g.draw_player_settings(game, player_settings_top, enabled=True)

            # Recompute badge rects as the GUI would
            board_rect = g._calculate_board_rect()
            left_margin = board_rect.left
            white_player_label_x = g.screen_width // 2 + Screen.RADIO_BUTTON_MARGIN
            badge_y = player_settings_top + font_mock.get_height()

            label_black = gui.Label((left_margin + Screen.BADGE_MARGIN, badge_y + Screen.BADGE_Y_OFFSET), 'AI (Black)', font_mock, Color.BUTTON_TEXT)
            badge_rect_black = label_black.rect.inflate(Screen.BADGE_PADDING_X, Screen.BADGE_PADDING_Y)
            label_white = gui.Label((white_player_label_x + Screen.BADGE_MARGIN, badge_y + Screen.BADGE_Y_OFFSET), 'AI (White)', font_mock, Color.BUTTON_TEXT)
            badge_rect_white = label_white.rect.inflate(Screen.BADGE_PADDING_X, Screen.BADGE_PADDING_Y)

            # badges must be inside window horizontally
            self.assertGreaterEqual(badge_rect_black.left, 0)
            self.assertLessEqual(badge_rect_black.right, g.screen_width)
            self.assertGreaterEqual(badge_rect_white.left, 0)
            self.assertLessEqual(badge_rect_white.right, g.screen_width)


if __name__ == '__main__':
    unittest.main()
