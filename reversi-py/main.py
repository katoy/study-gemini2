# main.py
import pygame
import sys
import logging # ロギングを追加
from game import Game
from gui import GameGUI
from config.theme import Screen, Color
# from config.agents import get_agent_options # gui が内部で使うので不要かも

# --- gui.py に追加が必要なメソッド ---
# def get_clicked_radio_button(self, click_pos, player_settings_top):
#     """クリックされたラジオボタンの情報を返す (gui.py に実装)"""
#     # ... (実装は gui.py に記述) ...
#     # return player, agent_id or None, None
# ------------------------------------

def main():
    # --- 初期化 ---
    pygame.init()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # ロギング設定
    game = Game()
    gui = GameGUI()
    clock = pygame.time.Clock()

    # --- プレイヤー設定の初期値 ---
    black_player_id = 0
    white_player_id = 0
    game.set_players(black_player_id, white_player_id)

    # --- ゲーム状態 ---
    game_started = False
    running = True

    # --- アニメーション管理用フラグ (簡易的な例、必要なら拡張) ---
    # is_animating = False

    # --- メインループ ---
    while running:
        time_delta = clock.tick(60) / 1000.0 # FPS制限とデルタタイム

        # --- イベント処理 ---
        mouse_click_pos = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 左クリックのみ
                    # --- アニメーション中はクリックを無視する場合 ---
                    # if not is_animating:
                    #     mouse_click_pos = event.pos
                    mouse_click_pos = event.pos # 現状はアニメーション中でもクリックを受け付ける

        # --- 状態更新 (イベントに基づく) ---
        if mouse_click_pos:
            if not game_started:
                # --- ゲーム開始前 ---
                start_button_rect = gui._calculate_button_rect(is_start_button=True)
                is_start_clicked = gui.is_button_clicked(mouse_click_pos, start_button_rect)
                if is_start_clicked:
                    game_started = True
                    game.set_message("")
                else:
                    # ラジオボタン判定 (GUIに移譲)
                    player_settings_top = gui._calculate_player_settings_top()
                    clicked_player, clicked_agent_id = gui.get_clicked_radio_button(
                        mouse_click_pos, player_settings_top
                    )
                    if clicked_player is not None:
                        if clicked_player == -1 and black_player_id != clicked_agent_id:
                            black_player_id = clicked_agent_id
                            game.set_players(black_player_id, white_player_id)
                        elif clicked_player == 1 and white_player_id != clicked_agent_id:
                            white_player_id = clicked_agent_id
                            game.set_players(black_player_id, white_player_id)

            elif game.game_over:
                # --- ゲームオーバー時 ---
                restart_button_rect = gui._calculate_button_rect(False, True, False, False)
                reset_button_rect = gui._calculate_button_rect(False, True, True, False)
                quit_button_rect = gui._calculate_button_rect(False, True, False, True)

                is_restart_clicked = gui.is_button_clicked(mouse_click_pos, restart_button_rect)
                is_reset_clicked = gui.is_button_clicked(mouse_click_pos, reset_button_rect)
                is_quit_clicked = gui.is_button_clicked(mouse_click_pos, quit_button_rect)

                if is_restart_clicked:
                    game.reset()
                    game.set_players(black_player_id, white_player_id) # 設定引き継ぎ
                    game_started = True
                    # is_animating = False # アニメーション状態リセット
                elif is_reset_clicked:
                    game.reset()
                    black_player_id = 0 # 設定リセット
                    white_player_id = 0
                    game.set_players(black_player_id, white_player_id)
                    game_started = False
                    # is_animating = False # アニメーション状態リセット
                elif is_quit_clicked:
                    running = False

            else:
                # --- ゲーム中 ---
                restart_button_rect = gui._calculate_button_rect(False, False, False, False)
                reset_button_rect = gui._calculate_button_rect(False, False, True, False)
                quit_button_rect = gui._calculate_button_rect(False, False, False, True)

                is_restart_clicked = gui.is_button_clicked(mouse_click_pos, restart_button_rect)
                is_reset_clicked = gui.is_button_clicked(mouse_click_pos, reset_button_rect)
                is_quit_clicked = gui.is_button_clicked(mouse_click_pos, quit_button_rect)

                if is_restart_clicked:
                    game.reset()
                    game.set_players(black_player_id, white_player_id) # 設定引き継ぎ
                    game_started = True
                    # is_animating = False
                elif is_reset_clicked:
                    game.reset()
                    black_player_id = 0 # 設定リセット
                    white_player_id = 0
                    game.set_players(black_player_id, white_player_id)
                    game_started = False
                    # is_animating = False
                elif is_quit_clicked:
                    running = False
                elif game.agents[game.turn] is None: # 人間の手番
                    row, col = gui.get_clicked_cell(mouse_click_pos)
                    valid_moves = game.get_valid_moves()
                    if (row, col) in valid_moves:
                        # --- 人間の手 ---
                        if game.place_stone(row, col):
                            game.set_message("")
                            game.switch_turn()
                            game.check_game_over() # ゲームオーバーチェック
                        else:
                            # place_stone が False を返すのは通常 is_valid_move が False の場合
                            # ここに来る場合は予期せぬエラーの可能性
                            logging.error(f"Error: place_stone({row}, {col}) returned False unexpectedly for human player.")
                    # else: # 無効な手をクリックした場合は何もしない

        # --- 状態更新 (AIの手番、パス) ---
        # --- アニメーション中はAIやパス処理をスキップする場合 ---
        # if not is_animating:
        if game_started and not game.game_over:
            current_turn = game.turn
            current_agent = game.agents[current_turn]
            valid_moves = game.get_valid_moves()

            if not valid_moves:
                # --- パス処理 ---
                current_player_color = '黒' if current_turn == -1 else '白'
                pass_message = f"{current_player_color}はパスです。"
                game.set_message(pass_message)
                game.switch_turn()
                # 相手もパスかチェック -> ゲームオーバー判定
                opponent_valid_moves = game.get_valid_moves()
                if not opponent_valid_moves:
                    game.game_over = True
                    # 勝敗メッセージ設定は描画セクションで行う
            elif current_agent is not None:
                # --- AIの手番 ---
                move = current_agent.play(game)
                if move and move in valid_moves: # AIが有効な手を返したか確認
                    if game.place_stone(move[0], move[1]):
                        game.set_message("")
                        game.switch_turn()
                        game.check_game_over()
                    else:
                        # place_stone が False を返すのは通常 is_valid_move が False の場合
                        # AIが有効な手を返したはずなのに False になるのは予期せぬエラー
                        logging.error(f"Error: AI place_stone({move[0]}, {move[1]}) returned False unexpectedly.")
                else:
                    # AIが手を返さなかった、または無効な手を返した場合
                    log_message = f"AI ({type(current_agent).__name__}) returned invalid move: {move}. Valid moves: {valid_moves}"
                    logging.warning(log_message)
                    # 必要であればここでエラー処理やフォールバック処理を追加
            # else: 人間の手番の場合はクリック待ち

        # --- 描画処理 ---
        gui.screen.fill(Color.BACKGROUND)
        player_settings_top = gui._calculate_player_settings_top() # 描画前に計算

        # --- アニメーション描画 (必要なら) ---
        # if is_animating:
        #     # アニメーションのステップ描画関数を呼び出す
        #     # is_animating = gui.draw_animation_step(animation_type, animation_data) # アニメ完了したらFalseを返すように
        #     pass # アニメーション描画処理
        # else:
        # --- 通常描画 ---
        if not game_started:
            # --- ゲーム開始前画面 ---
            gui.draw_board(game)
            gui.draw_start_button()
            gui.draw_player_settings(game, player_settings_top, enabled=True)

        elif game.game_over:
            # --- ゲームオーバー画面 ---
            winner = game.get_winner()
            winner_message = ""
            if winner == -1: winner_message = "黒の勝ちです！"
            elif winner == 1: winner_message = "白の勝ちです！"
            else: winner_message = "引き分けです！"
            game.set_message(winner_message)

            gui.draw_board(game)
            gui.draw_message(game.get_message(), is_game_over=True)
            gui.draw_player_settings(game, player_settings_top, enabled=True) # リセット用に有効
            gui.draw_restart_button(game_over=True)
            gui.draw_reset_button(game_over=True)
            gui.draw_quit_button(game_over=True)

        else:
            # --- ゲーム中画面 ---
            gui.draw_board(game)
            if game.agents[game.turn] is None: # 人間の番なら合法手表示
                gui.draw_valid_moves(game)
            gui.draw_turn_message(game)
            gui.draw_restart_button(game_over=False)
            gui.draw_reset_button(game_over=False)
            gui.draw_quit_button(game_over=False)
            gui.draw_message(game.get_message()) # パスメッセージなど
            gui.draw_player_settings(game, player_settings_top, enabled=False) # ゲーム中は設定無効

        # --- 画面更新 ---
        pygame.display.flip()

    # --- 終了処理 ---
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
