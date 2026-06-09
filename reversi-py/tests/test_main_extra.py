import sys
import os
from unittest.mock import MagicMock
import queue
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


def make_app():
    mock_game = MagicMock(spec=Game)
    mock_gui = MagicMock(spec=GameGUI)

    # basic game mock defaults
    mock_game.turn = -1
    mock_game.game_over = False
    mock_game.agents = {-1: None, 1: None}
    mock_game.get_valid_moves = MagicMock(return_value=[(3, 3)])
    mock_game.place_stone = MagicMock(return_value=True)
    mock_game.switch_turn = MagicMock()
    mock_game.check_game_over = MagicMock()
    mock_game.replay = MagicMock()
    mock_game.history_index = 0

    mock_gui.get_clicked_cell = MagicMock(return_value=(3, 3))
    mock_gui._calculate_player_settings_top = MagicMock(return_value=400)

    pygame.init()
    # silence display.flip during tests
    patcher = patch('pygame.display.flip')
    patcher.start()

    app = main.App(mock_game, mock_gui)
    return app, mock_game, mock_gui, patcher


def test_update_state_applies_ai_move_from_queue():
    app, mock_game, mock_gui, patcher = make_app()
    try:
        app.is_ai_thinking = True
        app.ai_queue.put((3, 3))
        with patch.object(app, '_apply_ai_move') as mock_apply:
            app._update_state(None)
            mock_apply.assert_called_once_with((3, 3))
            assert app.is_ai_thinking is False
    finally:
        patcher.stop()


def test_update_state_queue_empty():
    app, mock_game, mock_gui, patcher = make_app()
    try:
        app.is_ai_thinking = True
        # ensure queue is empty
        with patch.object(app, '_apply_ai_move') as mock_apply:
            app._update_state(None)
            mock_apply.assert_not_called()
            assert app.is_ai_thinking is True
    finally:
        patcher.stop()


def test_handle_click_in_game_undo():
    app, mock_game, mock_gui, patcher = make_app()
    try:
        # configure for undo
        mock_gui.is_restart_button_clicked.return_value = False
        mock_gui.is_reset_button_clicked.return_value = False
        mock_gui.is_quit_button_clicked.return_value = False
        mock_gui.is_undo_button_clicked.return_value = True

        mock_game.history_index = 1
        # make current agent non-None so second replay happens
        mock_game.agents = {-1: MagicMock(), 1: None}

        app._handle_click_in_game((0, 0))
        # replay should be called twice (one for undo, one for AI agent present)
        assert mock_game.replay.call_count == 2
        mock_game.set_message.assert_called()
    finally:
        patcher.stop()


def test_run_ai_agent_exception_handling():
    app, mock_game, mock_gui, patcher = make_app()
    try:
        # agent that raises
        agent = MagicMock()
        def raise_err(game):
            raise RuntimeError('boom')
        agent.play.side_effect = raise_err

        app._run_ai_agent(agent)
        # queue should have a None put
        val = app.ai_queue.get_nowait()
        assert val is None
    finally:
        patcher.stop()


def test_apply_ai_move_success_and_invalid():
    app, mock_game, mock_gui, patcher = make_app()
    try:
        # success case
        mock_game.get_valid_moves.return_value = [(2, 2), (3, 3)]
        mock_game.place_stone.return_value = True
        app._apply_ai_move((3, 3))
        mock_game.place_stone.assert_called_with(3, 3)
        mock_game.set_message.assert_called_with("")
        mock_game.switch_turn.assert_called()
        mock_game.check_game_over.assert_called()

        # invalid case: move not in valid_moves and not None
        mock_game.get_valid_moves.return_value = [(0, 0)]
        # reset mocks
        mock_game.place_stone.reset_mock()
        app._apply_ai_move((9, 9))
        mock_game.place_stone.assert_not_called()
    finally:
        patcher.stop()


def test_handle_human_move_ignores_when_ai_thinking():
    app, mock_game, mock_gui, patcher = make_app()
    try:
        app.is_ai_thinking = True
        app._handle_human_move((10, 10))
        # when AI is thinking, get_clicked_cell should not be called
        mock_gui.get_clicked_cell.assert_not_called()
        mock_game.place_stone.assert_not_called()
    finally:
        patcher.stop()
