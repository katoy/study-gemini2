# gui.py
import pygame
import os
# 必要なエージェントクラスをインポート
from agents import RandomAgent, GainAgent, FirstAgent # HumanAgent は game.py で None として扱われるため、直接インポートは不要

# 色の定義
class Color:
    # ... (変更なし) ...
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 128, 0)
    GRAY = (128, 128, 128)
    BOARD = (0, 128, 0)
    BACKGROUND = (100, 100, 100)
    BUTTON = (50, 50, 50)
    BUTTON_TEXT = (200, 200, 200)
    DISABLED_TEXT = (100, 100, 100)
    DARK_BLUE = (0, 0, 128)
    LIGHT_BLUE = (173, 216, 230)

# 画面サイズとマージンの定義
class Screen:
    WIDTH = 450
    HEIGHT = 780 # UI要素が収まるように調整
    BOARD_SIZE = 400
    BOARD_TOP_MARGIN = 0
    BUTTON_MARGIN = 10
    BUTTON_VERTICAL_MARGIN = 3
    # --- マージン定義 ---
    TURN_MESSAGE_TOP_MARGIN = 10 # 石数表示と手番表示の間のマージン
    TURN_MESSAGE_BOTTOM_MARGIN = 15 # 手番表示とボタンの間のマージン
    BUTTON_BOTTOM_MARGIN = 15 # ボタンとプレイヤー設定UIの間のマージン
    PLAYER_SETTINGS_BOTTOM_MARGIN = 20 # プレイヤー設定UIとメッセージの間のマージン (現在は未使用)
    MESSAGE_MARGIN = 20 # メッセージと下端 or 他要素とのマージン (現在は未使用)
    MESSAGE_ABOVE_TURN_MARGIN = 10 # メッセージと手番表示の間のマージン (追加)
    # --------------------
    GAME_START_MESSAGE_TOP_MARGIN = 200
    RADIO_BUTTON_SIZE = 24
    RADIO_BUTTON_MARGIN = 10
    BUTTON_BORDER_WIDTH = 2
    CELL_SIZE = BOARD_SIZE // 8
    RADIO_BUTTON_INNER_CIRCLE_RATIO = 0.4
    RADIO_Y_OFFSET = 30
    RADIO_Y_SPACING = 30

class GameGUI:
    def __init__(self, screen_width=Screen.WIDTH, screen_height=Screen.HEIGHT):
        # ... (変更なし) ...
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Reversi")
        self.cell_size = Screen.CELL_SIZE
        self.font = self._load_font()

    # --- ヘルパーメソッド ---
    def _calculate_turn_message_center_y(self):
        # ... (変更なし) ...
        board_rect = self._calculate_board_rect()
        stone_count_y = board_rect.bottom + Screen.TURN_MESSAGE_TOP_MARGIN
        font_height = self.font.get_height()
        return stone_count_y + font_height + Screen.TURN_MESSAGE_TOP_MARGIN + font_height // 2

    def _calculate_button_height(self):
        # ... (変更なし) ...
        text_surface = self.font.render("Button", True, Color.BUTTON_TEXT)
        return text_surface.get_height() + Screen.BUTTON_VERTICAL_MARGIN * 2 + Screen.BUTTON_BORDER_WIDTH * 2

    def _calculate_player_settings_height(self):
        # ... (変更なし) ...
        font_height = self.font.get_height()
        return font_height + Screen.RADIO_Y_OFFSET + Screen.RADIO_Y_SPACING * 3 + Screen.RADIO_BUTTON_SIZE

    def _calculate_player_settings_top(self):
        # ... (変更なし) ...
        button_rect = self._calculate_button_rect(False, False, False)
        button_y = button_rect.top
        button_height = button_rect.height
        return button_y + button_height + Screen.BUTTON_BOTTOM_MARGIN

    # --- メッセージ位置計算修正 ---
    def _get_message_y_position(self, is_game_start=False, is_game_over=False):
        """メッセージの中心Y座標を取得する"""
        if is_game_start:
            # ゲーム開始時は特定の位置
            return Screen.GAME_START_MESSAGE_TOP_MARGIN
        elif is_game_over:
            # ゲームオーバー時は手番表示と同じ位置
            return self._calculate_turn_message_center_y()
        else: # ゲーム中
            # 手番表示の上に表示
            turn_message_center_y = self._calculate_turn_message_center_y()
            font_height = self.font.get_height()
            # メッセージの中心Y = 手番表示中心Y - フォント高さ - マージン
            return turn_message_center_y - font_height - Screen.MESSAGE_ABOVE_TURN_MARGIN
    # --------------------------------

    def _load_font(self):
        # ... (変更なし) ...
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
        # ... (変更なし) ...
        board_left = (self.screen_width - Screen.BOARD_SIZE) // 2
        board_top = Screen.BOARD_TOP_MARGIN
        return pygame.Rect(board_left, board_top, Screen.BOARD_SIZE, Screen.BOARD_SIZE)

    def _draw_board_background(self, board_rect):
        # ... (変更なし) ...
        self.screen.fill(Color.BACKGROUND)
        pygame.draw.rect(self.screen, Color.BOARD, board_rect)

    def _draw_board_grid(self, board_rect):
        # ... (変更なし) ...
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
        # ... (変更なし) ...
        for row in range(8):
            for col in range(8):
                if board[row][col] == 1:
                    self._draw_stone(board_rect, row, col, Color.WHITE)
                elif board[row][col] == -1:
                    self._draw_stone(board_rect, row, col, Color.BLACK)

    def _draw_stone(self, board_rect, row, col, color):
        # ... (変更なし) ...
        center = (
            board_rect.left + col * self.cell_size + self.cell_size // 2,
            board_rect.top + row * self.cell_size + self.cell_size // 2
        )
        pygame.draw.circle(self.screen, color, center, self.cell_size // 2 - 5)

    def draw_board(self, game):
        # ... (変更なし) ...
        board_rect = self._calculate_board_rect()
        self._draw_board_background(board_rect)
        self._draw_board_grid(board_rect)
        self._draw_stones(game.get_board(), board_rect)
        self._draw_stone_count(game, board_rect)

    def _draw_stone_count(self, game, board_rect):
        # ... (変更なし) ...
        black_count, white_count = game.board.count_stones()
        stone_count_y = board_rect.bottom + Screen.TURN_MESSAGE_TOP_MARGIN
        left_margin = board_rect.left
        self._draw_text_with_position(f"黒: {black_count}", Color.BLACK, (left_margin, stone_count_y))
        self._draw_text_with_position(f"白: {white_count}", Color.WHITE, (self.screen_width - left_margin, stone_count_y), is_right_aligned=True)

    def _draw_text_with_position(self, text, color, pos, is_right_aligned=False):
        # ... (変更なし) ...
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(topleft=pos)
        if is_right_aligned:
            text_rect.right = pos[0]
        self.screen.blit(text_surface, text_rect)

    def draw_valid_moves(self, game):
        # ... (変更なし) ...
        board_rect = self._calculate_board_rect()
        valid_moves = game.get_valid_moves()
        for row, col in valid_moves:
            center = (
                board_rect.left + col * self.cell_size + self.cell_size // 2,
                board_rect.top + row * self.cell_size + self.cell_size // 2
            )
            pygame.draw.circle(self.screen, Color.GRAY, center, self.cell_size // 8)

    def draw_message(self, message, is_game_start=False, is_game_over=False):
        # ... (変更なし) ...
        text_surface = self.font.render(message, True, Color.WHITE) if message else None
        if text_surface is not None:
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, self._get_message_y_position(is_game_start, is_game_over)))
            self.screen.blit(text_surface, text_rect)

    def get_clicked_cell(self, pos):
        # ... (変更なし) ...
        board_rect = self._calculate_board_rect()
        if not board_rect.collidepoint(pos):
            return -1, -1
        col = (pos[0] - board_rect.left) // self.cell_size
        row = (pos[1] - board_rect.top) // self.cell_size
        return row, col

    def draw_stone_animation(self, game, row, col, color):
        # ... (変更なし) ...
        board_rect = self._calculate_board_rect()
        center = (
            board_rect.left + col * self.cell_size + self.cell_size // 2,
            board_rect.top + row * self.cell_size + self.cell_size // 2
        )
        max_radius = self.cell_size // 2 - 5

        for radius in range(0, max_radius, 5):
            self.draw_board(game)
            self.draw_turn_message(game)
            self.draw_message(game.get_message())
            self.draw_restart_button()
            self.draw_reset_button()
            player_settings_top = self._calculate_player_settings_top()
            self.draw_player_settings(game, player_settings_top, False)
            pygame.draw.circle(self.screen, color, center, radius)
            pygame.display.flip()
            pygame.time.delay(10)

    def draw_flip_animation(self, game, flipped_stones, color):
        # ... (変更なし) ...
        board_rect = self._calculate_board_rect()
        other_color = Color.WHITE if color == Color.BLACK else Color.BLACK
        max_radius = self.cell_size // 2 - 5
        for i in range(10):
            current_board_state = game.get_board()
            self._draw_board_background(board_rect)
            self._draw_board_grid(board_rect)
            for r in range(game.get_board_size()):
                for c in range(game.get_board_size()):
                    is_flipping = False
                    for fr, fc in flipped_stones:
                        if r == fr and c == fc:
                            is_flipping = True
                            break
                    if not is_flipping:
                        if current_board_state[r][c] == 1:
                            self._draw_stone(board_rect, r, c, Color.WHITE)
                        elif current_board_state[r][c] == -1:
                            self._draw_stone(board_rect, r, c, Color.BLACK)
            self.draw_turn_message(game)
            self.draw_message(game.get_message())
            self.draw_restart_button()
            self.draw_reset_button()
            player_settings_top = self._calculate_player_settings_top()
            self.draw_player_settings(game, player_settings_top, False)
            for fr, fc in flipped_stones:
                stone_center = (
                    board_rect.left + fc * self.cell_size + self.cell_size // 2,
                    board_rect.top + fr * self.cell_size + self.cell_size // 2
                )
                current_radius = 0
                current_color = other_color
                if i < 5:
                    current_radius = max_radius * (1 - i / 5.0)
                    current_color = other_color
                else:
                    current_radius = max_radius * ((i - 5) / 5.0)
                    current_color = color
                pygame.draw.circle(self.screen, current_color, stone_center, int(current_radius))
            pygame.display.flip()
            pygame.time.delay(20)

    def draw_start_button(self):
        # ... (変更なし) ...
        button_rect = self._calculate_button_rect(True)
        return self._draw_button(button_rect, "ゲーム開始")

    def draw_restart_button(self, game_over=False):
        # ... (変更なし) ...
        button_rect = self._calculate_button_rect(False, game_over)
        return self._draw_button(button_rect, "リスタート")

    def draw_reset_button(self, game_over=False):
        # ... (変更なし) ...
        button_rect = self._calculate_button_rect(False, game_over, is_reset_button=True)
        return self._draw_button(button_rect, "リセット")

    def _calculate_button_rect(self, is_start_button, game_over=False, is_reset_button=False):
        # ... (変更なし) ...
        text = "ゲーム開始" if is_start_button else ("リセット" if is_reset_button else "リスタート")
        text_surface = self.font.render(text, True, Color.BUTTON_TEXT)
        button_width = text_surface.get_width() + Screen.BUTTON_MARGIN * 2 + Screen.BUTTON_BORDER_WIDTH * 2
        button_height = self._calculate_button_height()

        if is_start_button:
            button_x = (self.screen_width - button_width) // 2
            button_y = self.screen_height // 2 - button_height // 2
        else: # リスタート・リセットボタン
            total_button_width = button_width * 2 + Screen.BUTTON_MARGIN
            start_x = (self.screen_width - total_button_width) // 2
            turn_message_center_y = self._calculate_turn_message_center_y()
            font_height = self.font.get_height()
            button_y = turn_message_center_y + font_height // 2 + Screen.TURN_MESSAGE_BOTTOM_MARGIN
            button_x = start_x + button_width + Screen.BUTTON_MARGIN if is_reset_button else start_x

        return pygame.Rect(button_x, button_y, button_width, button_height)

    def _draw_button(self, button_rect, text):
        # ... (変更なし) ...
        text_surface = self.font.render(text, True, Color.BUTTON_TEXT)
        text_rect = text_surface.get_rect(center=button_rect.center)
        pygame.draw.rect(self.screen, Color.BUTTON, button_rect)
        self._draw_button_border(button_rect)
        self.screen.blit(text_surface, text_rect)
        return button_rect

    def _draw_button_border(self, button_rect):
        # ... (変更なし) ...
        pygame.draw.line(self.screen, Color.WHITE, button_rect.topleft, button_rect.bottomleft, Screen.BUTTON_BORDER_WIDTH)
        pygame.draw.line(self.screen, Color.WHITE, button_rect.topright, button_rect.bottomright, Screen.BUTTON_BORDER_WIDTH)
        pygame.draw.line(self.screen, Color.WHITE, button_rect.topleft, button_rect.topright, Screen.BUTTON_BORDER_WIDTH)
        pygame.draw.line(self.screen, Color.WHITE, button_rect.bottomleft, button_rect.bottomright, Screen.BUTTON_BORDER_WIDTH)

    def is_button_clicked(self, pos, button_rect):
        # ... (変更なし) ...
        return button_rect is not None and button_rect.collidepoint(pos)

    def draw_radio_button(self, pos, selected, enabled=True):
        # ... (変更なし) ...
        x, y = pos
        center = (x + Screen.RADIO_BUTTON_SIZE // 2, y + Screen.RADIO_BUTTON_SIZE // 2)
        outer_color = Color.DARK_BLUE if enabled else Color.LIGHT_BLUE
        pygame.draw.circle(self.screen, outer_color, center, Screen.RADIO_BUTTON_SIZE // 2, 1)
        if selected:
            inner_color = Color.DARK_BLUE if enabled else Color.LIGHT_BLUE
            inner_circle_radius = int(Screen.RADIO_BUTTON_SIZE * Screen.RADIO_BUTTON_INNER_CIRCLE_RATIO // 2)
            pygame.draw.circle(self.screen, inner_color, center, inner_circle_radius)

    def draw_text(self, text, pos, enabled=True):
        # ... (変更なし) ...
        color = Color.WHITE
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, pos)

    def draw_player_settings(self, game, player_settings_top, enabled=False):
        # ... (変更なし) ...
        board_rect = self._calculate_board_rect()
        left_margin = board_rect.left
        black_player_label_pos = (left_margin, player_settings_top)
        white_player_label_pos = (self.screen_width // 2, player_settings_top)
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
        black_agent = game.agents[-1]
        white_agent = game.agents[1]
        self.draw_text("黒プレイヤー", black_player_label_pos, enabled)
        self.draw_radio_button(black_human_radio_pos, black_agent is None, enabled)
        self.draw_text("人間", (black_human_radio_pos[0] + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN, black_human_radio_pos[1]), enabled)
        self.draw_radio_button(black_first_radio_pos, isinstance(black_agent, FirstAgent), enabled)
        self.draw_text("First", (black_first_radio_pos[0] + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN, black_first_radio_pos[1]), enabled)
        self.draw_radio_button(black_random_radio_pos, isinstance(black_agent, RandomAgent), enabled)
        self.draw_text("Random", (black_random_radio_pos[0] + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN, black_random_radio_pos[1]), enabled)
        self.draw_radio_button(black_gain_radio_pos, isinstance(black_agent, GainAgent), enabled)
        self.draw_text("Gain", (black_gain_radio_pos[0] + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN, black_gain_radio_pos[1]), enabled)
        self.draw_text("白プレイヤー", white_player_label_pos, enabled)
        self.draw_radio_button(white_human_radio_pos, white_agent is None, enabled)
        self.draw_text("人間", (white_human_radio_pos[0] + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN, white_human_radio_pos[1]), enabled)
        self.draw_radio_button(white_first_radio_pos, isinstance(white_agent, FirstAgent), enabled)
        self.draw_text("First", (white_first_radio_pos[0] + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN, white_first_radio_pos[1]), enabled)
        self.draw_radio_button(white_random_radio_pos, isinstance(white_agent, RandomAgent), enabled)
        self.draw_text("Random", (white_random_radio_pos[0] + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN, white_random_radio_pos[1]), enabled)
        self.draw_radio_button(white_gain_radio_pos, isinstance(white_agent, GainAgent), enabled)
        self.draw_text("Gain", (white_gain_radio_pos[0] + Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN, white_gain_radio_pos[1]), enabled)

    def draw_turn_message(self, game):
        """手番表示を描画する"""
        if game.game_over:
            return # ゲームオーバー時は表示しない
        message = f"{'黒' if game.turn == -1 else '白'}の番です"
        text_surface = self.font.render(message, True, Color.WHITE)
        turn_message_center_y = self._calculate_turn_message_center_y()
        text_rect = text_surface.get_rect(center=(self.screen_width // 2, turn_message_center_y))
        self.screen.blit(text_surface, text_rect)
