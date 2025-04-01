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
BUTTON_COLOR = (50, 50, 50) #ボタンの色
BUTTON_TEXT_COLOR = (200, 200, 200) #ボタンの文字色
DISABLED_TEXT_COLOR = (100, 100, 100) #無効な文字色

class GameGUI:
    def __init__(self, screen_width=450, screen_height=650): #画面サイズを変更
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
                self.font = pygame.font.Font(font_path, 24) #フォントサイズを変更
            else:
                self.font = pygame.font.Font(None, 24) #フォントサイズを変更
        except Exception as e:
            print(f"フォントの読み込みに失敗しました: {e}")
            self.font = pygame.font.Font(None, 24) #フォントサイズを変更

        self.board_top_margin = 0 # ボード上部のマージン
        self.board_bottom_margin = 100 # ボード下部のマージン
        self.board_size = 400 # ボードサイズを定義
        self.cell_size = self.board_size // 8 # セルのサイズを再計算
        self.button_width = 150 #ボタンの幅
        self.button_height = 50 #ボタンの高さ
        self.stone_count_margin = 5 #石の数の表示マージン
        self.player_settings_margin = 40 # プレーヤー設定のマージン
        self.message_margin = 5 #メッセージのマージン
        self.radio_button_size = 20
        self.radio_button_margin = 10

    def draw_board(self, game):
        self.screen.fill(BACKGROUND_COLOR)  # ボード外の背景色で画面全体を塗りつぶす

        # ボードの描画範囲を計算
        board_width = self.board_size
        board_height = self.board_size
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
        self.draw_stone_count(black_count, white_count, board_left, board_top, board_width, board_height)

    def draw_stone_count(self, black_count, white_count, board_left, board_top, board_width, board_height):
        # 黒石の数を表示
        black_text = self.font.render(f"黒: {black_count}", True, BLACK)
        black_rect = black_text.get_rect(topleft=(board_left, board_top + board_height + self.stone_count_margin))
        self.screen.blit(black_text, black_rect)

        # 白石の数を表示
        white_text = self.font.render(f"白: {white_count}", True, WHITE)
        white_rect = white_text.get_rect(topright=(board_left + board_width, board_top + board_height + self.stone_count_margin))
        self.screen.blit(white_text, white_rect)

    def draw_valid_moves(self, game):
        valid_moves = game.get_valid_moves() # 合法手の取得
        board_width = self.board_size
        board_left = (self.screen_width - board_width) // 2
        board_top = self.board_top_margin
        for row, col in valid_moves:
            pygame.draw.circle(self.screen, GRAY, (board_left + col * self.cell_size + self.cell_size // 2, board_top + row * self.cell_size + self.cell_size // 2), self.cell_size // 8)

    def draw_message(self, message):
        text = self.font.render(message, True, WHITE)
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height - self.message_margin - 30)) # メッセージの表示位置を変更
        self.screen.blit(text, text_rect)

    def get_clicked_cell(self, pos):
        x, y = pos
        board_width = self.board_size
        board_left = (self.screen_width - board_width) // 2
        board_top = self.board_top_margin
        if not (board_left <= x < board_left + board_width and board_top <= y < board_top + board_width):
            return -1, -1
        col = (x - board_left) // self.cell_size
        row = (y - board_top) // self.cell_size
        return row, col

    def draw_stone_animation(self, game, row, col, color):
        board_width = self.board_size
        board_left = (self.screen_width - board_width) // 2
        board_top = self.board_top_margin
        center = (board_left + col * self.cell_size + self.cell_size // 2, board_top + row * self.cell_size + self.cell_size // 2)
        max_radius = self.cell_size // 2 - 5

        # 石を置くアニメーション
        for radius in range(0, max_radius, 5):
            self.draw_board(game)
            self.draw_valid_moves(game)
            self.draw_message(game.get_message())
            self.draw_player_settings(game, True)
            pygame.draw.circle(self.screen, color, center, radius)
            pygame.display.flip()
            pygame.time.delay(10)

        # 最終的な石を描画
        pygame.draw.circle(self.screen, color, center, max_radius)
        pygame.display.flip()

    def draw_flip_animation(self, game, flipped_stones, color):
        max_radius = self.cell_size // 2 - 5
        other_color = WHITE if color == BLACK else BLACK
        board_width = self.board_size
        board_left = (self.screen_width - board_width) // 2
        board_top = self.board_top_margin
        for i in range(10):  # アニメーションのフレーム数
            self.draw_board(game)
            self.draw_valid_moves(game)
            self.draw_message(game.get_message())
            self.draw_player_settings(game, True)
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

    def draw_start_button(self):
        button_x = (self.screen_width - self.button_width) // 2
        button_y = (self.screen_height - self.button_height) // 2
        pygame.draw.rect(self.screen, BUTTON_COLOR, (button_x, button_y, self.button_width, self.button_height))
        text = self.font.render("ゲーム開始", True, BUTTON_TEXT_COLOR)
        text_rect = text.get_rect(center=(button_x + self.button_width // 2, button_y + self.button_height // 2))
        self.screen.blit(text, text_rect)
        return (button_x, button_y, self.button_width, self.button_height)

    def draw_restart_button(self, game_over=False):
        button_x = (self.screen_width - self.button_width) // 2
        button_y = (self.screen_height - self.button_height) // 2 if game_over else self.screen_height - 40
        pygame.draw.rect(self.screen, BUTTON_COLOR, (button_x, button_y, self.button_width, self.button_height))
        text = self.font.render("リスタート", True, BUTTON_TEXT_COLOR)
        text_rect = text.get_rect(center=(button_x + self.button_width // 2, button_y + self.button_height // 2))
        self.screen.blit(text, text_rect)
        return (button_x, button_y, self.button_width, self.button_height)

    def is_button_clicked(self, pos, button_rect):
        x, y = pos
        button_x, button_y, button_width, button_height = button_rect
        return button_x <= x <= button_x + button_width and button_y <= y <= button_y + button_height

    def draw_radio_button(self, pos, size, selected):
        x, y = pos
        pygame.draw.circle(self.screen, WHITE, (x + size // 2, y + size // 2), size // 2, 1)
        if selected:
            pygame.draw.circle(self.screen, WHITE, (x + size // 2, y + size // 2), size // 4)

    def draw_text(self, text, pos, enabled=True):
        color = WHITE if enabled else DISABLED_TEXT_COLOR
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, pos)

    def draw_player_settings(self, game, enabled=False):

        # ボードの描画範囲を計算
        board_width = self.board_size
        board_height = self.board_size
        board_left = (self.screen_width - board_width) // 2
        board_top = self.board_top_margin

        #石の数の表示位置
        stone_count_top = board_top + board_height + self.stone_count_margin

        # プレーヤー設定の表示位置を調整
        player_settings_top = stone_count_top + self.player_settings_margin

        black_player_label_pos = (10, player_settings_top)
        white_player_label_pos = (self.screen_width // 2, player_settings_top)

        black_human_radio_pos = (black_player_label_pos[0], black_player_label_pos[1] + 30)
        black_random_radio_pos = (black_player_label_pos[0], black_human_radio_pos[1] + 30)
        white_human_radio_pos = (white_player_label_pos[0], white_player_label_pos[1] + 30)
        white_random_radio_pos = (white_player_label_pos[0], white_human_radio_pos[1] + 30)

        black_player_type = game.agents[-1]
        white_player_type = game.agents[1]

        # 黒プレイヤーの設定を描画
        self.draw_text("黒プレイヤー", black_player_label_pos, enabled)
        self.draw_text("人間", (black_human_radio_pos[0] + self.radio_button_size + self.radio_button_margin, black_human_radio_pos[1]), enabled)
        self.draw_text("ランダム", (black_random_radio_pos[0] + self.radio_button_size + self.radio_button_margin, black_random_radio_pos[1]), enabled)
        if black_player_type is None:
            self.draw_radio_button(black_human_radio_pos, self.radio_button_size, True)
            self.draw_radio_button(black_random_radio_pos, self.radio_button_size, False)
        else:
            self.draw_radio_button(black_human_radio_pos, self.radio_button_size, False)
            self.draw_radio_button(black_random_radio_pos, self.radio_button_size, True)

        # 白プレイヤーの設定を描画
        self.draw_text("白プレイヤー", white_player_label_pos, enabled)
        self.draw_text("人間", (white_human_radio_pos[0] + self.radio_button_size + self.radio_button_margin, white_human_radio_pos[1]), enabled)
        self.draw_text("ランダム", (white_random_radio_pos[0] + self.radio_button_size + self.radio_button_margin, white_random_radio_pos[1]), enabled)
        if white_player_type is None:
            self.draw_radio_button(white_human_radio_pos, self.radio_button_size, True)
            self.draw_radio_button(white_random_radio_pos, self.radio_button_size, False)
        else:
            self.draw_radio_button(white_human_radio_pos, self.radio_button_size, False)
            self.draw_radio_button(white_random_radio_pos, self.radio_button_size, True)
