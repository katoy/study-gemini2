# main.py
import pygame
from game import Game
from gui import GameGUI, Color, Screen  # Screen クラスをインポート
from agent import HumanAgent, RandomAgent, GainAgent, FirstAgent

def main():
    game = Game()
    gui = GameGUI()
    clock = pygame.time.Clock()

    # プレイヤーの設定（初期値）
    black_player_type = 0  # 0: 人間, 2: RandomAgent
    white_player_type = 0  # 0: 人間, 2: RandomAgent
    game.set_players(black_player_type, white_player_type)

    game_started = False  # ゲーム開始フラグ
    running = True

    # ラジオボタンの状態を管理する変数
    black_player_selected = 0  # 0: 人間, 1: RandomAgent
    white_player_selected = 0  # 0: 人間, 1: RandomAgent

    # ラジオボタンの描画位置とサイズ
    radio_button_size = Screen.RADIO_BUTTON_SIZE
    radio_button_margin = Screen.RADIO_BUTTON_MARGIN

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not game_started:  # ゲーム開始前
                    if gui.is_button_clicked(event.pos, start_button_rect):
                        game_started = True
                    else:
                        # 黒プレイヤーのラジオボタンのクリック判定
                        # ボードの描画範囲を計算
                        board_width = Screen.BOARD_SIZE
                        board_height = Screen.BOARD_SIZE
                        board_left = (gui.screen_width - board_width) // 2
                        board_top = Screen.BOARD_TOP_MARGIN

                        #石の数の表示位置(ゲーム開始前は石の表示がないので、盤面の下端を基準にする)
                        stone_count_top = board_top + board_height + (gui.screen_width - (board_left + board_width)) #修正

                        # プレーヤー設定の表示位置を調整
                        player_settings_top = stone_count_top + Screen.PLAYER_SETTINGS_MARGIN
                        # ボードの左マージンを取得
                        left_margin = board_left

                        black_player_label_pos = (left_margin, player_settings_top)
                        white_player_label_pos = (gui.screen_width // 2, player_settings_top)

                        black_human_radio_pos = (black_player_label_pos[0], black_player_label_pos[1] + 30)
                        black_random_radio_pos = (black_player_label_pos[0], black_human_radio_pos[1] + 30)
                        white_human_radio_pos = (white_player_label_pos[0], white_player_label_pos[1] + 30)
                        white_random_radio_pos = (white_player_label_pos[0], white_human_radio_pos[1] + 30)
                        if (black_human_radio_pos[0] <= event.pos[0] <= black_human_radio_pos[0] + radio_button_size and
                                black_human_radio_pos[1] <= event.pos[1] <= black_human_radio_pos[1] + radio_button_size):
                            black_player_selected = 0
                            black_player_type = 0
                        elif (black_random_radio_pos[0] <= event.pos[0] <= black_random_radio_pos[0] + radio_button_size and
                                black_random_radio_pos[1] <= event.pos[1] <= black_random_radio_pos[1] + radio_button_size):
                            black_player_selected = 1
                            black_player_type = 2
                        # 白プレイヤーのラジオボタンのクリック判定
                        if (white_human_radio_pos[0] <= event.pos[0] <= white_human_radio_pos[0] + radio_button_size and
                                white_human_radio_pos[1] <= event.pos[1] <= white_human_radio_pos[1] + radio_button_size):
                            white_player_selected = 0
                            white_player_type = 0
                        elif (white_random_radio_pos[0] <= event.pos[0] <= white_random_radio_pos[0] + radio_button_size and
                                white_random_radio_pos[1] <= event.pos[1] <= white_random_radio_pos[1] + radio_button_size):
                            white_player_selected = 1
                            white_player_type = 2
                        game.set_players(black_player_type, white_player_type)

                elif game.game_over:  # ゲームオーバー時
                    # リスタートボタンのクリックを検知
                    if gui.is_button_clicked(event.pos, restart_button_rect):
                        game.reset()  # ゲームをリセット
                        game.set_players(black_player_type, white_player_type)  # プレイヤーを再設定
                        game_started = True
                    # リセットボタンのクリックを検知
                    elif gui.is_button_clicked(event.pos, reset_button_rect):
                        game.reset()  # ゲームをリセット
                        # プレイヤー設定を初期化
                        black_player_type = 0
                        white_player_type = 0
                        black_player_selected = 0
                        white_player_selected = 0
                        game.set_players(black_player_type, white_player_type)
                        game_started = False  # ゲーム開始前へ
                else:  # ゲーム中
                    # リスタートボタンのクリックを検知
                    if gui.is_button_clicked(event.pos, restart_button_rect):
                        game.reset()  # ゲームをリセット
                        game.set_players(black_player_type, white_player_type)  # プレイヤーを再設定
                        game_started = True
                    # リセットボタンのクリックを検知
                    elif gui.is_button_clicked(event.pos, reset_button_rect):
                        game.reset()  # ゲームをリセット
                        # プレイヤー設定を初期化
                        black_player_type = 0
                        white_player_type = 0
                        black_player_selected = 0
                        white_player_selected = 0
                        game.set_players(black_player_type, white_player_type)
                        game_started = False  # ゲーム開始前へ
                    elif not game.game_over and game.agents[game.turn] is None:
                        row, col = gui.get_clicked_cell(event.pos)
                        if (row, col) in game.get_valid_moves():
                            game.place_stone(row, col)
                            gui.draw_stone_animation(game, row, col, Color.WHITE if game.turn == 1 else Color.BLACK)  # game を渡す
                            flipped_stones = game.get_flipped_stones(row, col, -1 if game.turn == -1 else 1)
                            gui.draw_flip_animation(game, flipped_stones, Color.WHITE if game.turn == 1 else Color.BLACK)
                            game.switch_turn()
                            game.check_game_over()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    game.history_top()
                elif event.key == pygame.K_RIGHT:
                    game.history_last()

        if not game_started:  # ゲーム開始前
            gui.draw_board(game)
            start_button_rect = gui.draw_start_button()  # スタートボタンを描画

            # ボードの描画範囲を計算
            board_width = Screen.BOARD_SIZE
            board_height = Screen.BOARD_SIZE
            board_left = (gui.screen_width - board_width) // 2
            board_top = Screen.BOARD_TOP_MARGIN

            #石の数の表示位置(ゲーム開始前は石の表示がないので、盤面の下端を基準にする)
            stone_count_top = board_top + board_height + (gui.screen_width - (board_left + board_width)) #修正

            # プレーヤー設定の表示位置を調整
            player_settings_top = stone_count_top + Screen.PLAYER_SETTINGS_MARGIN
            # ボードの左マージンを取得
            left_margin = board_left

            black_player_label_pos = (left_margin, player_settings_top)
            white_player_label_pos = (gui.screen_width // 2, player_settings_top)

            black_human_radio_pos = (black_player_label_pos[0], black_player_label_pos[1] + 30)
            black_random_radio_pos = (black_player_label_pos[0], black_human_radio_pos[1] + 30)
            white_human_radio_pos = (white_player_label_pos[0], white_player_label_pos[1] + 30)
            white_random_radio_pos = (white_player_label_pos[0], white_human_radio_pos[1] + 30)

            # 黒プレイヤーのラジオボタンを描画
            gui.draw_radio_button(black_human_radio_pos, black_player_selected == 0)
            gui.draw_radio_button(black_random_radio_pos, black_player_selected == 1)
            gui.draw_text("黒プレイヤー", black_player_label_pos)
            gui.draw_text("人間", (black_human_radio_pos[0] + radio_button_size + radio_button_margin, black_human_radio_pos[1]))
            gui.draw_text("ランダム", (black_random_radio_pos[0] + radio_button_size + radio_button_margin, black_random_radio_pos[1]))

            # 白プレイヤーのラジオボタンを描画
            gui.draw_radio_button(white_human_radio_pos, white_player_selected == 0)
            gui.draw_radio_button(white_random_radio_pos, white_player_selected == 1)
            gui.draw_text("白プレイヤー", white_player_label_pos)
            gui.draw_text("人間", (white_human_radio_pos[0] + radio_button_size + radio_button_margin, white_human_radio_pos[1]))
            gui.draw_text("ランダム", (white_random_radio_pos[0] + radio_button_size + radio_button_margin, white_random_radio_pos[1]))

            pygame.display.flip()
            clock.tick(60)
            continue  # ゲーム開始前は、それ以降の処理を行わない

        if game.game_over:
            winner = game.get_winner()
            if winner == -1:
                game.set_message("黒の勝ちです！")
            elif winner == 1:
                game.set_message("白の勝ちです！")
            else:
                game.set_message("引き分けです！")
            gui.draw_board(game)
            gui.draw_message(game.get_message(), is_game_over=True) #button_heightを削除
            gui.draw_player_settings(game, True)
            restart_button_rect = gui.draw_restart_button(True)  # リスタートボタンを描画 #button_heightを取得を削除
            # リセットボタンを描画
            reset_button_rect = gui.draw_reset_button(True) #button_heightを取得を削除
            pygame.display.flip()
            clock.tick(60)
            continue  # ゲームオーバーになったら、それ以降の処理を行わない

        else:
            if not game.get_valid_moves():
                print(f"{'黒' if game.turn == -1 else '白'}はパスです。")
                game.set_message(f"{'黒' if game.turn == -1 else '白'}はパスです。")
                game.switch_turn()
                game.check_game_over()
            else:
                if game.agents[game.turn] is not None:
                    agent = game.agents[game.turn]
                    move = agent.play(game)
                    if move:
                        gui.draw_stone_animation(game, move[0], move[1], Color.WHITE if game.turn == 1 else Color.BLACK)  # game を渡す
                        game.place_stone(move[0], move[1])
                        game.switch_turn()
                        game.check_game_over()

        gui.draw_board(game)
        gui.draw_valid_moves(game)
        restart_button_rect = gui.draw_restart_button()  # リスタートボタンを描画 #button_heightを取得を削除
        # リセットボタンを描画
        reset_button_rect = gui.draw_reset_button() #button_heightを取得を削除
        gui.draw_message(game.get_message()) #button_heightを削除
        gui.draw_player_settings(game, True)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
