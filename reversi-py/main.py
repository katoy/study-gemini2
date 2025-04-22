# main.py
import pygame
from game import Game
# --- gui から GameGUI のみインポート ---
from gui import GameGUI
# --- config.theme から Screen, Color をインポート ---
from config.theme import Screen, Color
# --- config.agents から get_agent_options をインポート ---
from config.agents import get_agent_options
# -------------------------------------------------------

def main():
    game = Game()
    gui = GameGUI()
    clock = pygame.time.Clock()
    black_player_type = 0 # デフォルトは人間 (ID: 0)
    white_player_type = 0 # デフォルトは人間 (ID: 0)
    game.set_players(black_player_type, white_player_type)
    game_started = False
    running = True
    radio_button_size = Screen.RADIO_BUTTON_SIZE

    # --- エージェントオプションを取得 ---
    agent_options = get_agent_options()
    # -------------------------------

    while running:
        board_rect = gui._calculate_board_rect() # 盤面描画領域を計算
        board_left = board_rect.left
        player_settings_top = gui._calculate_player_settings_top()
        # ボタンのRectはイベントループ内で必要に応じて計算するため、ここでは初期化しない

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not game_started:
                    # ゲーム開始ボタンのクリック判定
                    temp_start_button_rect = gui._calculate_button_rect(True)
                    if gui.is_button_clicked(event.pos, temp_start_button_rect):
                        game_started = True
                        game.set_message("")
                    else:
                        # --- 修正: ラジオボタンのクリック判定とプレイヤー設定更新 ---
                        white_player_label_x = gui.screen_width // 2 + Screen.RADIO_BUTTON_MARGIN
                        radio_y_offset = Screen.RADIO_Y_OFFSET
                        radio_y_spacing = Screen.RADIO_Y_SPACING
                        radio_button_size = Screen.RADIO_BUTTON_SIZE

                        clicked_on_radio = False
                        for i, (agent_id, _) in enumerate(agent_options):
                            # ラジオボタンのY座標を計算
                            radio_y = player_settings_top + radio_y_offset + i * radio_y_spacing

                            # 黒プレイヤーのラジオボタンのRectを計算してクリック判定
                            black_radio_rect = pygame.Rect(board_left, radio_y, radio_button_size, radio_button_size)
                            if black_radio_rect.collidepoint(event.pos):
                                if black_player_type != agent_id: # 変更があった場合のみ更新
                                    black_player_type = agent_id
                                    game.set_players(black_player_type, white_player_type) # ゲーム状態更新
                                clicked_on_radio = True
                                break # どちらかをクリックしたらループを抜ける

                            # 白プレイヤーのラジオボタンのRectを計算してクリック判定
                            white_radio_rect = pygame.Rect(white_player_label_x, radio_y, radio_button_size, radio_button_size)
                            if white_radio_rect.collidepoint(event.pos):
                                if white_player_type != agent_id: # 変更があった場合のみ更新
                                    white_player_type = agent_id
                                    game.set_players(black_player_type, white_player_type) # ゲーム状態更新
                                clicked_on_radio = True
                                break # どちらかをクリックしたらループを抜ける
                        # ---------------------------------------------------------

                elif game.game_over:
                    # ゲームオーバー時のボタンクリック判定
                    temp_restart_button_rect = gui._calculate_button_rect(False, True, is_reset_button=False, is_quit_button=False)
                    temp_reset_button_rect = gui._calculate_button_rect(False, True, is_reset_button=True, is_quit_button=False)
                    temp_quit_button_rect = gui._calculate_button_rect(False, True, is_reset_button=False, is_quit_button=True) # 終了ボタンRect取得

                    if gui.is_button_clicked(event.pos, temp_restart_button_rect):
                        game.reset()
                        game.set_players(black_player_type, white_player_type) # 前回の設定を引き継ぐ
                        game_started = True
                    elif gui.is_button_clicked(event.pos, temp_reset_button_rect):
                        game.reset()
                        black_player_type = 0 # プレイヤー設定もリセット
                        white_player_type = 0
                        game.set_players(black_player_type, white_player_type)
                        game_started = False
                    elif gui.is_button_clicked(event.pos, temp_quit_button_rect):
                        running = False # ゲームループを終了
                    else:
                        pass # ボタン外クリックは無視

                else:  # ゲーム中
                    # リスタート・リセット・終了ボタンのクリック判定
                    temp_restart_button_rect = gui._calculate_button_rect(False, False, is_reset_button=False, is_quit_button=False)
                    temp_reset_button_rect = gui._calculate_button_rect(False, False, is_reset_button=True, is_quit_button=False)
                    temp_quit_button_rect = gui._calculate_button_rect(False, False, is_reset_button=False, is_quit_button=True) # 終了ボタンRect取得

                    if gui.is_button_clicked(event.pos, temp_restart_button_rect):
                        game.reset()
                        game.set_players(black_player_type, white_player_type) # 前回の設定を引き継ぐ
                        game_started = True
                    elif gui.is_button_clicked(event.pos, temp_reset_button_rect):
                        game.reset()
                        black_player_type = 0 # プレイヤー設定もリセット
                        white_player_type = 0
                        game.set_players(black_player_type, white_player_type)
                        game_started = False
                    elif gui.is_button_clicked(event.pos, temp_quit_button_rect):
                        running = False # ゲームループを終了
                    elif not game.game_over and game.agents[game.turn] is None: # 人間プレイヤーの番
                        row, col = gui.get_clicked_cell(event.pos)
                        if (row, col) in game.get_valid_moves():
                            flipped_stones = game.get_flipped_stones(row, col, game.turn)
                            if game.place_stone(row, col):
                                game.set_message("") # 石を置いたらメッセージをクリア
                                gui.draw_stone_animation(game, row, col, Color.WHITE if game.turn == 1 else Color.BLACK)
                                gui.draw_flip_animation(game, flipped_stones, Color.WHITE if game.turn == 1 else Color.BLACK)
                                game.switch_turn()
                                game.check_game_over()
            elif event.type == pygame.KEYDOWN:
                # キー入力イベント（現在は未使用）
                pass

        # --- 描画処理 ---
        gui.screen.fill(Color.BACKGROUND)

        if not game_started:
            # ゲーム開始前の画面描画
            gui.draw_board(game)
            gui.draw_start_button() # 戻り値は使わない
            gui.draw_player_settings(game, player_settings_top, True) # 設定有効
            pygame.display.flip()
            clock.tick(60)
            continue # ゲーム開始までループの先頭に戻る

        if game.game_over:
            # ゲームオーバー画面の描画
            winner = game.get_winner()
            if winner == -1: game.set_message("黒の勝ちです！")
            elif winner == 1: game.set_message("白の勝ちです！")
            else: game.set_message("引き分けです！")
            gui.draw_board(game)
            gui.draw_message(game.get_message(), is_game_over=True)
            # ゲームオーバー時もプレイヤー設定を表示するが、操作はできないようにする
            # gui.draw_player_settings(game, player_settings_top, False) # 設定無効
            # -> リセットボタンで設定を初期化できるように、表示は有効のままにする
            gui.draw_player_settings(game, player_settings_top, True) # 設定有効 (リセット用)
            gui.draw_restart_button(True) # 戻り値は使わない
            gui.draw_reset_button(True)   # 戻り値は使わない
            gui.draw_quit_button(True)    # --- 追加: 終了ボタン描画 ---
            pygame.display.flip()
            clock.tick(60)
            continue # ゲームオーバー状態を維持

        else: # ゲーム中
            # パス判定と処理
            if not game.get_valid_moves():
                current_player_color = '黒' if game.turn == -1 else '白'
                game.set_message(f"{current_player_color}はパスです。") # パス時にメッセージ設定
                game.switch_turn()
                game.check_game_over()
                if game.game_over:
                    continue
            else:
                # エージェントの処理
                if game.agents[game.turn] is not None: # エージェントの番
                    agent = game.agents[game.turn]
                    move = agent.play(game)
                    if move:
                        flipped_stones = game.get_flipped_stones(move[0], move[1], game.turn)
                        # 石を置く前にアニメーション用に描画更新
                        gui.draw_board(game)
                        gui.draw_turn_message(game)
                        gui.draw_restart_button()
                        gui.draw_reset_button()
                        gui.draw_quit_button()
                        gui.draw_message(game.get_message())
                        gui.draw_player_settings(game, player_settings_top, False) # ゲーム中は設定無効
                        pygame.display.flip()

                        gui.draw_stone_animation(game, move[0], move[1], Color.WHITE if game.turn == 1 else Color.BLACK)
                        if game.place_stone(move[0], move[1]):
                            game.set_message("")
                            # 裏返しアニメーション用に描画更新
                            gui.draw_board(game)
                            gui.draw_turn_message(game)
                            gui.draw_restart_button()
                            gui.draw_reset_button()
                            gui.draw_quit_button()
                            gui.draw_message(game.get_message())
                            gui.draw_player_settings(game, player_settings_top, False) # ゲーム中は設定無効
                            pygame.display.flip()

                            gui.draw_flip_animation(game, flipped_stones, Color.WHITE if game.turn == 1 else Color.BLACK)
                            game.switch_turn()
                            game.check_game_over()

            # --- ゲーム中の共通描画 ---
            gui.draw_board(game)
            if game.agents[game.turn] is None: # 人間の番なら合法手表示
                gui.draw_valid_moves(game)
            gui.draw_turn_message(game)
            gui.draw_restart_button() # 戻り値は使わない
            gui.draw_reset_button()   # 戻り値は使わない
            gui.draw_quit_button()    # --- 追加: 終了ボタン描画 ---
            gui.draw_message(game.get_message()) # メッセージを描画 (パス以外は空のはず)
            gui.draw_player_settings(game, player_settings_top, False) # 設定無効
            pygame.display.flip()
            clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
