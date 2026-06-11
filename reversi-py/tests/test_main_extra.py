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
        app.ai_queue.put(((3, 3), 0))
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

        app._run_ai_agent(agent, 0)
        # queue should have a (None, generation) tuple
        val = app.ai_queue.get_nowait()
        assert val == (None, 0)
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


def test_app_has_ai_generation_attribute():
    """App は _ai_generation 属性（初期値 0）を持つ"""
    app, _, _, patcher = make_app()
    try:
        assert hasattr(app, "_ai_generation")
        assert app._ai_generation == 0
    finally:
        patcher.stop()


def test_invalidate_ai_thinking_increments_generation():
    """_invalidate_ai_thinking() を呼ぶと _ai_generation が増加する"""
    app, _, _, patcher = make_app()
    try:
        app.is_ai_thinking = True
        app._invalidate_ai_thinking()
        assert app._ai_generation == 1
        assert app.is_ai_thinking is False
    finally:
        patcher.stop()


def test_invalidate_ai_thinking_drains_queue():
    """_invalidate_ai_thinking() はキューに積まれた古い結果を捨てる"""
    app, _, _, patcher = make_app()
    try:
        app.ai_queue.put(((3, 2), 0))
        app._invalidate_ai_thinking()
        assert app.ai_queue.empty()
    finally:
        patcher.stop()


def test_stale_ai_result_is_discarded():
    """世代が一致しない AI 結果は盤面に適用されない"""
    app, mock_game, _, patcher = make_app()
    try:
        app.game_started = True
        app.game.game_over = False
        app.is_ai_thinking = True
        app._ai_generation = 1  # 現在の世代は 1
        app.ai_queue.put(((3, 2), 0))  # 古い世代 0 の結果

        with patch.object(app, "_apply_ai_move") as mock_apply:
            app._update_state(None)
        mock_apply.assert_not_called()
        assert app.is_ai_thinking is False  # フラグはリセットされる
    finally:
        patcher.stop()


def test_fresh_ai_result_is_applied():
    """世代が一致する AI 結果は盤面に適用される"""
    app, mock_game, _, patcher = make_app()
    try:
        app.game_started = True
        app.game.game_over = False
        app.is_ai_thinking = True
        app._ai_generation = 1
        app.ai_queue.put(((3, 2), 1))  # 現在の世代と一致

        with patch.object(app, "_apply_ai_move") as mock_apply:
            app._update_state(None)
        mock_apply.assert_called_once_with((3, 2))
    finally:
        patcher.stop()


def test_player_change_mid_game_invalidates_ai():
    """ゲーム中にプレイヤー設定を変更すると AI 思考が無効化される"""
    app, mock_game, mock_gui, patcher = make_app()
    try:
        app.game_started = True
        app.game.game_over = False
        app.black_player_id = 0
        app.is_ai_thinking = True

        # 黒を RandomAgent (id=2) に変更するクリックをシミュレート
        mock_gui.get_clicked_radio_button.return_value = (-1, 2)
        app._handle_player_settings_click((0, 0))

        assert app._ai_generation == 1
        assert app.is_ai_thinking is False
    finally:
        patcher.stop()


def test_player_change_before_start_does_not_invalidate():
    """ゲーム開始前のプレイヤー設定変更では _ai_generation が変化しない"""
    app, mock_game, mock_gui, patcher = make_app()
    try:
        app.game_started = False
        app.black_player_id = 0
        mock_gui.get_clicked_radio_button.return_value = (-1, 2)
        app._handle_player_settings_click((0, 0))
        assert app._ai_generation == 0
    finally:
        patcher.stop()


def test_run_ai_agent_puts_generation_in_queue():
    """_run_ai_agent は (move, generation) のタプルをキューに入れる"""
    app, _, _, patcher = make_app()
    try:
        app._ai_generation = 3
        mock_agent = MagicMock()
        mock_agent.play.return_value = (2, 5)

        app._run_ai_agent(mock_agent, 3)

        result = app.ai_queue.get_nowait()
        assert result == ((2, 5), 3)
    finally:
        patcher.stop()


def test_handle_player_settings_click_early_return_when_clicked_player_none():
    """clicked_player が None のとき _handle_player_settings_click は早期リターン"""
    app, mock_game, mock_gui, patcher = make_app()
    try:
        # 初期化後に set_players の呼び出しをリセット
        mock_game.set_players.reset_mock()

        # プレイヤー ID を 1, 1 に変更して初期化をクリア
        app.black_player_id = 1
        app.white_player_id = 1

        mock_gui.get_clicked_radio_button.return_value = (None, 2)
        initial_black_id = app.black_player_id
        initial_white_id = app.white_player_id

        app._handle_player_settings_click((400, 400))

        # プレイヤー ID が変更されていないことを確認
        assert app.black_player_id == initial_black_id
        assert app.white_player_id == initial_white_id
        # set_players が呼ばれていないことを確認
        mock_game.set_players.assert_not_called()
    finally:
        patcher.stop()


def test_handle_click_in_game_calls_player_settings_click():
    """ゲーム中にプレイヤー設定がクリックされた場合、_handle_player_settings_click が呼ばれる"""
    app, mock_game, mock_gui, patcher = make_app()
    try:
        # ゲーム中の設定：プレイヤー設定クリック
        # get_clicked_radio_button は (-1, "api_first") を返す（黒プレイヤー設定）
        mock_gui.get_clicked_radio_button.return_value = (-1, "api_first")
        mock_gui.is_restart_button_clicked.return_value = False
        mock_gui.is_reset_button_clicked.return_value = False
        mock_gui.is_quit_button_clicked.return_value = False
        mock_gui.is_undo_button_clicked.return_value = False

        with patch.object(app, '_handle_player_settings_click') as mock_handle:
            app._handle_click_in_game((400, 400))
            # _handle_player_settings_click が呼ばれたことを確認
            mock_handle.assert_called_once_with((400, 400))
    finally:
        patcher.stop()
