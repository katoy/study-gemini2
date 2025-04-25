# gui.py
import pygame
import os
from pathlib import Path
# --- config.agents からヘルパー関数をインポート ---
from config.agents import get_agent_options, get_agent_class
# --- config.theme からインポート ---
from config.theme import Color, Screen

class GameGUI:
    def __init__(self, screen_width=Screen.WIDTH, screen_height=Screen.HEIGHT):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Reversi")
        self.cell_size = Screen.CELL_SIZE # Screen.CELL_SIZE を使用
        self.font = self._load_font()
        # --- エージェントオプションをキャッシュ ---
        self.agent_options = get_agent_options()

    # --- ヘルパーメソッド ---
    def _calculate_turn_message_center_y(self):
        """手番表示の中心Y座標を計算する"""
        board_rect = self._calculate_board_rect()
        stone_count_y = board_rect.bottom + Screen.TURN_MESSAGE_TOP_MARGIN
        font_height = self.font.get_height()
        # 石数表示の下 + マージン + 手番表示テキストの高さの半分
        return stone_count_y + font_height + Screen.TURN_MESSAGE_TOP_MARGIN + font_height // 2

    def _calculate_button_height(self):
        """ボタンの高さを計算する"""
        # ダミーテキストで高さを計算
        text_surface = self.font.render("Button", True, Color.BUTTON_TEXT)
        return text_surface.get_height() + Screen.BUTTON_VERTICAL_MARGIN * 2 + Screen.BUTTON_BORDER_WIDTH * 2

    def _calculate_player_settings_height(self):
        """プレイヤー設定UIの高さを計算する"""
        font_height = self.font.get_height()
        num_options = len(self.agent_options) # self.agent_options を使う
        if num_options == 0:
            return font_height # ラベル分のみ
        # ラベル高さ + オフセット + (ラジオボタン数-1)*間隔 + ラジオボタンサイズ
        return font_height + Screen.RADIO_Y_OFFSET + Screen.RADIO_Y_SPACING * (num_options - 1) + Screen.RADIO_BUTTON_SIZE

    def _calculate_player_settings_top(self):
        """プレイヤー設定UIの上端Y座標を計算する"""
        # リスタート/リセット/終了ボタンの下端を基準にする
        # is_start=False, game_over=False, is_reset=False, is_quit=False でリスタートボタンのRectを取得
        # (ゲーム開始前でもリスタート/リセット/終了ボタンと同じ高さ・幅のボタンがあると仮定して計算)
        button_rect = self._calculate_button_rect(False, False, False, False) # リスタートボタンのRectを取得
        button_bottom = button_rect.bottom # ボタンの下端
        return button_bottom + Screen.BUTTON_BOTTOM_MARGIN # ボタンの下端 + マージン

    def _get_message_y_position(self, is_game_start=False, is_game_over=False):
        """メッセージの中心Y座標を取得する"""
        if is_game_start:
            # ゲーム開始時は特定の位置
            return Screen.GAME_START_MESSAGE_TOP_MARGIN
        elif is_game_over:
            # ゲームオーバー時は手番表示と同じ位置 (勝敗メッセージ用)
            return self._calculate_turn_message_center_y()
        else: # ゲーム中 (パスなどのメッセージ用)
            # 手番表示の上に表示
            turn_message_center_y = self._calculate_turn_message_center_y()
            font_height = self.font.get_height()
            # メッセージの中心Y = 手番表示中心Y - フォント高さ - マージン
            return turn_message_center_y - font_height - Screen.MESSAGE_ABOVE_TURN_MARGIN


    def _load_font(self):
        """同梱された日本語フォントをロードする"""
        # このファイルの場所を基準にフォントファイルへの相対パスを構築
        script_dir = Path(__file__).parent # gui.py があるディレクトリ
        # --- fonts ディレクトリを正しく参照するように修正 ---
        # プロジェクトルートからの相対パスではなく、gui.pyからの相対パスを使う
        font_dir = script_dir / "fonts"    # gui.py と同じ階層にある fonts ディレクトリ
        # -------------------------------------------------
        font_filename = "NotoSansJP-Regular.ttf" # 使用するフォントファイル名
        font_path = font_dir / font_filename

        font_size = 24

        if font_path.exists():
            try:
                return pygame.font.Font(str(font_path), font_size) # pathlib オブジェクトを文字列に変換
            except Exception as e:
                print(f"同梱フォントの読み込みに失敗しました ({font_path}): {e}")
        else:
            print(f"同梱フォントファイルが見つかりません: {font_path}")

        # 同梱フォントが読み込めなかった場合のフォールバック
        print("デフォルトフォント（英語）を使用します。")
        try:
            # 日本語は表示できないが、エラーにはなりにくいシステムフォントを試す
            return pygame.font.SysFont('sans', font_size)
        except Exception:
            # それも失敗した場合の最終手段
            print("システムフォントも利用できません。pygame デフォルトフォントを使用します。")
            return pygame.font.Font(None, font_size)


    def _calculate_board_rect(self):
        """盤面の描画領域(Rect)を計算する"""
        board_left = (self.screen_width - Screen.BOARD_SIZE) // 2
        board_top = Screen.BOARD_TOP_MARGIN
        return pygame.Rect(board_left, board_top, Screen.BOARD_SIZE, Screen.BOARD_SIZE)

    def _draw_board_background(self, board_rect):
        """画面背景と盤面の背景を描画する"""
        self.screen.fill(Color.BACKGROUND)
        pygame.draw.rect(self.screen, Color.BOARD, board_rect)

    def _draw_board_grid(self, board_rect):
        """盤面のグリッド線を描画する"""
        for row in range(8):
            for col in range(8):
                cell_rect = pygame.Rect(
                    board_rect.left + col * self.cell_size,
                    board_rect.top + row * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                pygame.draw.rect(self.screen, Color.BLACK, cell_rect, 1) # 線の太さ 1

    def _draw_stones(self, board, board_rect):
        """盤面上のすべての石を描画する"""
        for row in range(8):
            for col in range(8):
                if board[row][col] == 1: # 白石
                    self._draw_stone(board_rect, row, col, Color.WHITE)
                elif board[row][col] == -1: # 黒石
                    self._draw_stone(board_rect, row, col, Color.BLACK)

    def _draw_stone(self, board_rect, row, col, color):
        """指定された位置に石を描画する"""
        center = (
            board_rect.left + col * self.cell_size + self.cell_size // 2,
            board_rect.top + row * self.cell_size + self.cell_size // 2
        )
        pygame.draw.circle(self.screen, color, center, self.cell_size // 2 - 5) # 石の半径

    def draw_board(self, game):
        """盤面全体を描画する（背景、グリッド、石、石数）"""
        board_rect = self._calculate_board_rect()
        self._draw_board_background(board_rect)
        self._draw_board_grid(board_rect)
        self._draw_stones(game.get_board(), board_rect)
        self._draw_stone_count(game, board_rect)

    def _draw_stone_count(self, game, board_rect):
        """盤面下の石数を描画する"""
        black_count, white_count = game.board.count_stones()
        stone_count_y = board_rect.bottom + Screen.TURN_MESSAGE_TOP_MARGIN
        left_margin = board_rect.left
        # 黒石数 (左寄せ)
        self._draw_text_with_position(f"黒: {black_count}", Color.BLACK, (left_margin, stone_count_y))
        # 白石数 (右寄せ)
        self._draw_text_with_position(f"白: {white_count}", Color.WHITE, (self.screen_width - left_margin, stone_count_y), is_right_aligned=True)

    def _draw_text_with_position(self, text, color, pos, is_right_aligned=False):
        """指定された位置にテキストを描画する（右寄せオプション付き）"""
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(topleft=pos)
        if is_right_aligned:
            text_rect.right = pos[0] # 右端を指定したx座標に合わせる
        self.screen.blit(text_surface, text_rect)

    def draw_valid_moves(self, game):
        """合法手を示すマーカーを描画する"""
        board_rect = self._calculate_board_rect()
        valid_moves = game.get_valid_moves()
        for row, col in valid_moves:
            center = (
                board_rect.left + col * self.cell_size + self.cell_size // 2,
                board_rect.top + row * self.cell_size + self.cell_size // 2
            )
            pygame.draw.circle(self.screen, Color.GRAY, center, self.cell_size // 8) # マーカーの半径

    def draw_message(self, message, is_game_start=False, is_game_over=False):
        """画面中央にメッセージを描画する"""
        text_surface = self.font.render(message, True, Color.WHITE) if message else None
        if text_surface is not None:
            # メッセージの位置を状況に応じて計算
            y_pos = self._get_message_y_position(is_game_start, is_game_over)
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, y_pos))
            self.screen.blit(text_surface, text_rect)

    def get_clicked_cell(self, pos):
        """クリックされた座標が盤面のどのセルに対応するかを返す"""
        board_rect = self._calculate_board_rect()
        if not board_rect.collidepoint(pos):
            return -1, -1 # 盤面外
        # 盤面内の相対座標から行と列を計算
        col = (pos[0] - board_rect.left) // self.cell_size
        row = (pos[1] - board_rect.top) // self.cell_size
        return row, col

    def draw_stone_animation(self, game, row, col, color):
        """石が置かれるアニメーションを描画する"""
        board_rect = self._calculate_board_rect()
        center = (
            board_rect.left + col * self.cell_size + self.cell_size // 2,
            board_rect.top + row * self.cell_size + self.cell_size // 2
        )
        max_radius = self.cell_size // 2 - 5

        # 徐々に大きくなる円を描画
        for radius in range(0, max_radius, 5): # 半径を5ずつ増やす
            # アニメーション中に背景や他のUIも再描画
            self.draw_board(game)
            self.draw_turn_message(game)
            self.draw_message(game.get_message())
            self.draw_restart_button()
            self.draw_reset_button()
            self.draw_quit_button() # 終了ボタンも描画
            player_settings_top = self._calculate_player_settings_top()
            self.draw_player_settings(game, player_settings_top, False) # ゲーム中は設定無効
            # アニメーション中の石を描画
            pygame.draw.circle(self.screen, color, center, radius)
            pygame.display.flip() # 画面更新
            pygame.time.delay(10) # 短い待機時間

    def draw_flip_animation(self, game, flipped_stones, color):
        """石が裏返るアニメーションを描画する"""
        board_rect = self._calculate_board_rect()
        other_color = Color.WHITE if color == Color.BLACK else Color.BLACK
        max_radius = self.cell_size // 2 - 5

        # アニメーションのステップ数
        steps = 10
        for i in range(steps):
            # 現在の盤面状態を取得 (アニメーション中に他の石は固定)
            current_board_state = game.get_board()
            # 背景とグリッドを再描画
            self._draw_board_background(board_rect)
            self._draw_board_grid(board_rect)

            # 裏返らない石を描画
            for r in range(game.get_board_size()):
                for c in range(game.get_board_size()):
                    is_flipping = False
                    for fr, fc in flipped_stones:
                        if r == fr and c == fc:
                            is_flipping = True
                            break
                    if not is_flipping: # 裏返らない石
                        if current_board_state[r][c] == 1:
                            self._draw_stone(board_rect, r, c, Color.WHITE)
                        elif current_board_state[r][c] == -1:
                            self._draw_stone(board_rect, r, c, Color.BLACK)

            # 他のUI要素も再描画
            self.draw_turn_message(game)
            self.draw_message(game.get_message())
            self.draw_restart_button()
            self.draw_reset_button()
            self.draw_quit_button() # 終了ボタンも描画
            player_settings_top = self._calculate_player_settings_top()
            self.draw_player_settings(game, player_settings_top, False) # ゲーム中は設定無効

            # 裏返る石のアニメーション描画
            for fr, fc in flipped_stones:
                stone_center = (
                    board_rect.left + fc * self.cell_size + self.cell_size // 2,
                    board_rect.top + fr * self.cell_size + self.cell_size // 2
                )
                current_radius = 0
                current_color = other_color
                # アニメーション前半：元の色で縮小
                if i < steps // 2:
                    current_radius = max_radius * (1 - (i / (steps // 2)))
                    current_color = other_color
                # アニメーション後半：新しい色で拡大
                else:
                    current_radius = max_radius * ((i - steps // 2) / (steps // 2))
                    current_color = color
                pygame.draw.circle(self.screen, current_color, stone_center, int(current_radius))

            pygame.display.flip() # 画面更新
            pygame.time.delay(20) # アニメーション速度調整

    def draw_start_button(self):
        """ゲーム開始ボタンを描画する"""
        button_rect = self._calculate_button_rect(True) # is_start_button=True
        return self._draw_button(button_rect, "ゲーム開始")

    def draw_restart_button(self, game_over=False):
        """リスタートボタンを描画する"""
        # is_quit_button=False (デフォルト) を明示的に渡す (必須ではないが可読性のため)
        button_rect = self._calculate_button_rect(False, game_over, is_reset_button=False, is_quit_button=False)
        return self._draw_button(button_rect, "リスタート")

    def draw_reset_button(self, game_over=False):
        """リセットボタンを描画する"""
        button_rect = self._calculate_button_rect(False, game_over, is_reset_button=True, is_quit_button=False)
        return self._draw_button(button_rect, "リセット")

    # --- 追加: 終了ボタンを描画するメソッド ---
    def draw_quit_button(self, game_over=False):
        """終了ボタンを描画する"""
        button_rect = self._calculate_button_rect(False, game_over, is_reset_button=False, is_quit_button=True)
        return self._draw_button(button_rect, "終了")
    # ---------------------------------------

    # --- 修正: ボタンの位置計算ロジック ---
    def _calculate_button_rect(self, is_start_button, game_over=False, is_reset_button=False, is_quit_button=False): # is_quit_button 引数を追加
        """ボタンの描画領域(Rect)を計算する"""
        if is_start_button:
            text = "ゲーム開始"
        elif is_reset_button:
            text = "リセット"
        elif is_quit_button: # 終了ボタンのテキスト
            text = "終了"
        else: # リスタートボタン
            text = "リスタート"

        text_surface = self.font.render(text, True, Color.BUTTON_TEXT)
        # ボタン幅はテキストに応じて可変にする場合 (今回は固定幅とする)
        # button_width = text_surface.get_width() + Screen.BUTTON_MARGIN * 2 + Screen.BUTTON_BORDER_WIDTH * 2
        # 固定幅にする (例: "リスタート" の幅を基準にする)
        base_text_surface = self.font.render("リスタート", True, Color.BUTTON_TEXT)
        button_width = base_text_surface.get_width() + Screen.BUTTON_MARGIN * 2 + Screen.BUTTON_BORDER_WIDTH * 2
        button_height = self._calculate_button_height()

        if is_start_button:
            # ゲーム開始ボタンは画面中央付近
            button_x = (self.screen_width - button_width) // 2
            # 垂直方向も中央に配置 (調整が必要な場合あり)
            # button_y = (self.screen_height - button_height) // 2
            # プレイヤー設定の上に配置する場合
            player_settings_top = self._calculate_player_settings_top()
            player_settings_height = self._calculate_player_settings_height()
            # ゲーム開始ボタンのY座標をプレイヤー設定UIの上に配置するように調整
            # (プレイヤー設定UIの計算がボタン位置に依存しないように注意)
            # 仮のボタンY座標でプレイヤー設定Topを計算し、そこから逆算する
            # 1. ダミーのボタンYを計算 (手番表示の下)
            turn_message_center_y_dummy = self._calculate_turn_message_center_y()
            font_height_dummy = self.font.get_height()
            button_y_dummy = turn_message_center_y_dummy + font_height_dummy // 2 + Screen.TURN_MESSAGE_BOTTOM_MARGIN
            # 2. ダミーのボタンRectを作成
            button_rect_dummy = pygame.Rect(0, button_y_dummy, button_width, button_height)
            # 3. ダミーのボタンRectを使ってプレイヤー設定Topを計算
            player_settings_top_calc = button_rect_dummy.bottom + Screen.BUTTON_BOTTOM_MARGIN
            # 4. 実際のボタンYを計算
            button_y = player_settings_top_calc - button_height - Screen.BUTTON_BOTTOM_MARGIN

        else: # リスタート・リセット・終了ボタン
            # 3つのボタンを横に並べる
            total_button_width = button_width * 3 + Screen.BUTTON_MARGIN * 2 # 3つ分の幅と間のマージン2つ
            start_x = (self.screen_width - total_button_width) // 2
            # 手番表示の下に配置
            turn_message_center_y = self._calculate_turn_message_center_y()
            font_height = self.font.get_height()
            button_y = turn_message_center_y + font_height // 2 + Screen.TURN_MESSAGE_BOTTOM_MARGIN

            if is_reset_button: # 中央 (リセット)
                button_x = start_x + button_width + Screen.BUTTON_MARGIN
            elif is_quit_button: # 右 (終了)
                button_x = start_x + (button_width + Screen.BUTTON_MARGIN) * 2
            else: # 左 (リスタート)
                button_x = start_x

        return pygame.Rect(button_x, button_y, button_width, button_height)
    # -----------------------------------

    def _draw_button(self, button_rect, text):
        """指定された領域にボタンを描画する"""
        text_surface = self.font.render(text, True, Color.BUTTON_TEXT)
        text_rect = text_surface.get_rect(center=button_rect.center)
        # ボタン背景
        pygame.draw.rect(self.screen, Color.BUTTON, button_rect)
        # ボタン枠線
        self._draw_button_border(button_rect)
        # ボタンテキスト
        self.screen.blit(text_surface, text_rect)
        return button_rect # クリック判定用にRectを返す

    def _draw_button_border(self, button_rect):
        """ボタンの枠線を描画する"""
        # 立体感を出すために少しずらして線を描画しても良いが、シンプルに枠線を描画
        pygame.draw.rect(self.screen, Color.WHITE, button_rect, Screen.BUTTON_BORDER_WIDTH)

    def is_button_clicked(self, pos, button_rect):
        """指定された座標がボタンの領域内にあるか判定する"""
        # button_rect が None でないことも確認
        return button_rect is not None and button_rect.collidepoint(pos)

    def draw_radio_button(self, pos, selected, enabled=True):
        """ラジオボタンを描画する"""
        x, y = pos
        center = (x + Screen.RADIO_BUTTON_SIZE // 2, y + Screen.RADIO_BUTTON_SIZE // 2)
        # 外側の円
        outer_color = Color.DARK_BLUE if enabled else Color.LIGHT_BLUE # 無効時は薄い色
        pygame.draw.circle(self.screen, outer_color, center, Screen.RADIO_BUTTON_SIZE // 2, 1) # 線の太さ 1
        # 選択されている場合、内側の円を描画
        if selected:
            inner_color = Color.DARK_BLUE if enabled else Color.LIGHT_BLUE
            inner_circle_radius = int(Screen.RADIO_BUTTON_SIZE * Screen.RADIO_BUTTON_INNER_CIRCLE_RATIO // 2)
            pygame.draw.circle(self.screen, inner_color, center, inner_circle_radius)

    def draw_text(self, text, pos, enabled=True):
        """ラジオボタンの隣などにテキストを描画する"""
        color = Color.WHITE if enabled else Color.DISABLED_TEXT # 無効時は薄い色
        text_surface = self.font.render(text, True, color)
        # テキストの左上座標を指定
        text_rect = text_surface.get_rect(topleft=pos)
        self.screen.blit(text_surface, text_rect)

    def draw_player_settings(self, game, player_settings_top, enabled=False):
        """プレイヤー選択のラジオボタンUIを描画する (動的生成)"""
        board_rect = self._calculate_board_rect()
        left_margin = board_rect.left
        white_player_label_x = self.screen_width // 2 + Screen.RADIO_BUTTON_MARGIN

        # ラベル描画
        self._draw_text_with_position("黒プレイヤー", Color.WHITE, (left_margin, player_settings_top))
        self._draw_text_with_position("白プレイヤー", Color.WHITE, (white_player_label_x, player_settings_top))

        # ラジオボタンの垂直位置オフセットと間隔
        radio_y_offset = Screen.RADIO_Y_OFFSET
        radio_y_spacing = Screen.RADIO_Y_SPACING
        radio_text_x_offset = Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN

        # 現在選択されているエージェントを取得
        black_agent = game.agents[-1]
        white_agent = game.agents[1]

        # 黒プレイヤーのラジオボタンを描画
        for i, (agent_id, display_name) in enumerate(self.agent_options):
            radio_y = player_settings_top + radio_y_offset + i * radio_y_spacing
            radio_pos = (left_margin, radio_y)
            text_pos = (left_margin + radio_text_x_offset, radio_y)

            # 選択状態の判定
            is_selected = False
            if agent_id == 0: # 人間
                is_selected = (black_agent is None)
            else: # AIエージェント
                agent_class = get_agent_class(agent_id)
                if agent_class and black_agent:
                    is_selected = isinstance(black_agent, agent_class)

            self.draw_radio_button(radio_pos, is_selected, enabled)
            # テキストは常に有効な色で描画 (enabled フラグはボタン自体に適用)
            self._draw_text_with_position(display_name, Color.WHITE, text_pos)

        # 白プレイヤーのラジオボタンを描画
        for i, (agent_id, display_name) in enumerate(self.agent_options):
            radio_y = player_settings_top + radio_y_offset + i * radio_y_spacing
            radio_pos = (white_player_label_x, radio_y)
            text_pos = (white_player_label_x + radio_text_x_offset, radio_y)

            # 選択状態の判定
            is_selected = False
            if agent_id == 0: # 人間
                is_selected = (white_agent is None)
            else: # AIエージェント
                agent_class = get_agent_class(agent_id)
                if agent_class and white_agent:
                    is_selected = isinstance(white_agent, agent_class)

            self.draw_radio_button(radio_pos, is_selected, enabled)
            # テキストは常に有効な色で描画
            self._draw_text_with_position(display_name, Color.WHITE, text_pos)

    def draw_turn_message(self, game):
        """手番表示を描画する"""
        if game.game_over:
            return # ゲームオーバー時は表示しない
        message = f"{'黒' if game.turn == -1 else '白'}の番です"
        text_surface = self.font.render(message, True, Color.WHITE)
        # 手番表示のY座標を計算
        turn_message_center_y = self._calculate_turn_message_center_y()
        text_rect = text_surface.get_rect(center=(self.screen_width // 2, turn_message_center_y))
        self.screen.blit(text_surface, text_rect)

    # gui.py の GameGUI クラス内に追加
    def get_clicked_radio_button(self, click_pos, player_settings_top):
        """
        クリックされた位置がどのプレイヤーのどのラジオボタンに対応するかを返す。
        Args:
            click_pos (tuple[int, int]): マウスクリック座標。
            player_settings_top (int): プレイヤー設定UIの上端Y座標。
        Returns:
            tuple[int, int] | tuple[None, None]:
                クリックされた場合: (player (-1 or 1), agent_id)
                クリックされなかった場合: (None, None)
        """
        # agent_options がロードされているか確認 (通常は __init__ でロードされる)
        if not hasattr(self, 'agent_options') or not self.agent_options:
             print("Warning: agent_options not found in GUI. Radio button clicks won't work.")
             return None, None

        board_rect = self._calculate_board_rect()
        board_left = board_rect.left
        white_player_label_x = self.screen_width // 2 + Screen.RADIO_BUTTON_MARGIN
        radio_y_offset = Screen.RADIO_Y_OFFSET
        radio_y_spacing = Screen.RADIO_Y_SPACING
        radio_button_size = Screen.RADIO_BUTTON_SIZE

        for i, (agent_id, _) in enumerate(self.agent_options):
            radio_y = player_settings_top + radio_y_offset + i * radio_y_spacing

            # 黒プレイヤーのラジオボタンのRectを計算してクリック判定
            black_radio_rect = pygame.Rect(board_left, radio_y, radio_button_size, radio_button_size)
            if black_radio_rect.collidepoint(click_pos):
                return -1, agent_id # 黒プレイヤー、エージェントID

            # 白プレイヤーのラジオボタンのRectを計算してクリック判定
            white_radio_rect = pygame.Rect(white_player_label_x, radio_y, radio_button_size, radio_button_size)
            if white_radio_rect.collidepoint(click_pos):
                return 1, agent_id # 白プレイヤー、エージェントID

        return None, None # どのラジオボタンもクリックされなかった
