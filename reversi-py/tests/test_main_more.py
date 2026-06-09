import sys
import os
from unittest.mock import MagicMock
from unittest.mock import patch

# Ensure project root is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import pygame
import main
from game import Game
from gui import GameGUI


def make_app_simple():
    mock_game = MagicMock(spec=Game)
    mock_gui = MagicMock(spec=GameGUI)
    mock_game.turn = -1
    mock_game.game_over = False
    mock_game.agents = {-1: None, 1: None}
    mock_game.get_valid_moves = MagicMock(return_value=[(3, 3)])

    pygame.init()
    patcher = patch('pygame.display.flip')
    patcher.start()
    app = main.App(mock_game, mock_gui)
    return app, mock_game, mock_gui, patcher


def test_handle_ai_or_pass_ignores_when_ai_thinking():
    app, mock_game, mock_gui, patcher = make_app_simple()
    try:
        app.is_ai_thinking = True
        # should simply return and not start a thread
        app._handle_ai_or_pass()
        assert app.is_ai_thinking is True
        assert app.ai_thread is None
    finally:
        patcher.stop()


def test_run_ai_agent_puts_move_on_queue():
    app, mock_game, mock_gui, patcher = make_app_simple()
    try:
        agent = MagicMock()
        agent.play.return_value = (4, 4)
        app._run_ai_agent(agent)
        val = app.ai_queue.get_nowait()
        assert val == (4, 4)
    finally:
        patcher.stop()
