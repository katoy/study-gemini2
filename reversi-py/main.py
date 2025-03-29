# main.py
import pygame
from game import Game
from gui import GameGUI
from agent import HumanAgent

def main():
    game = Game()
    gui = GameGUI()
    human_agent = HumanAgent()
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not game.game_over:
                    row, col = gui.get_clicked_cell(event.pos)
                    if (row, col) in game.get_valid_moves():
                        game.place_stone(row, col)
                        game.switch_turn()
                        game.check_game_over()

        if game.game_over:
            winner = game.get_winner()
            if winner == -1:
                gui.draw_message("黒の勝ちです！")
            elif winner == 1:
                gui.draw_message("白の勝ちです！")
            else:
                gui.draw_message("引き分けです！")
        else:
            if not game.get_valid_moves():
                print(f"{'黒' if game.turn == -1 else '白'}はパスです。")
                game.switch_turn()
                game.check_game_over()

        gui.draw_board(game)
        gui.draw_valid_moves(game)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
