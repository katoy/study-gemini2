# gui.py
import pygame
import os

# 色の定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)
GRAY = (128, 128, 128)
BOARD_COLOR = (0, 128, 0)  # ボードの色を定義
BACKGROUND_COLOR = (100, 100, 100)  # ボード外の背景色を定義（例：濃い灰色）

class GameGUI:
    def __init__(self, screen_width=600, screen_height=600):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Reversi")

        # フォントの指定（x.py を参考に変更）
        font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"  # macOS 用のパス
        if not os.path.exists(font_path):
            font_path = "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc" #macOS用パス
        if not os.path.exists(font_path):
            font_path = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf" #ubuntu用パス
        if not os.path.exists(font_path):
            font_path = "/usr/share/fonts/truetype/fonts-japanese-mincho.ttf" #ubuntu用パス
        if not os.path.exists(font_path):
            font_path = None
            print("日本語フォントが見つかりませんでした。デフォルトフォントを使用します。")

        try:
            if font_path:
                self.font = pygame.font.Font(font_path, 36)
            else:
                self.font = pygame.font.Font(None, 36)
        except Exception as e:
            print(f"フォントの読み込みに失敗しました: {e}")
            self.font = pygame.font.Font(None, 36)

        self.cell_size = self.screen_width // 8
        self.board_top_margin = 0 # ボード上部のマージン
        self.board_bottom_margin = 100 # ボード下部のマージン
        self.board_height = self.screen_height - self.board_bottom_margin - self.board_top_margin # ボードの高さ
        self.cell_size = self.board_height // 8

    def draw_board(self, game):
        self.screen.fill(BACKGROUND_COLOR)  # ボード外の背景色で画面全体を塗りつぶす

        # ボードの描画範囲を計算
        board_width = self.cell_size * 8
        board_height = self.cell_size * 8
        board_left = (self.screen_width - board_width) // 2
        board_top = self.board_top_margin

        # ボードの描画
        pygame.draw.rect(self.screen, BOARD_COLOR, (board_left, board_top, board_width, board_height))

        board = game.get_board()  # 盤面の2次元配列を取得
        board_size = game.get_board_size()
        for row in range(board_size):
            for col in range(board_size):
                pygame.draw.rect(self.screen, BLACK, (board_left + col * self.cell_size, board_top + row * self.cell_size, self.cell_size, self.cell_size), 1)
                if board[row][col] == 1:
                    pygame.draw.circle(self.screen, WHITE, (board_left + col * self.cell_size + self.cell_size // 2, board_top + row * self.cell_size + self.cell_size // 2), self.cell_size // 2 - 5)
                elif board[row][col] == -1:
                    pygame.draw.circle(self.screen, BLACK, (board_left + col * self.cell_size + self.cell_size // 2, board_top + row * self.cell_size + self.cell_size // 2), self.cell_size // 2 - 5)

        # 石の数を表示
        black_count, white_count = game.board.count_stones()
        self.draw_stone_count(black_count, white_count)

    def draw_stone_count(self, black_count, white_count):
        # 黒石の数を表示
        black_text = self.font.render(f"黒: {black_count}", True, BLACK)
        black_rect = black_text.get_rect(topleft=(10, self.screen_height - 80))
        self.screen.blit(black_text, black_rect)

        # 白石の数を表示
        white_text = self.font.render(f"白: {white_count}", True, WHITE)
        white_rect = white_text.get_rect(topright=(self.screen_width - 10, self.screen_height - 80))
        self.screen.blit(white_text, white_rect)

    def draw_valid_moves(self, game):
        valid_moves = game.get_valid_moves() # 合法手の取得
        board_width = self.cell_size * 8
        board_left = (self.screen_width - board_width) // 2
        board_top = self.board_top_margin
        for row, col in valid_moves:
            pygame.draw.circle(self.screen, GRAY, (board_left + col * self.cell_size + self.cell_size // 2, board_top + row * self.cell_size + self.cell_size // 2), self.cell_size // 8)

    def draw_message(self, message):
        text = self.font.render(message, True, WHITE)
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height - 40)) # メッセージの表示位置を変更
        self.screen.blit(text, text_rect)

    def get_clicked_cell(self, pos):
        x, y = pos
        board_width = self.cell_size * 8
        board_left = (self.screen_width - board_width) // 2
        board_top = self.board_top_margin
        if not (board_left <= x < board_left + board_width and board_top <= y < board_top + board_width):
            return -1, -1
        col = (x - board_left) // self.cell_size
        row = (y - board_top) // self.cell_size
        return row, col

    def draw_stone_animation(self, game, row, col, color):
        board_width = self.cell_size * 8
        board_left = (self.screen_width - board_width) // 2
        board_top = self.board_top_margin
        center = (board_left + col * self.cell_size + self.cell_size // 2, board_top + row * self.cell_size + self.cell_size // 2)
        max_radius = self.cell_size // 2 - 5

        # 石を置くアニメーション
        for radius in range(0, max_radius, 5):
            self.draw_board(game)
            self.draw_valid_moves(game)
            self.draw_message(game.get_message())
            pygame.draw.circle(self.screen, color, center, radius)
            pygame.display.flip()
            pygame.time.delay(10)

        # 最終的な石を描画
        pygame.draw.circle(self.screen, color, center, max_radius)
        pygame.display.flip()

    def draw_flip_animation(self, game, flipped_stones, color):
        max_radius = self.cell_size // 2 - 5
        other_color = WHITE if color == BLACK else BLACK
        board_width = self.cell_size * 8
        board_left = (self.screen_width - board_width) // 2
        board_top = self.board_top_margin
        for i in range(10):  # アニメーションのフレーム数
            self.draw_board(game)
            self.draw_valid_moves(game)
            self.draw_message(game.get_message())
            for fr, fc in flipped_stones:
                stone_center = (board_left + fc * self.cell_size + self.cell_size // 2, board_top + fr * self.cell_size + self.cell_size // 2)
                if i < 5:
                    # 石が小さくなるアニメーション
                    pygame.draw.circle(self.screen, GREEN, stone_center, max_radius - (max_radius / 5) * i)
                else:
                    # 石が大きくなるアニメーション
                    pygame.draw.circle(self.screen, color, stone_center, (max_radius / 5) * (i - 4))
            pygame.display.flip()
            pygame.time.delay(10)

    def get_flipped_stones(self, game, row, col, turn):
        # board.pyのplace_stoneのロジックを呼び出す
        return game.get_flipped_stones(row, col, turn)
