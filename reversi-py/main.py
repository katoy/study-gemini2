# main.py
import pygame
from game import Game
from gui import GameGUI, Color, Screen  # Screen クラスをインポート
# HumanAgent は game.py で 0 として扱われるため、ここでのインポートは必須ではない
from agents import RandomAgent, GainAgent, FirstAgent

def main():
    # ... (前半部分は変更なし) ...
    game = Game()
    gui = GameGUI()
    clock = pygame.time.Clock()
    black_player_type = 0
    white_player_type = 0
    game.set_players(black_player_type, white_player_type)
    game_started = False
    running = True
    radio_button_size = Screen.RADIO_BUTTON_SIZE

    while running:
        # ... (描画位置計算などは変更なし) ...
        board_width = Screen.BOARD_SIZE
        board_height = Screen.BOARD_SIZE
        board_left = (gui.screen_width - board_width) // 2
        board_top = Screen.BOARD_TOP_MARGIN
        player_settings_top = gui._calculate_player_settings_top()
        start_button_rect = None
        restart_button_rect = None
        reset_button_rect = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not game_started:
                    # ... (ゲーム開始前の処理は変更なし) ...
                    temp_start_button_rect = gui._calculate_button_rect(True)
                    if gui.is_button_clicked(event.pos, temp_start_button_rect):
                        game_started = True
                        game.set_message("")
                    else:
                        # ... (ラジオボタンクリック処理は変更なし) ...
                        left_margin = board_left
                        black_player_label_pos = (left_margin, player_settings_top)
                        white_player_label_pos = (gui.screen_width // 2, player_settings_top)
                        radio_y_offset = Screen.RADIO_Y_OFFSET
                        radio_y_spacing = Screen.RADIO_Y_SPACING
                        black_human_radio_pos = (black_player_label_pos[0], black_player_label_pos[1] + radio_y_offset)
                        black_first_radio_pos = (black_player_label_pos[0], black_human_radio_pos[1] + radio_y_spacing)
                        black_random_radio_pos = (black_player_label_pos[0], black_first_radio_pos[1] + radio_y_spacing)
                        black_gain_radio_pos = (black_player_label_pos[0], black_random_radio_pos[1] + radio_y_spacing)
                        white_human_radio_pos = (white_player_label_pos[0], white_player_label_pos[1] + radio_y_offset)
                        white_first_radio_pos = (white_player_label_pos[0], white_human_radio_pos[1] + radio_y_spacing)
                        white_random_radio_pos = (white_player_label_pos[0], white_first_radio_pos[1] + radio_y_spacing)
                        white_gain_radio_pos = (white_player_label_pos[0], white_random_radio_pos[1] + radio_y_spacing)
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
                    # ... (ゲームオーバー時の処理は変更なし) ...
                    temp_restart_button_rect = gui._calculate_button_rect(False, True)
                    temp_reset_button_rect = gui._calculate_button_rect(False, True, is_reset_button=True)
                    if gui.is_button_clicked(event.pos, temp_restart_button_rect):
                        game.reset()
                        game.set_players(black_player_type, white_player_type)
                        game_started = True
                    elif gui.is_button_clicked(event.pos, temp_reset_button_rect):
                        game.reset()
                        black_player_type = 0
                        white_player_type = 0
                        game.set_players(black_player_type, white_player_type)
                        game_started = False
                    else:
                        pass
                else:  # ゲーム中
                    # ... (ボタンクリック処理は変更なし) ...
                    temp_restart_button_rect = gui._calculate_button_rect(False, False)
                    temp_reset_button_rect = gui._calculate_button_rect(False, False, is_reset_button=True)
                    if gui.is_button_clicked(event.pos, temp_restart_button_rect):
                        game.reset()
                        game.set_players(black_player_type, white_player_type)
                        game_started = True
                    elif gui.is_button_clicked(event.pos, temp_reset_button_rect):
                        game.reset()
                        black_player_type = 0
                        white_player_type = 0
                        game.set_players(black_player_type, white_player_type)
                        game_started = False
                    elif not game.game_over and game.agents[game.turn] is None: # 人間プレイヤーの番
                        row, col = gui.get_clicked_cell(event.pos)
                        if (row, col) in game.get_valid_moves():
                            flipped_stones = game.get_flipped_stones(row, col, game.turn)
                            if game.place_stone(row, col):
                                # --- ここにメッセージクリアを追加 ---
                                game.set_message("")
                                # ---------------------------------
                                gui.draw_stone_animation(game, row, col, Color.WHITE if game.turn == 1 else Color.BLACK)
                                gui.draw_flip_animation(game, flipped_stones, Color.WHITE if game.turn == 1 else Color.BLACK)
                                game.switch_turn()
                                game.check_game_over()
            elif event.type == pygame.KEYDOWN:
                # ... (変更なし) ...
                pass

        # --- 描画処理 ---
        gui.screen.fill(Color.BACKGROUND)

        if not game_started:
            # ... (ゲーム開始前の描画は変更なし) ...
            gui.draw_board(game)
            start_button_rect = gui.draw_start_button()
            gui.draw_player_settings(game, player_settings_top, True)
            pygame.display.flip()
            clock.tick(60)
            continue

        if game.game_over:
            # ... (ゲームオーバー時の描画は変更なし) ...
            winner = game.get_winner()
            if winner == -1: game.set_message("黒の勝ちです！")
            elif winner == 1: game.set_message("白の勝ちです！")
            else: game.set_message("引き分けです！")
            gui.draw_board(game)
            gui.draw_message(game.get_message(), is_game_over=True)
            gui.draw_player_settings(game, player_settings_top, True)
            restart_button_rect = gui.draw_restart_button(True)
            reset_button_rect = gui.draw_reset_button(True)
            pygame.display.flip()
            clock.tick(60)
            continue

        else: # ゲーム中
            # パス判定と処理
            if not game.get_valid_moves():
                current_player_color = '黒' if game.turn == -1 else '白'
                game.set_message(f"{current_player_color}はパスです。") # パス時にメッセージ設定
                game.switch_turn()
                game.check_game_over()
            else:
                # エージェントの処理
                if game.agents[game.turn] is not None: # エージェントの番
                    agent = game.agents[game.turn]
                    move = agent.play(game)
                    if move:
                        flipped_stones = game.get_flipped_stones(move[0], move[1], game.turn)
                        gui.draw_stone_animation(game, move[0], move[1], Color.WHITE if game.turn == 1 else Color.BLACK)
                        if game.place_stone(move[0], move[1]):
                            # --- ここにメッセージクリアを追加 ---
                            game.set_message("")
                            # ---------------------------------
                            gui.draw_flip_animation(game, flipped_stones, Color.WHITE if game.turn == 1 else Color.BLACK)
                            game.switch_turn()
                            game.check_game_over()

            # --- ゲーム中の共通描画 ---
            gui.draw_board(game)
            if game.agents[game.turn] is None:
                gui.draw_valid_moves(game)
            gui.draw_turn_message(game)
            restart_button_rect = gui.draw_restart_button()
            reset_button_rect = gui.draw_reset_button()
            gui.draw_message(game.get_message()) # メッセージを描画 (パス以外は空のはず)
            gui.draw_player_settings(game, player_settings_top, False)
            pygame.display.flip()
            clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
