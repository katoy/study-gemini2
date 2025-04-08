# gui.py
import pygame
import os

# 色の定義
class Color:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 128, 0)
    GRAY = (128, 128, 128)
    BOARD = (0, 128, 0)
    BACKGROUND = (100, 100, 100)
    BUTTON = (50, 50, 50)
    BUTTON_TEXT = (200, 200, 200)
    DISABLED_TEXT = (100, 100, 100)
    DARK_BLUE = (0, 0, 128)  # 濃い青色を追加
    LIGHT_BLUE = (173, 216, 230)  # 薄い青色を追加

# 画面サイズとマージンの定義
class Screen:
    WIDTH = 450
    HEIGHT = 650
    BOARD_SIZE = 400
    BOARD_TOP_MARGIN = 0
    BUTTON_MARGIN = 10
    BUTTON_VERTICAL_MARGIN = 3
    PLAYER_SETTINGS_MARGIN = 30
    MESSAGE_MARGIN = 20
    TURN_MESSAGE_MARGIN = 5
    TURN_MESSAGE_TOP_MARGIN = 10
    TURN_MESSAGE_TOP_MARGIN_GAME_START = 5
    GAME_START_MESSAGE_TOP_MARGIN = 200
    RADIO_BUTTON_SIZE = 24
    RADIO_BUTTON_MARGIN = 10
    BUTTON_BORDER_WIDTH = 2
    CELL_SIZE = BOARD_SIZE // 8
    RADIO_BUTTON_INNER_CIRCLE_RATIO = 0.4 # 小さな円の比率を追加

class GameGUI:
    def __init__(self, screen_width=Screen.WIDTH, screen_height=Screen.HEIGHT):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Reversi")
        self.cell_size = Screen.CELL_SIZE
        self.font = self._load_font()

    def _load_font(self):
        font_paths = [
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",  # macOS
            "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc",  # macOS
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",  # Ubuntu
            "/usr/share/fonts/truetype/fonts-japanese-mincho.ttf",  # Ubuntu
        ]
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return pygame.font.Font(font_path, 24)
                except Exception as e:
                    print(f"フォントの読み込みに失敗しました: {e}")
        print("日本語フォントが見つかりませんでした。デフォルトフォントを使用します。")
        return pygame.font.Font(None, 24)

    def _calculate_board_rect(self):
        board_left = (self.screen_width - Screen.BOARD_SIZE) // 2
        board_top = Screen.BOARD_TOP_MARGIN
        return pygame.Rect(board_left, board_top, Screen.BOARD_SIZE, Screen.BOARD_SIZE)

    def _draw_board_background(self, board_rect):
        self.screen.fill(Color.BACKGROUND)
        pygame.draw.rect(self.screen, Color.BOARD, board_rect)

    def _draw_board_grid(self, board_rect):
        for row in range(8):
            for col in range(8):
                cell_rect = pygame.Rect(
                    board_rect.left + col * self.cell_size,
                    board_rect.top + row * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                pygame.draw.rect(self.screen, Color.BLACK, cell_rect, 1)

    def _draw_stones(self, board, board_rect):
        for row in range(8):
            for col in range(8):
                if board[row][col] == 1:
                    self._draw_stone(board_rect, row, col, Color.WHITE)
                elif board[row][col] == -1:
                    self._draw_stone(board_rect, row, col, Color.BLACK)

    def _draw_stone(self, board_rect, row, col, color):
        center = (
            board_rect.left + col * self.cell_size + self.cell_size // 2,
            board_rect.top + row * self.cell_size + self.cell_size // 2
        )
        pygame.draw.circle(self.screen, color, center, self.cell_size // 2 - 5)

    def draw_board(self, game):
        board_rect = self._calculate_board_rect()
        self._draw_board_background(board_rect)
        self._draw_board_grid(board_rect)
        self._draw_stones(game.get_board(), board_rect)
        self._draw_stone_count(game, board_rect)

    def _draw_stone_count(self, game, board_rect):
        black_count, white_count = game.board.count_stones()
        # 石の数の表示位置を調整
        stone_count_top = board_rect.bottom + (self.screen_width - (board_rect.left + Screen.BOARD_SIZE))
        left_margin = board_rect.left  # ボードの左マージンを取得
        self._draw_text_with_position(f"黒: {black_count}", Color.BLACK, (left_margin, stone_count_top))
        self._draw_text_with_position(f"白: {white_count}", Color.WHITE, (self.screen_width - left_margin, stone_count_top), is_right_aligned=True)

    def _draw_text_with_position(self, text, color, pos, is_right_aligned=False):
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(topleft=pos)
        if is_right_aligned:
            text_rect.right = pos[0]
        self.screen.blit(text_surface, text_rect)

    def draw_valid_moves(self, game):
        board_rect = self._calculate_board_rect()
        valid_moves = game.get_valid_moves()
        for row, col in valid_moves:
            center = (
                board_rect.left + col * self.cell_size + self.cell_size // 2,
                board_rect.top + row * self.cell_size + self.cell_size // 2
            )
            pygame.draw.circle(self.screen, Color.GRAY, center, self.cell_size // 8)

    def draw_message(self, message, is_game_start=False, is_game_over=False):
        text_surface = self.font.render(message, True, Color.WHITE) if not is_game_start else None
        if text_surface is not None:
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, self._get_message_y_position(is_game_start, is_game_over)))
            self.screen.blit(text_surface, text_rect)

    def _get_message_y_position(self, is_game_start, is_game_over):
        if is_game_start:
            return Screen.GAME_START_MESSAGE_TOP_MARGIN
        elif is_game_over:
            # ゲームオーバー時のメッセージ位置を調整
            return self._get_message_y_position_in_game()
        else:
            return self._get_message_y_position_in_game()

    def _get_message_y_position_in_game(self):
        board_rect = self._calculate_board_rect()
        stone_count_top = board_rect.bottom + (self.screen_width - (board_rect.left + Screen.BOARD_SIZE))
        font_height = self.font.get_height()
        turn_message_top = stone_count_top + font_height + Screen.TURN_MESSAGE_TOP_MARGIN
        # 手番表示の直下の行に表示されるように調整
        return turn_message_top

    def get_clicked_cell(self, pos):
        board_rect = self._calculate_board_rect()
        if not board_rect.collidepoint(pos):
            return -1, -1
        col = (pos[0] - board_rect.left) // self.cell_size
        row = (pos[1] - board_rect.top) // self.cell_size
        return row, col

    def draw_stone_animation(self, game, row, col, color):
        board_rect = self._calculate_board_rect()
        center = (
            board_rect.left + col * self.cell_size + self.cell_size // 2,
            board_rect.top + row * self.cell_size + self.cell_size // 2
        )
        max_radius = self.cell_size // 2 - 5

        for radius in range(0, max_radius, 5):
            self.draw_board(game)
            self.draw_valid_moves(game)
            self.draw_message(game.get_message())
            pygame.draw.circle(self.screen, color, center, radius)
            pygame.display.flip()
            pygame.time.delay(10)

        pygame.draw.circle(self.screen, color, center, max_radius)
        pygame.display.flip()

    def draw_flip_animation(self, game, flipped_stones, color):
        board_rect = self._calculate_board_rect()
        other_color = Color.WHITE if color == Color.BLACK else Color.BLACK
        max_radius = self.cell_size // 2 - 5
        for i in range(10):
            self.draw_board(game)
            self.draw_valid_moves(game)
            self.draw_message(game.get_message())
            for fr, fc in flipped_stones:
                stone_center = (
                    board_rect.left + fc * self.cell_size + self.cell_size // 2,
                    board_rect.top + fr * self.cell_size + self.cell_size // 2
                )
                if i < 5:
                    pygame.draw.circle(self.screen, Color.GREEN, stone_center, max_radius - (max_radius / 5) * i)
                else:
                    pygame.draw.circle(self.screen, color, stone_center, (max_radius / 5) * (i - 4))
            pygame.display.flip()
            pygame.time.delay(10)

    def draw_start_button(self):
        button_rect = self._calculate_button_rect(True)
        return self._draw_button(button_rect, "ゲーム開始")

    def draw_restart_button(self, game_over=False):
        button_rect = self._calculate_button_rect(False, game_over)
        return self._draw_button(button_rect, "リスタート")

    def draw_reset_button(self, game_over=False):
        button_rect = self._calculate_button_rect(False, game_over, is_reset_button=True)
        return self._draw_button(button_rect, "リセット")

    def _calculate_button_rect(self, is_start_button, game_over=False, is_reset_button=False):
        text = "ゲーム開始" if is_start_button else ("リセット" if is_reset_button else "リスタート")
        text_surface = self.font.render(text, True, Color.BUTTON_TEXT)
        button_width = text_surface.get_width() + Screen.BUTTON_MARGIN * 2 + Screen.BUTTON_BORDER_WIDTH * 2
        button_height = text_surface.get_height() + Screen.BUTTON_VERTICAL_MARGIN * 2 + Screen.BUTTON_BORDER_WIDTH * 2

        if is_start_button:
            button_x = (self.screen_width - button_width) // 2
            button_y = (self.screen_height - button_height) // 2
        else:
            total_button_width = button_width * 2 + Screen.BUTTON_MARGIN
            start_x = (self.screen_width - total_button_width) // 2

            if game_over:
                # ゲームオーバー時のボタンの Y 座標を調整
                message_y = self._get_message_y_position_in_game()
                button_y = message_y + self.font.get_height() + Screen.MESSAGE_MARGIN
            else:
                # ゲーム中のボタンの Y 座標を手番表示の下に調整
                button_y = self._get_message_y_position_in_game() + Screen.MESSAGE_MARGIN #font_heightを削除

            button_x = start_x + button_width + Screen.BUTTON_MARGIN if is_reset_button else start_x

        return pygame.Rect(button_x, button_y, button_width, button_height)

    def _draw_button(self, button_rect, text):
        text_surface = self.font.render(text, True, Color.BUTTON_TEXT)
        text_rect = text_surface.get_rect(center=button_rect.center)
        pygame.draw.rect(self.screen, Color.BUTTON, button_rect)
        self._draw_button_border(button_rect)
        self.screen.blit(text_surface, text_rect)
        return button_rect

    def _draw_button_border(self, button_rect):
        pygame.draw.line(self.screen, Color.WHITE, button_rect.topleft, button_rect.bottomleft, Screen.BUTTON_BORDER_WIDTH)
        pygame.draw.line(self.screen, Color.WHITE, button_rect.topright, button_rect.bottomright, Screen.BUTTON_BORDER_WIDTH)
        pygame.draw.line(self.screen, Color.WHITE, button_rect.topleft, button_rect.topright, Screen.BUTTON_BORDER_WIDTH)
        pygame.draw.line(self.screen, Color.WHITE, button_rect.bottomleft, button_rect.bottomright, Screen.BUTTON_BORDER_WIDTH)

    def is_button_clicked(self, pos, button_rect):
        return button_rect.collidepoint(pos)

    def draw_radio_button(self, pos, selected, enabled=True):
        x, y = pos
        center = (x + Screen.RADIO_BUTTON_SIZE // 2, y + Screen.RADIO_BUTTON_SIZE // 2)

        # チェックボックスの枠を描画
        pygame.draw.circle(self.screen, Color.DARK_BLUE if enabled else Color.LIGHT_BLUE, center, Screen.RADIO_BUTTON_SIZE // 2, 1)

        if selected:
            # 選択状態の小さな円を描画
            inner_circle_radius = int(Screen.RADIO_BUTTON_SIZE * Screen.RADIO_BUTTON_INNER_CIRCLE_RATIO // 2)
            pygame.draw.circle(self.screen, Color.DARK_BLUE if enabled else Color.LIGHT_BLUE, center, inner_circle_radius)

    def draw_text(self, text, pos, enabled=True):
        color = Color.WHITE if enabled else Color.DISABLED_TEXT
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, pos)

    def draw_player_settings(self, game, player_settings_top, enabled=False):
        board_rect = self._calculate_board_rect()
        left_margin = board_rect.left

        black_player_label_pos = (left_margin, player_settings_top)
        white_player_label_pos = (self.screen_width // 2, player_settings_top)

        black_human_radio_pos = (black_player_label_pos[0], black_player_label_pos[1] + 30)
        black_random_radio_pos = (black_player_label_pos[0], black_human_radio_pos[1] + 30)
        white_human_radio_pos = (white_player_label_pos[0], white_player_label_pos[1] + 30)
        white_random_radio_pos = (white_player_label_pos[0], white_human_radio_pos[1] + 30)

        black_player_type = game.agents[-1]
        white_player_type = game.agents[1]

        self.draw_text("黒プレイヤー", black_player_label_pos) #enabledを削除
        self.draw_text("人間", (black_human_radio_pos[0] + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN, black_human_radio_pos[1])) #enabledを削除
        self.draw_text("ランダム", (black_random_radio_pos[0] + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN, black_random_radio_pos[1])) #enabledを削除
        self.draw_radio_button(black_human_radio_pos, black_player_type is None, enabled)
        self.draw_radio_button(black_random_radio_pos, black_player_type is not None, enabled)

        self.draw_text("白プレイヤー", white_player_label_pos) #enabledを削除
        self.draw_text("人間", (white_human_radio_pos[0] + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN, white_human_radio_pos[1])) #enabledを削除
        self.draw_text("ランダム", (white_random_radio_pos[0] + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN, white_random_radio_pos[1])) #enabledを削除
        self.draw_radio_button(white_human_radio_pos, white_player_type is None, enabled)
        self.draw_radio_button(white_random_radio_pos, white_player_type is not None, enabled)

    def draw_turn_message(self, game):
        message = f"{'黒' if game.turn == -1 else '白'}の番です"
        text_surface = self.font.render(message, True, Color.WHITE)
        text_rect = text_surface.get_rect(center=(self.screen_width // 2, self._get_message_y_position_in_game()))
        self.screen.blit(text_surface, text_rect)
