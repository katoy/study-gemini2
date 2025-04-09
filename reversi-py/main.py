# main.py
import pygame
from game import Game
# --- gui から GameGUI のみインポート ---
from gui import GameGUI
# --- config.theme から Screen, Color をインポート ---
from config.theme import Screen, Color
# ------------------------------------------
# HumanAgent は game.py で 0 として扱われるため、ここでのインポートは必須ではない
from agents import RandomAgent, GainAgent, FirstAgent

def main():
    game = Game()
    gui = GameGUI() # GameGUI の初期化は変更なし
    clock = pygame.time.Clock()
    black_player_type = 0
    white_player_type = 0
    game.set_players(black_player_type, white_player_type)
    game_started = False
    running = True
    # --- Screen を直接インポートしたのでそのまま使える ---
    radio_button_size = Screen.RADIO_BUTTON_SIZE
    # -------------------------------------------------

    while running:
        # --- Screen を直接インポートしたのでそのまま使える ---
        board_width = Screen.BOARD_SIZE
        board_height = Screen.BOARD_SIZE
        board_left = (gui.screen_width - board_width) // 2
        board_top = Screen.BOARD_TOP_MARGIN
        player_settings_top = gui._calculate_player_settings_top()
        # -------------------------------------------------
        start_button_rect = None
        restart_button_rect = None
        reset_button_rect = None

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
                        # ラジオボタンのクリック判定
                        # --- Screen を直接インポートしたのでそのまま使える ---
                        radio_y_offset = Screen.RADIO_Y_OFFSET
                        radio_y_spacing = Screen.RADIO_Y_SPACING
                        # -------------------------------------------------
                        black_player_label_pos = (board_left, player_settings_top)
                        white_player_label_pos = (gui.screen_width // 2, player_settings_top)
                        black_human_radio_pos = (black_player_label_pos[0], black_player_label_pos[1] + radio_y_offset)
                        black_first_radio_pos = (black_player_label_pos[0], black_human_radio_pos[1] + radio_y_spacing)
                        black_random_radio_pos = (black_player_label_pos[0], black_first_radio_pos[1] + radio_y_spacing)
                        black_gain_radio_pos = (black_player_label_pos[0], black_random_radio_pos[1] + radio_y_spacing)
                        white_human_radio_pos = (white_player_label_pos[0], white_player_label_pos[1] + radio_y_offset)
                        white_first_radio_pos = (white_player_label_pos[0], white_human_radio_pos[1] + radio_y_spacing)
                        white_random_radio_pos = (white_player_label_pos[0], white_first_radio_pos[1] + radio_y_spacing)
                        white_gain_radio_pos = (white_player_label_pos[0], white_random_radio_pos[1] + radio_y_spacing)

                        # 各ラジオボタンの Rect を作成して判定
                        if gui.is_button_clicked(event.pos, pygame.Rect(black_human_radio_pos, (radio_button_size, radio_button_size))): black_player_type = 0
                        elif gui.is_button_clicked(event.pos, pygame.Rect(black_first_radio_pos, (radio_button_size, radio_button_size))): black_player_type = 1
                        elif gui.is_button_clicked(event.pos, pygame.Rect(black_random_radio_pos, (radio_button_size, radio_button_size))): black_player_type = 2
                        elif gui.is_button_clicked(event.pos, pygame.Rect(black_gain_radio_pos, (radio_button_size, radio_button_size))): black_player_type = 3
                        if gui.is_button_clicked(event.pos, pygame.Rect(white_human_radio_pos, (radio_button_size, radio_button_size))): white_player_type = 0
                        elif gui.is_button_clicked(event.pos, pygame.Rect(white_first_radio_pos, (radio_button_size, radio_button_size))): white_player_type = 1
                        elif gui.is_button_clicked(event.pos, pygame.Rect(white_random_radio_pos, (radio_button_size, radio_button_size))): white_player_type = 2
                        elif gui.is_button_clicked(event.pos, pygame.Rect(white_gain_radio_pos, (radio_button_size, radio_button_size))): white_player_type = 3
                        game.set_players(black_player_type, white_player_type)

                elif game.game_over:
                    # ゲームオーバー時のボタンクリック判定
                    temp_restart_button_rect = gui._calculate_button_rect(False, True)
                    temp_reset_button_rect = gui._calculate_button_rect(False, True, is_reset_button=True)
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
                    else:
                        pass # ボタン外クリックは無視

                else:  # ゲーム中
                    # リスタート・リセットボタンのクリック判定
                    temp_restart_button_rect = gui._calculate_button_rect(False, False)
                    temp_reset_button_rect = gui._calculate_button_rect(False, False, is_reset_button=True)
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
                    elif not game.game_over and game.agents[game.turn] is None: # 人間プレイヤーの番
                        row, col = gui.get_clicked_cell(event.pos)
                        if (row, col) in game.get_valid_moves():
                            flipped_stones = game.get_flipped_stones(row, col, game.turn)
                            if game.place_stone(row, col):
                                game.set_message("") # 石を置いたらメッセージをクリア
                                # --- Color を直接インポートしたのでそのまま使える ---
                                gui.draw_stone_animation(game, row, col, Color.WHITE if game.turn == 1 else Color.BLACK)
                                gui.draw_flip_animation(game, flipped_stones, Color.WHITE if game.turn == 1 else Color.BLACK)
                                # -------------------------------------------------
                                game.switch_turn()
                                game.check_game_over()
            elif event.type == pygame.KEYDOWN:
                # キー入力イベント（現在は未使用）
                pass

        # --- 描画処理 ---
        # --- Color を直接インポートしたのでそのまま使える ---
        gui.screen.fill(Color.BACKGROUND)
        # -------------------------------------------------

        if not game_started:
            # ゲーム開始前の画面描画
            gui.draw_board(game)
            start_button_rect = gui.draw_start_button()
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
            gui.draw_player_settings(game, player_settings_top, True) # 設定有効
            restart_button_rect = gui.draw_restart_button(True)
            reset_button_rect = gui.draw_reset_button(True)
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
                # パス後もゲームオーバーでなければ、相手のターンへ
                if game.game_over: # 両者パスでゲームオーバーの場合
                    continue # ゲームオーバーループへ
                # パスでなければ、次のループで相手の処理へ
            else:
                # エージェントの処理
                if game.agents[game.turn] is not None: # エージェントの番
                    agent = game.agents[game.turn]
                    move = agent.play(game)
                    if move:
                        flipped_stones = game.get_flipped_stones(move[0], move[1], game.turn)
                        # --- Color を直接インポートしたのでそのまま使える ---
                        gui.draw_stone_animation(game, move[0], move[1], Color.WHITE if game.turn == 1 else Color.BLACK)
                        # -------------------------------------------------
                        if game.place_stone(move[0], move[1]):
                            game.set_message("") # 石を置いたらメッセージをクリア
                            # --- Color を直接インポートしたのでそのまま使える ---
                            gui.draw_flip_animation(game, flipped_stones, Color.WHITE if game.turn == 1 else Color.BLACK)
                            # -------------------------------------------------
                            game.switch_turn()
                            game.check_game_over()

            # --- ゲーム中の共通描画 ---
            gui.draw_board(game)
            if game.agents[game.turn] is None: # 人間の番なら合法手表示
                gui.draw_valid_moves(game)
            gui.draw_turn_message(game)
            restart_button_rect = gui.draw_restart_button()
            reset_button_rect = gui.draw_reset_button()
            gui.draw_message(game.get_message()) # メッセージを描画 (パス以外は空のはず)
            gui.draw_player_settings(game, player_settings_top, False) # 設定無効
            pygame.display.flip()
            clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
