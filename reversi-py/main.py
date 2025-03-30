# main.py
import pygame
from game import Game
from gui import GameGUI, BLACK, WHITE  # BLACK と WHITE をインポート
from agent import HumanAgent, RandomAgent, GainAgent, FirstAgent

def main():
    game = Game()
    gui = GameGUI()
    clock = pygame.time.Clock()

    # プレイヤーの設定
    game.set_players(0, 3)  # 黒:人間, 白:GainAgent

    game_started = False #ゲーム開始フラグ
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not game_started: #ゲーム開始前
                    if gui.is_button_clicked(event.pos, start_button_rect):
                        game_started = True
                elif game.game_over: #ゲームオーバー時
                    if gui.is_button_clicked(event.pos, restart_button_rect):
                        game.reset() #ゲームをリセット
                        game.set_players(0, 3) #プレイヤーを再設定
                        game_started = True
                else: #ゲーム中
                    if gui.is_button_clicked(event.pos, restart_button_rect):
                        game.reset() #ゲームをリセット
                        game.set_players(0, 3) #プレイヤーを再設定
                        game_started = True
                    elif not game.game_over and game.agents[game.turn] is None:
                        row, col = gui.get_clicked_cell(event.pos)
                        if (row, col) in game.get_valid_moves():
                            game.place_stone(row, col)
                            gui.draw_stone_animation(game, row, col, WHITE if game.turn == 1 else BLACK) # game を渡す
                            flipped_stones = game.get_flipped_stones(row, col, -1 if game.turn == -1 else 1)
                            gui.draw_flip_animation(game, flipped_stones, WHITE if game.turn == 1 else BLACK)
                            game.switch_turn()
                            game.check_game_over()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    game.history_top()
                elif event.key == pygame.K_RIGHT:
                    game.history_last()

        if not game_started: #ゲーム開始前
            gui.draw_board(game)
            start_button_rect = gui.draw_start_button() #スタートボタンを描画
            pygame.display.flip()
            clock.tick(60)
            continue #ゲーム開始前は、それ以降の処理を行わない

        if game.game_over:
            winner = game.get_winner()
            if winner == -1:
                game.set_message("黒の勝ちです！")
            elif winner == 1:
                game.set_message("白の勝ちです！")
            else:
                game.set_message("引き分けです！")
            gui.draw_board(game)
            gui.draw_message(game.get_message())
            restart_button_rect = gui.draw_restart_button(True) #リスタートボタンを描画
            pygame.display.flip()
            clock.tick(60)
            continue #ゲームオーバーになったら、それ以降の処理を行わない

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
                        gui.draw_stone_animation(game, move[0], move[1], WHITE if game.turn == 1 else BLACK) # game を渡す
                        game.place_stone(move[0], move[1])
                        game.switch_turn()
                        game.check_game_over()

        gui.draw_board(game)
        gui.draw_valid_moves(game)
        gui.draw_message(game.get_message())
        restart_button_rect = gui.draw_restart_button() #リスタートボタンを描画
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
