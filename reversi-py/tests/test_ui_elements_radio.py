# tests/test_ui_elements_radio.py
import unittest
from unittest.mock import patch, MagicMock
import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from ui_elements import RadioButton
from config.theme import Color

class TestRadioButtonDraw(unittest.TestCase):
    def test_non_selected_enabled_uses_unselected_color(self):
        rb = RadioButton((10, 10), 20, selected=False, enabled=True)
        with patch('ui_elements.pygame.draw') as mock_draw:
            surface = MagicMock()
            rb.draw(surface)
            # outline only
            self.assertEqual(mock_draw.circle.call_count, 1)
            # color is second positional argument of circle call
            args = mock_draw.circle.call_args[0]
            self.assertEqual(args[1], Color.RADIO_UNSELECTED)

    def test_selected_enabled_draws_inner_selected_color(self):
        rb = RadioButton((10, 10), 20, selected=True, enabled=True)
        with patch('ui_elements.pygame.draw') as mock_draw:
            surface = MagicMock()
            rb.draw(surface)
            # outline + inner
            self.assertEqual(mock_draw.circle.call_count, 2)
            outer_args = mock_draw.circle.call_args_list[0][0]
            inner_args = mock_draw.circle.call_args_list[1][0]
            self.assertEqual(outer_args[1], Color.DARK_BLUE)
            self.assertEqual(inner_args[1], Color.RADIO_SELECTED)

    def test_disabled_uses_disabled_color_for_outline_and_inner(self):
        rb = RadioButton((10, 10), 20, selected=True, enabled=False)
        with patch('ui_elements.pygame.draw') as mock_draw:
            surface = MagicMock()
            rb.draw(surface)
            # outline + inner
            self.assertEqual(mock_draw.circle.call_count, 2)
            outer_args = mock_draw.circle.call_args_list[0][0]
            inner_args = mock_draw.circle.call_args_list[1][0]
            self.assertEqual(outer_args[1], Color.DISABLED_TEXT)
            self.assertEqual(inner_args[1], Color.DISABLED_TEXT)

if __name__ == '__main__':
    unittest.main()
