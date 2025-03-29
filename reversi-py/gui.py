# gui.py
import pygame

# 色の定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)
GRAY = (128, 128, 128)

class GameGUI:
    def __init__(self, screen_width=600, screen_height=600):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Reversi")
        self.font = pygame.font.Font(None, 36)
        self.cell_size = self.screen_width // 8

    def draw_board(self, game):
        self.screen.fill(GREEN)
        board = game.get_board()  # 盤面の2次元配列を取得
        board_size = game.get_board_size()
        for row in range(board_size):
            for col in range(board_size):
                pygame.draw.rect(self.screen, BLACK, (col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size), 1)
                if board[row][col] == 1:
                    pygame.draw.circle(self.screen, WHITE, (col * self.cell_size + self.cell_size // 2, row * self.cell_size + self.cell_size // 2), self.cell_size // 2 - 5)
                elif board[row][col] == -1:
                    pygame.draw.circle(self.screen, BLACK, (col * self.cell_size + self.cell_size // 2, row * self.cell_size + self.cell_size // 2), self.cell_size // 2 - 5)

    def draw_valid_moves(self, game):
        valid_moves = game.get_valid_moves() # 合法手の取得
        for row, col in valid_moves:
            pygame.draw.circle(self.screen, GRAY, (col * self.cell_size + self.cell_size // 2, row * self.cell_size + self.cell_size // 2), self.cell_size // 8)

    def draw_message(self, message):
        text = self.font.render(message, True, WHITE)
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
        self.screen.blit(text, text_rect)

    def get_clicked_cell(self, pos):
        x, y = pos
        col = x // self.cell_size
        row = y // self.cell_size
        return row, col

    def draw_stone_animation(self, game, row, col, color): # game を引数に追加
        radius = 0
        while radius < self.cell_size // 2 - 5:
            self.draw_board(game) # game を渡す
            pygame.draw.circle(self.screen, color, (col * self.cell_size + self.cell_size // 2, row * self.cell_size + self.cell_size // 2), radius)
            pygame.display.flip()
            radius += 5
            pygame.time.delay(10)
