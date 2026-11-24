"""main.py の終局後解説モード・任意局面打ち直し機能の単体テスト。"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pygame

import main
from analysis.models import GameAnalysis, MoveAnalysis
from game import Game
from gui import GameGUI


def _empty_board() -> list[list[int]]:
    return [[0] * 8 for _ in range(8)]


def _make_sample_analysis(history: list) -> GameAnalysis:
    ma1 = MoveAnalysis(
        move_index=0,
        move_number=1,
        turn=history[0][1],
        board_before=_empty_board(),
        played_move=history[0][0],
        best_move=(2, 3),
        played_score=-30.0,
        best_score=20.0,
        score_loss=50.0,
        is_exact=False,
        played_disc_diff=None,
        best_disc_diff=None,
        refutation_move=(2, 2),
        pv=[(2, 3), (2, 2)],
        is_decisive=True,
        reason_codes=["general_positional"],
        summary="summary-1",
        explanation="detail-1",
    )
    return GameAnalysis(
        loser=1,
        winner=-1,
        final_black=40,
        final_white=24,
        total_moves=len(history),
        key_mistakes=[ma1],
        moves_by_index={0: ma1},
        headline="白は第1手で勝ちを逃し、負けが決定しました",
        missed_win_move_index=0,
        loss_sealed_move_index=0,
    )


def _make_real_game_with_history(moves_count: int = 4) -> Game:
    g = Game(board_size=8)
    for _ in range(moves_count):
        valid = g.get_valid_moves()
        if valid:
            r, c = valid[0]
            g.place_stone(r, c)
        g.switch_turn()
        g.check_game_over()
    return g


def _make_app_with_real_game(moves_count: int = 4):
    pygame.init()
    game = _make_real_game_with_history(moves_count)
    mock_gui = MagicMock(spec=GameGUI)
    mock_gui._calculate_player_settings_top.return_value = 400
    mock_gui.is_restart_button_clicked.return_value = False
    mock_gui.is_reset_button_clicked.return_value = False
    mock_gui.is_quit_button_clicked.return_value = False
    mock_gui.is_analyze_button_clicked.return_value = False
    mock_gui.get_clicked_radio_button.return_value = (None, None)
    mock_gui.get_clicked_analysis_button.return_value = None
    mock_gui.get_clicked_analysis_nav.return_value = (None, None)
    mock_gui.get_clicked_resume_pending_button.return_value = None
    mock_gui.is_analysis_panel_point.return_value = False
    patcher = patch("pygame.display.flip")
    patcher.start()
    app = main.App(game, mock_gui)
    app.game_started = True
    game.game_over = True
    return app, game, mock_gui, patcher


def test_start_analysis_worker_queue_and_cache() -> None:
    app, game, mock_gui, patcher = _make_app_with_real_game(4)
    try:
        # 履歴空なら起動しない
        saved_hist = game.history
        game.history = []
        app._start_analysis()
        assert app.is_analyzing is False
        game.history = saved_hist

        # クリックで解析スレッド起動
        mock_gui.is_analyze_button_clicked.return_value = True
        with patch("main.threading.Thread") as mock_thread:
            app._handle_click_game_over((10, 10))
        assert app.is_analyzing is True
        mock_thread.return_value.start.assert_called_once()

        # すでに is_analyzing 中なら二重起動しない
        with patch("main.threading.Thread") as mock_thread2:
            app._handle_click_game_over((10, 10))
        mock_thread2.assert_not_called()

        # 別世代の結果・エラー・進捗の処理
        sample = _make_sample_analysis(game.history)
        app.analysis_queue.put(("done", sample, 999))  # 古い世代 → 無視
        app._poll_analysis_queue()
        assert app.analysis_result is None

        app.analysis_queue.put(("progress", (1, 2), app._analysis_generation))
        app._poll_analysis_queue()
        assert app.analysis_progress == (1, 2)

        app.analysis_queue.put(("error", "boom", app._analysis_generation))
        app._poll_analysis_queue()
        assert app.is_analyzing is False

        app.is_analyzing = True
        app.analysis_queue.put(("done", sample, app._analysis_generation))
        app._poll_analysis_queue()
        assert app.is_analyzing is False
        assert app.analysis_mode is True
        assert app.analysis_result is sample

        # 閉じて再クリック時はキャッシュ即座利用
        app.analysis_mode = False
        app._start_analysis()
        assert app.analysis_mode is True
    finally:
        patcher.stop()


def test_run_analysis_worker_success_and_error() -> None:
    app, game, _, patcher = _make_app_with_real_game(2)
    try:
        sample = _make_sample_analysis(game.history)
        with patch("main.analyze_game", return_value=sample) as mock_az:
            def fake_analyze(history, board_size, on_progress):
                on_progress(1, 1)
                return sample
            mock_az.side_effect = fake_analyze
            app._run_analysis_worker(list(game.history), 8, 0)

        ev1 = app.analysis_queue.get_nowait()
        ev2 = app.analysis_queue.get_nowait()
        assert ev1 == ("progress", (1, 1), 0)
        assert ev2 == ("done", sample, 0)

        with patch("main.analyze_game", side_effect=RuntimeError("fail")):
            app._run_analysis_worker(list(game.history), 8, 1)
        ev_err = app.analysis_queue.get_nowait()
        assert ev_err[0] == "error" and ev_err[2] == 1
    finally:
        patcher.stop()


def test_analysis_navigation_pv_keys_scroll_and_render() -> None:
    app, game, mock_gui, patcher = _make_app_with_real_game(4)
    try:
        # 結果なし/履歴空の防御分岐
        app._enter_analysis_mode()
        app._step_analysis_mistake(1)
        app._advance_analysis_pv()
        saved_h = game.history
        game.history = []
        app._set_analysis_move_index(0)
        game.history = saved_h

        # key_mistakes が空のケース
        sample_empty = GameAnalysis(
            loser=0,
            winner=0,
            final_black=32,
            final_white=32,
            total_moves=len(game.history),
            key_mistakes=[],
            moves_by_index={},
            headline="ok",
        )
        app.analysis_result = sample_empty
        app._enter_analysis_mode()
        assert app.analysis_move_index == len(game.history) - 1
        app._step_analysis_mistake(1)
        app._advance_analysis_pv()

        # key_mistakes あり + move_index が悪手外から悪手ジャンプ
        sample = _make_sample_analysis(game.history)
        app.analysis_result = sample
        app._enter_analysis_mode()
        assert app.analysis_move_index == 0

        # 1 手進める (index=1 は moves_by_index にない → board_before は history[0][2])
        mock_gui.get_clicked_analysis_nav.return_value = ("step_next", None)
        app._handle_click_game_over((0, 0))
        assert app.analysis_move_index == 1

        # 描画（非解析対象手 idx=1、さらに idx=0 も確認）
        app._render_game_over(400)
        mock_gui.draw_analysis_board.assert_called()
        mock_gui.draw_analysis_buttons.assert_called()
        mock_gui.draw_analysis_panel.assert_called()

        # 非解析対象手 idx=0 相当（ma=None, idx==0）
        app.analysis_result = sample_empty
        app._set_analysis_move_index(0)
        app._render_game_over(400)

        # 戻して step_prev / jump_move / toggle_pv
        app.analysis_result = sample
        mock_gui.get_clicked_analysis_nav.return_value = ("jump_move", 2)
        app._handle_click_game_over((0, 0))
        assert app.analysis_move_index == 2

        # key_mistakes 外の idx=2 から next_mistake
        mock_gui.get_clicked_analysis_button.return_value = "next_mistake"
        app._handle_click_game_over((0, 0))
        assert app.analysis_move_index == 0

        mock_gui.get_clicked_analysis_button.return_value = "prev_mistake"
        app._handle_click_game_over((0, 0))
        assert app.analysis_move_index == 0

        mock_gui.get_clicked_analysis_button.return_value = None
        mock_gui.get_clicked_analysis_nav.return_value = ("step_prev", None)
        app._handle_click_game_over((0, 0))
        mock_gui.get_clicked_analysis_nav.return_value = ("toggle_pv", None)
        app._handle_click_game_over((0, 0))
        assert app.analysis_pv_step == 1
        # PV コマ送り状態での描画（有効な初期盤面由来の PV を使う）
        board_0 = Game(8).get_board()
        ma_valid = MoveAnalysis(
            move_index=0,
            move_number=1,
            turn=-1,
            board_before=board_0,
            played_move=(2, 3),
            best_move=(2, 3),
            played_score=0.0,
            best_score=0.0,
            score_loss=0.0,
            is_exact=False,
            played_disc_diff=None,
            best_disc_diff=None,
            refutation_move=(2, 2),
            pv=[(2, 3), (2, 2)],
            is_decisive=False,
            reason_codes=[],
            summary="s",
            explanation="e",
        )
        app.analysis_result = GameAnalysis(
            loser=1,
            winner=-1,
            final_black=33,
            final_white=31,
            total_moves=len(game.history),
            key_mistakes=[ma_valid],
            moves_by_index={0: ma_valid},
            headline="h",
        )
        app.analysis_pv_step = 2
        app._render_game_over(400)

        # PV ステップ内でパス（相手手番になる）ケース
        # 手番不一致時に cur_turn = -cur_turn へ入るケースをカバー
        app.analysis_move_index = 0
        app.analysis_pv_step = 1
        ma_flip = MoveAnalysis(
            move_index=0,
            move_number=1,
            turn=1,  # 盤面は黒番のみ (2,3) が合法なので cur_turn=-cur_turn が通る
            board_before=board_0,
            played_move=(2, 3),
            best_move=(2, 3),
            played_score=0.0,
            best_score=0.0,
            score_loss=0.0,
            is_exact=False,
            played_disc_diff=None,
            best_disc_diff=None,
            refutation_move=None,
            pv=[(2, 3)],
            is_decisive=False,
            reason_codes=[],
            summary="s",
            explanation="e",
        )
        # app.game.history[0] の turn も 1 にしておく（_get_analysis_board_view は history[idx][1] を使うため！）
        orig_h0 = game.history[0]
        game.history[0] = (orig_h0[0], 1, orig_h0[2])
        app.analysis_result = GameAnalysis(
            loser=1,
            winner=-1,
            final_black=33,
            final_white=31,
            total_moves=len(game.history),
            key_mistakes=[ma_flip],
            moves_by_index={0: ma_flip},
            headline="h",
        )
        app._render_game_over(400)
        game.history[0] = orig_h0

        # マウスホイール / ボタン 4・5 / 0 デルタを網羅
        ev_b4 = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 4, "pos": (200, 450)})
        ev_b5 = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 5, "pos": (200, 450)})
        ev_mw0 = pygame.event.Event(pygame.MOUSEWHEEL, {"y": 0})
        ev_mw1 = pygame.event.Event(pygame.MOUSEWHEEL, {"y": 1})
        mock_gui.is_analysis_panel_point.return_value = True
        with patch("pygame.event.get", return_value=[ev_b4, ev_b5, ev_mw0, ev_mw1]), patch(
            "main.pygame.mouse.get_pos", return_value=(200, 450)
        ):
            app.analysis_mode = True
            app._handle_events()

        # キーイベント（_handle_events 経由も含む）
        for key in (
            pygame.K_RIGHT,
            pygame.K_LEFT,
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_SPACE,
            pygame.K_ESCAPE,
        ):
            ev = pygame.event.Event(pygame.KEYDOWN, {"key": key})
            with patch("pygame.event.get", return_value=[ev]):
                app.analysis_mode = True
                app._handle_events()
        assert app.analysis_mode is False

        # 解説パネル上のホイールスクロール
        app.analysis_mode = True
        mock_gui.is_analysis_panel_point.return_value = True
        mock_gui.scroll_analysis_panel.reset_mock()
        with patch("main.pygame.mouse.get_pos", return_value=(200, 450)):
            app._handle_player_settings_scroll(1)
        mock_gui.scroll_analysis_panel.assert_called_once()
        mock_gui.is_analysis_panel_point.return_value = False
        mock_gui.scroll_analysis_panel.reset_mock()
        with patch("main.pygame.mouse.get_pos", return_value=(200, 450)):
            app._handle_player_settings_scroll(1)
        mock_gui.scroll_analysis_panel.assert_not_called()

        # 閉じるボタン
        mock_gui.get_clicked_analysis_button.return_value = "close"
        app._handle_click_game_over((0, 0))
        assert app.analysis_mode is False

        # 解析中メッセージ描画
        app.is_analyzing = True
        app.analysis_progress = (2, 5)
        app._render_game_over(400)
        mock_gui.draw_analyze_button.assert_called_with(game_over=True)

        # game_history が空になった状態で _handle_analysis_click
        game.history = []
        app.analysis_mode = True
        mock_gui.get_clicked_analysis_button.return_value = None
        app._handle_click_game_over((0, 0))
    finally:
        patcher.stop()


def test_resume_from_analysis_move_player_selection_and_branch() -> None:
    """任意局面からの打ち直し準備状態・プレイヤー変更・再開・戻る・リセット・履歴分岐を検証。"""
    app, game, mock_gui, patcher = _make_app_with_real_game(4)
    try:
        # 範囲外は無視
        app._resume_from_analysis_move(-1)
        app._resume_from_analysis_move(999)

        # AI vs AI の設定にしておく（黒=API First, 白=API Random）
        app.black_player_id = 1
        app.white_player_id = 2
        game.set_players(1, 2)
        app.analysis_result = _make_sample_analysis(game.history)
        app.analysis_mode = True
        app.analysis_move_index = 0  # 第1手（黒番）

        # 「ここから打つ」ボタンクリック → resume_pending に入り、AI が即起動しない
        mock_gui.get_clicked_analysis_button.return_value = "resume"
        app._handle_click_game_over((0, 0))

        assert app.analysis_mode is False
        assert app.resume_pending is True
        assert game.game_over is False
        assert app.game_started is True
        assert game.turn == -1
        assert game.history_index == -1
        assert app.analysis_result is not None
        assert game.get_message() == "第1手から打ち直し"
        assert app.resume_notices

        # AI が勝手には起動しない
        with patch("main.threading.Thread") as mock_thread:
            app._update_state(None)
        mock_thread.assert_not_called()
        assert app.is_ai_thinking is False

        # 「解説へ戻る」で再解析なしに解説画面へ戻れる
        mock_gui.get_clicked_resume_pending_button.return_value = "back_to_analysis"
        app._update_state((10, 10))
        assert app.resume_pending is False
        assert app.analysis_mode is True
        assert game.game_over is True

        # 再び第2手（白番）から打ち直し準備へ
        app.analysis_move_index = 1
        app._resume_from_analysis_move(1)
        assert app.resume_pending is True
        assert game.turn == 1

        # 打ち直し準備中にプレイヤー設定ラジオボタンで黒=人間(0)、白=API(Gain)(3) へ変更できる
        mock_gui.get_clicked_resume_pending_button.return_value = None
        mock_gui.get_clicked_radio_button.return_value = (-1, 0)
        app._update_state((50, 450))
        mock_gui.get_clicked_radio_button.return_value = (1, 3)
        app._update_state((300, 450))
        assert app.black_player_id == 0
        assert app.white_player_id == 3

        # 「対局再開」で確定 → 白 AI の手番が即座に開始する
        mock_gui.get_clicked_resume_pending_button.return_value = "confirm_resume"
        with patch("main.threading.Thread") as mock_thread:
            app._update_state((10, 10))
        assert app.resume_pending is False
        assert app.analysis_result is None
        assert app.is_ai_thinking is True
        mock_thread.return_value.start.assert_called_once()
        assert app.white_player_id == 3
        app._invalidate_ai_thinking()

        # 第1手（黒・人間番）で打ち直し準備 → 合法手セル直接クリックで即再開＋着手＋履歴分岐
        game = _make_real_game_with_history(4)
        app.game = game
        app.black_player_id = 0
        app.white_player_id = 2
        game.set_players(0, 2)
        app.analysis_result = None
        app._resume_from_analysis_move(0)
        assert app.resume_pending is True

        # 不合法手セル・盤面外なら準備状態のまま
        mock_gui.get_clicked_resume_pending_button.return_value = None
        mock_gui.get_clicked_radio_button.return_value = (None, None)
        mock_gui.get_clicked_cell.return_value = (0, 0)
        app._update_state((10, 10))
        assert app.resume_pending is True

        # 合法手 (3, 2) をクリック → 自動再開＋着手して履歴が分岐
        mock_gui.get_clicked_cell.return_value = (3, 2)
        app._update_state((100, 100))
        assert app.resume_pending is False
        assert len(game.history) == 1
        assert game.history[0][0] == (3, 2)

        # resume_pending 中の reset / quit と、history 空での _back_to_analysis_from_resume
        app._resume_from_analysis_move(0)
        mock_gui.get_clicked_resume_pending_button.return_value = "reset"
        app._update_state((0, 0))
        assert app.resume_pending is False
        assert app.game_started is False
        assert app.black_player_id == 0 and app.white_player_id == 0

        app.game_started = True
        game.game_over = False
        app.resume_pending = True
        mock_gui.get_clicked_resume_pending_button.return_value = "quit"
        app._update_state((0, 0))
        assert app.running is False

        game.history = []
        app._back_to_analysis_from_resume()
        assert app.analysis_mode is True
    finally:
        patcher.stop()


def test_invalidate_analysis_drains_queue_and_resets_on_restart_reset() -> None:
    app, _, mock_gui, patcher = _make_app_with_real_game(2)
    try:
        app.analysis_queue.put(("progress", (1, 1), 0))
        app.is_analyzing = True
        app.analysis_mode = True
        mock_gui.is_restart_button_clicked.return_value = True
        app._handle_click_game_over((0, 0))
        assert app.analysis_queue.empty()
        assert app.is_analyzing is False
        assert app.analysis_mode is False
    finally:
        patcher.stop()


def test_real_gui_analysis_rendering_and_hit_testing(monkeypatch) -> None:
    """実物の GameGUI で解説画面描画・クリック判定・スクロールがエラーなく動作する。"""
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    game = _make_real_game_with_history(6)
    font_mock = MagicMock()
    font_mock.render.return_value = pygame.Surface((40, 16))
    font_mock.get_height.return_value = 16
    font_mock.size.side_effect = lambda t: (len(t) * 8, 16)

    with patch("gui.GameGUI._load_font", return_value=font_mock), patch(
        "pygame.display.flip"
    ):
        gui = GameGUI(allow_width_shrink=True)
        app = main.App(game, gui)
        app.game_started = True
        game.game_over = True

        # 通常終局画面（解説ボタン含む）
        app._render()
        # 解説モード画面（詳細解説あり / なし 両方）
        app.analysis_result = _make_sample_analysis(game.history)
        app._enter_analysis_mode()
        app._render()
        app._set_analysis_move_index(1)
        app._render()

        # クリック判定が動作する
        specs = gui._get_analysis_button_specs()
        for expected_action, _, rect in specs:
            assert gui.get_clicked_analysis_button(rect.center) == expected_action
        assert gui.get_clicked_analysis_button((-10, -10)) is None

        panel_top = gui._calculate_player_settings_top()
        panel_rect = gui._analysis_panel_rect(panel_top)
        nav_rects = gui._analysis_nav_rects(panel_rect, has_pv=True)
        assert gui.get_clicked_analysis_nav(nav_rects["step_prev"].center, panel_top, 6, True) == ("step_prev", None)
        assert gui.get_clicked_analysis_nav(nav_rects["step_next"].center, panel_top, 6, True) == ("step_next", None)
        assert gui.get_clicked_analysis_nav(nav_rects["toggle_pv"].center, panel_top, 6, True) == ("toggle_pv", None)
        tl_act, tl_idx = gui.get_clicked_analysis_nav(nav_rects["timeline"].center, panel_top, 6, True)
        assert tl_act == "jump_move" and tl_idx is not None
        assert gui.is_analysis_panel_point(panel_rect.center, panel_top) is True
        gui.scroll_analysis_panel(22, panel_top)

        # 打ち直し準備状態（継続プレイヤー選択画面）の描画とボタン判定
        app._resume_from_analysis_move(0)
        app._render()
        rp_specs = gui._get_resume_pending_button_specs()
        for expected_action, _, rect in rp_specs:
            assert gui.get_clicked_resume_pending_button(rect.center) == expected_action
        assert gui.get_clicked_resume_pending_button((-10, -10)) is None










def test_resume_sealed_notice() -> None:
    """完全読み切りで人間側の勝ちが無いときだけ、負け確定・引き分けまでの文言を返す。"""
    from dataclasses import replace

    app, game, _, patcher = _make_app_with_real_game(4)
    try:
        ma = replace(
            _make_sample_analysis(game.history).moves_by_index[0],
            turn=1,
            is_exact=True,
        )
        # 手番 = 人間側（白）の最善が -4 → 白の 4 石差負け確定
        assert app._resume_sealed_notice(replace(ma, best_disc_diff=-4), 1, 1) == (
            "完全読み切り: 相手が最善なら白に勝ち目なし\n（最善でも 4 石差負け）"
        )
        # 最善 0 → 引き分けまで
        assert app._resume_sealed_notice(replace(ma, best_disc_diff=0), 1, 1) == (
            "完全読み切り: 相手が最善なら白に勝ち目なし\n（最善でも引き分け）"
        )
        # 最善が勝ち → 表示しない
        assert app._resume_sealed_notice(replace(ma, best_disc_diff=2), 1, 1) is None
        # 手番が相手（黒）の場合は符号を反転して人間側（白）から見る
        black_ma = replace(ma, turn=-1, best_disc_diff=6)
        assert app._resume_sealed_notice(black_ma, -1, 1) == (
            "完全読み切り: 相手が最善なら白に勝ち目なし\n（最善でも 6 石差負け）"
        )
        # 読み切りでない・解析結果なしで空きが多い → 表示しない
        assert app._resume_sealed_notice(replace(ma, is_exact=False), 1, 1) is None
        assert app._resume_sealed_notice(None, -1, -1) is None

        # 解析結果なしでも、終盤なら読み切って表示する
        with patch("main.solve_position_disc_diff", return_value=-10) as mock_solve:
            assert app._resume_sealed_notice(None, -1, -1) == (
                "完全読み切り: 相手が最善なら黒に勝ち目なし\n（最善でも 10 石差負け）"
            )
        mock_solve.assert_called_once_with(game.board.board, -1)
    finally:
        patcher.stop()


def test_resume_shows_sealed_notice_from_real_endgame() -> None:
    """解析結果が無くても、終盤の局面から打ち直すと実際に読み切って結果を表示する。"""
    from analysis.game_analyzer import solve_position_disc_diff

    app, game, _, patcher = _make_app_with_real_game(60)
    try:
        app.black_player_id = 1
        app.white_player_id = 2
        game.set_players(1, 2)
        app.analysis_result = None
        move_index = len(game.history) - 4
        human_side = app._resume_human_side(game.history[move_index][1])
        app._resume_from_analysis_move(move_index)

        mover_diff = solve_position_disc_diff(game.board.board, game.turn)
        assert mover_diff is not None
        human_diff = mover_diff if human_side == game.turn else -mover_diff
        sealed = [n for n in app.resume_notices if n.startswith("完全読み切り")]
        if human_diff > 0:
            assert sealed == []
        else:
            assert len(sealed) == 1
    finally:
        patcher.stop()


def test_draw_resume_notices_renders_on_real_gui(monkeypatch) -> None:
    """実物の GameGUI で補足表示が描画でき、長い行は盤面幅に縮小される。"""
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    font_mock = MagicMock()
    # 2 行目は盤面幅より広い文字列として描画させ、縮小処理を通す
    font_mock.render.side_effect = lambda text, *_: pygame.Surface(
        (len(text) * 16, 16)
    )
    font_mock.get_height.return_value = 16
    font_mock.size.side_effect = lambda t: (len(t) * 8, 16)
    with patch("gui.GameGUI._load_font", return_value=font_mock):
        gui = GameGUI(allow_width_shrink=True)
        gui.draw_resume_notices([])
        font_mock.render.reset_mock()
        with patch("gui.pygame.transform.smoothscale", wraps=pygame.transform.smoothscale) as scale:
            gui.draw_resume_notices(["短い行", "とても長い行" * 20])
        assert font_mock.render.call_count == 2
        scale.assert_called_once()


def test_resume_notice_band_avoids_human_moves(monkeypatch) -> None:
    """人間の合法手が上端の帯に隠れる場合だけ、帯を盤面の下端に置く。"""
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    font_mock = MagicMock()
    font_mock.render.return_value = pygame.Surface((40, 16))
    font_mock.get_height.return_value = 16
    font_mock.size.side_effect = lambda t: (len(t) * 8, 16)
    with patch("gui.GameGUI._load_font", return_value=font_mock):
        gui = GameGUI(allow_width_shrink=True)
        rect = gui._calculate_board_rect()
        band_height = 16 * 3 + 12
        # 隠す手が無い / 上端に無い → 上端
        assert gui._resume_notice_band_top(rect, band_height, []) == rect.top
        assert gui._resume_notice_band_top(rect, band_height, [(4, 4)]) == rect.top
        # 上端に隠れる手があり下端には無い → 下端
        assert gui._resume_notice_band_top(rect, band_height, [(0, 3)]) == (
            rect.bottom - band_height
        )
        # 上端・下端の両方に手がある → 上端のまま
        assert gui._resume_notice_band_top(rect, band_height, [(0, 3), (7, 3)]) == rect.top
        gui.draw_resume_notices(["行"], [(0, 3)])


def test_resume_overrides_loser_for_one_move_and_restores_on_back() -> None:
    """「ここから打つ」で負けた側（白）を 1 手だけ人間にし、画面の設定は変えない。解説へ戻ると元に戻る。"""
    app, game, mock_gui, patcher = _make_app_with_real_game(4)
    try:
        app.black_player_id = 1
        app.white_player_id = 2
        game.set_players(1, 2)
        app.analysis_result = _make_sample_analysis(game.history)  # loser=1（白）

        app._resume_from_analysis_move(0)  # 第1手（黒・AI の手番）

        # 画面のプレイヤー設定（ラジオボタン）はそのまま、白のエージェントだけ一時的に人間
        assert (app.black_player_id, app.white_player_id) == (1, 2)
        assert game.agent_ids == {-1: 1, 1: 2}
        assert game.agents[1] is None
        assert game.agents[-1] is not None
        assert app._resume_human_override == 1
        assert game.get_message() == "第1手から打ち直し"
        assert app.resume_notices[0] == "白は 1 手だけ人間が打ちます（以後は画面の設定で進行）"
        assert "推奨手: D3" in app.resume_notices
        # 手番は AI（黒）なので「対局再開」で再開する案内になる
        assert app.resume_notices[-1] == "「対局再開」で AI の手番から再開"

        # 解説へ戻ると画面の設定どおりのエージェントに戻る
        mock_gui.get_clicked_resume_pending_button.return_value = "back_to_analysis"
        app._update_state((10, 10))
        assert game.agents[1] is not None
        assert app._resume_human_override is None
        assert app.resume_notices == []

        # 続けて打ち直しても上書きは 1 側だけ
        app._resume_from_analysis_move(1)
        app._resume_from_analysis_move(0)
        assert game.agents[1] is None and game.agents[-1] is not None
        app._back_to_analysis_from_resume()
        assert game.agents[1] is not None
    finally:
        patcher.stop()


def test_resume_keeps_players_when_loser_already_human() -> None:
    """負けた側がすでに人間なら上書きせず、手番が人間なら盤面クリックの案内を出す。"""
    app, game, _, patcher = _make_app_with_real_game(4)
    try:
        app.black_player_id = 1
        app.white_player_id = 0
        game.set_players(1, 0)
        app.analysis_result = _make_sample_analysis(game.history)  # loser=1（白）

        app._resume_from_analysis_move(1)  # 第2手（白・人間の手番）

        assert (app.black_player_id, app.white_player_id) == (1, 0)
        assert app._resume_human_override is None
        assert not any("人間が打ちます" in n for n in app.resume_notices)
        assert app.resume_notices[-1] == "盤面をクリックするか「対局再開」で再開"
    finally:
        patcher.stop()


def test_resume_draw_and_no_analysis_choose_human_side() -> None:
    """引き分けなら打ち直す手番の側、解析結果が無ければ最終盤面で負けた側を 1 手だけ人間にする。"""
    from dataclasses import replace

    app, game, _, patcher = _make_app_with_real_game(4)
    try:
        app.black_player_id = 1
        app.white_player_id = 2
        game.set_players(1, 2)
        app.analysis_result = replace(
            _make_sample_analysis(game.history), loser=0, winner=0
        )
        app._resume_from_analysis_move(1)  # 第2手は白の手番
        assert app._resume_human_override == 1
        app._back_to_analysis_from_resume()

        # 解析結果なしで最終盤面が同数（4 手後は 4 対 4）: 打ち直す手番の側
        app.analysis_result = None
        app._resume_from_analysis_move(0)  # 第1手は黒の手番
        assert app._resume_human_override == -1
        assert (app.black_player_id, app.white_player_id) == (1, 2)
    finally:
        patcher.stop()

    # 解析結果なし: 最終盤面の石数で負けた側を求める（5 手後は黒が多い → 白が負け）
    app, game, _, patcher = _make_app_with_real_game(5)
    try:
        app.black_player_id = 1
        app.white_player_id = 2
        game.set_players(1, 2)
        final_board = game.history[-1][2]
        black = sum(row.count(-1) for row in final_board)
        white = sum(row.count(1) for row in final_board)
        assert black > white
        app._resume_from_analysis_move(0)
        assert app._resume_human_override == 1
    finally:
        patcher.stop()


def test_human_move_after_resume_continues_with_configured_players() -> None:
    """人間が打ち直しの 1 手を打つと、以後は画面で設定されたプレイヤー（AI 同士）で進む。"""
    from dataclasses import replace

    app, game, mock_gui, patcher = _make_app_with_real_game(4)
    try:
        app.black_player_id = 1
        app.white_player_id = 2
        game.set_players(1, 2)
        app.analysis_result = replace(
            _make_sample_analysis(game.history), loser=-1, winner=1
        )
        app._resume_from_analysis_move(0)  # 黒（負けた側）が 1 手だけ人間
        assert game.agents[-1] is None
        assert app.resume_notices[-1] == "盤面をクリックするか「対局再開」で再開"

        mock_gui.get_clicked_cell.return_value = (3, 2)
        with patch("main.threading.Thread") as mock_thread:
            app._update_state((100, 100))
        # 人間の手が打たれ、黒は画面の設定（API First）に戻り、白（API Random）が考え始める
        assert app.resume_pending is False
        assert app.resume_notices == []
        assert game.history[-1][0] == (3, 2)
        assert len(game.history) == 1
        assert game.turn == 1
        assert app._resume_human_override is None
        assert game.agents[-1] is not None
        assert game.agents[1] is not None
        assert (app.black_player_id, app.white_player_id) == (1, 2)
        assert app.is_ai_thinking is True
        mock_thread.return_value.start.assert_called_once()
        app._invalidate_ai_thinking()
    finally:
        patcher.stop()


def test_resume_override_waits_for_ai_turn_and_follows_radio_changes() -> None:
    """AI の手番から再開しても人間化は維持され、人間が打つまで解除されない。ラジオでの選び直しに従う。"""
    app, game, mock_gui, patcher = _make_app_with_real_game(4)
    try:
        app.black_player_id = 1
        app.white_player_id = 2
        game.set_players(1, 2)
        app.analysis_result = _make_sample_analysis(game.history)  # loser=1（白）
        app._resume_from_analysis_move(0)  # 黒（AI）の手番、白が 1 手だけ人間

        # 黒側をラジオで選び直しても、白の人間化は維持される
        mock_gui.get_clicked_radio_button.return_value = (-1, 3)
        app._update_state((50, 450))
        assert app.black_player_id == 3
        assert game.agents[-1] is not None
        assert game.agents[1] is None
        assert app._resume_human_override == 1

        # 「対局再開」後も、白が打つまでは人間のまま
        mock_gui.get_clicked_radio_button.return_value = (None, None)
        mock_gui.get_clicked_resume_pending_button.return_value = "confirm_resume"
        with patch("main.threading.Thread"):
            app._update_state((10, 10))
        app._invalidate_ai_thinking()
        assert app._resume_human_override == 1
        assert game.agents[1] is None

        # 黒の手を進めて白（人間）が 1 手打つと、白は画面の設定（API Random）に戻る
        r, c = game.get_valid_moves()[0]
        game.place_stone(r, c)
        game.switch_turn()
        mock_gui.get_clicked_cell.return_value = game.get_valid_moves()[0]
        app._handle_human_move((100, 100))
        assert app._resume_human_override is None
        assert game.agents[1] is not None
        assert (app.black_player_id, app.white_player_id) == (3, 2)

        # 人間化中の側をラジオで選び直した場合は、その選択を優先して人間化を解除する
        app.analysis_result = _make_sample_analysis(game.history)
        app._resume_from_analysis_move(0)
        assert app._resume_human_override == 1
        mock_gui.get_clicked_resume_pending_button.return_value = None
        mock_gui.get_clicked_radio_button.return_value = (1, 4)
        app._update_state((300, 450))
        assert app._resume_human_override is None
        assert app.white_player_id == 4
        assert game.agents[1] is not None

        # リセットでも人間化は解除される
        mock_gui.get_clicked_radio_button.return_value = (None, None)
        app.analysis_result = _make_sample_analysis(game.history)
        app._resume_from_analysis_move(0)
        mock_gui.get_clicked_resume_pending_button.return_value = "reset"
        app._update_state((0, 0))
        assert app._resume_human_override is None
    finally:
        patcher.stop()
