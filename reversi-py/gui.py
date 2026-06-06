# gui.py
import pygame
from pathlib import Path
# --- config.agents からヘルパー関数をインポート ---
from config.agents_config import get_agent_options, get_agent_class
# --- config.theme からインポート ---
from config.theme import Color, Screen
# --- config.i18n からインポート ---
from config.i18n import _t
# <<< 追加: ui_elements から UI要素をインポート >>>
from ui_elements import Button, RadioButton, Label
# ---------------------------------------------

class GameGUI:
    def __init__(self, screen_width=Screen.WIDTH, screen_height=Screen.HEIGHT):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Reversi")
        self.cell_size = Screen.CELL_SIZE # Screen.CELL_SIZE を使用
        self.font = self._load_font()
        # --- エージェントオプションをキャッシュ ---
        self.agent_options = get_agent_options()

        # --- ボタンインスタンスの生成 (Start ボタンのみ) ---
        # Start ボタンの Rect を計算
        start_rect = self._calculate_button_rect(is_start_button=True)
        # Start Button インスタンスを生成して保持
        self.start_button = Button(start_rect, _t("ui.start"), self.font)
        # 他のボタン (Restart, Reset, Quit) は描画時に都度生成する方針
        # -------------------------------------------------

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
        """同梱された日本語フォントをロードする

        Uses pygame._freetype when available to avoid pygame.font / pygame.sysfont
        circular-import issues on some environments. Wraps a freetype Font so
        callers can use .render(...) and .get_height() like pygame.font.Font.
        """
        # このファイルの場所を基準にフォントファイルへの相対パスを構築
        script_dir = Path(__file__).parent # gui.py があるディレクトリ
        # --- fonts ディレクトリを正しく参照するように修正 ---
        # プロジェクトルートからの相対パスではなく、gui.pyからの相対パスを使う
        font_dir = script_dir / "fonts"    # gui.py と同じ階層にある fonts ディレクトリ
        # -------------------------------------------------
        font_filename = "NotoSansJP-Regular.ttf" # 使用するフォントファイル名
        font_path = font_dir / font_filename

        font_size = 24

        # まず pygame._freetype を試して、問題があれば従来の pygame.font にフォールバックする
        try:
            import pygame._freetype as _freetype
            _freetype.init()

            class _FTFontWrapper:
                """Adapter that exposes a subset of pygame.font.Font's API
                (render(text, antialias, color, background=None) -> Surface,
                get_height() -> int) backed by pygame._freetype.Font.
                """
                def __init__(self, ff):
                    self._ff = ff

                def render(self, text, antialias, color, background=None):
                    # freetype.Font.render often returns (Surface, Rect)
                    # Normalize to return Surface like pygame.font.Font.render
                    try:
                        result = self._ff.render(text, fgcolor=color, bgcolor=background)
                    except TypeError:
                        # older signature fallback
                        result = self._ff.render(text, color, background)
                    if isinstance(result, tuple):
                        return result[0]
                    return result

                def get_height(self):
                    try:
                        return int(self._ff.get_sized_height())
                    except Exception:
                        return int(getattr(self._ff, 'height', font_size))

            if font_path.exists():
                ff_font = _freetype.Font(str(font_path), font_size)
            else:
                ff_font = _freetype.Font(None, font_size)
            return _FTFontWrapper(ff_font)
        except Exception as e:
            print(f"freetype font load failed: {e}")

        # ここから先は従来の pygame.font にフォールバック（環境によっては動作しない場合あり）
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

    # --- 描画メソッド ---
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
        Label((left_margin, stone_count_y), _t("game.black_stones", count=black_count), self.font, Color.BLACK).draw(self.screen)
        # 白石数 (右寄せ)
        Label((self.screen_width - left_margin, stone_count_y), _t("game.white_stones", count=white_count), self.font, Color.WHITE, is_right_aligned=True).draw(self.screen)

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
        if message:
            text_surface = self.font.render(message, True, Color.WHITE)
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

    # --- アニメーションメソッド (ボタン描画呼び出しを修正) ---
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
            # --- ボタン描画メソッド呼び出しを修正 ---
            self.draw_restart_button() # game_over フラグは不要に
            self.draw_reset_button()
            self.draw_quit_button()
            # ------------------------------------
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
            # --- ボタン描画メソッド呼び出しを修正 ---
            self.draw_restart_button()
            self.draw_reset_button()
            self.draw_quit_button()
            # ------------------------------------
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

    # --- ボタン描画メソッドの修正 ---
    def draw_start_button(self):
        """ゲーム開始ボタンを描画する"""
        # __init__ で生成したボタンインスタンスを描画
        self.start_button.draw(self.screen)
        # クリック判定用に Rect を返す必要はなくなる

    def draw_undo_button(self, game_over=False):
        """待ったボタンを描画する"""
        button_rect = self._calculate_button_rect(False, game_over, False, False, is_undo_button=True)
        button = Button(button_rect, _t("ui.undo"), self.font)
        button.draw(self.screen)

    def draw_restart_button(self, game_over=False):
        """リスタートボタンを描画する"""
        # 描画時に Button インスタンスを生成して描画
        button_rect = self._calculate_button_rect(False, game_over, False, False)
        button = Button(button_rect, _t("ui.restart"), self.font)
        button.draw(self.screen)

    def draw_reset_button(self, game_over=False):
        """リセットボタンを描画する"""
        button_rect = self._calculate_button_rect(False, game_over, True, False)
        button = Button(button_rect, _t("ui.reset"), self.font)
        button.draw(self.screen)

    def draw_quit_button(self, game_over=False):
        """終了ボタンを描画する"""
        button_rect = self._calculate_button_rect(False, game_over, False, True)
        button = Button(button_rect, _t("ui.quit"), self.font)
        button.draw(self.screen)
    # ---------------------------------

    def _calculate_button_rect(self, is_start_button=False, game_over=False, is_reset_button=False, is_quit_button=False, is_settings_button=False, is_undo_button=False):
        """ボタンの描画領域(Rect)を計算する"""
        # 固定幅にする (例: "リスタート" の幅を基準にする)
        base_text_surface = self.font.render(_t("ui.restart"), True, Color.BUTTON_TEXT)
        button_width = base_text_surface.get_width() + Screen.BUTTON_MARGIN * 2 + Screen.BUTTON_BORDER_WIDTH * 2
        button_height = self._calculate_button_height()

        if is_start_button:
            # ゲーム開始ボタンは画面中央付近
            button_x = (self.screen_width - button_width) // 2
            # プレイヤー設定の上に配置
            player_settings_top = self._calculate_player_settings_top()
            button_y = player_settings_top - button_height - Screen.BUTTON_BOTTOM_MARGIN

        elif is_settings_button: # 設定ボタン (右上)
            # 右上に配置
            button_x = self.screen_width - button_width - Screen.MARGIN # pragma: no cover
            button_y = Screen.MARGIN # pragma: no cover
            # (将来的に設定ダイアログなどを出すためのボタン)

        else: # 待った・リスタート・リセット・終了ボタン
            # 4つのボタンを横に並べる
            num_buttons = 4
            total_button_width = button_width * num_buttons + Screen.BUTTON_MARGIN * (num_buttons - 1)
            start_x = (self.screen_width - total_button_width) // 2
            # 手番表示の下に配置
            turn_message_center_y = self._calculate_turn_message_center_y()
            font_height = self.font.get_height()
            button_y = turn_message_center_y + font_height // 2 + Screen.TURN_MESSAGE_BOTTOM_MARGIN

            if is_undo_button: # 左端
                button_x = start_x
            elif is_reset_button: # 中央右
                button_x = start_x + (button_width + Screen.BUTTON_MARGIN) * 2
            elif is_quit_button: # 右端
                button_x = start_x + (button_width + Screen.BUTTON_MARGIN) * 3
            else: # リスタート (中央左)
                button_x = start_x + (button_width + Screen.BUTTON_MARGIN) * 1

        return pygame.Rect(button_x, button_y, button_width, button_height)
  # pragma: no cover

    # --- 不要になったメソッドを削除 ---
    # def _draw_button(self, button_rect, text): ...
    # def _draw_button_border(self, button_rect): ...
    # def is_button_clicked(self, pos, button_rect): ...
    # ---------------------------------

    def draw_player_settings(self, game, player_settings_top, enabled=False):
        """プレイヤー選択のラジオボタンUIを描画する (動的生成)"""
        board_rect = self._calculate_board_rect()
        left_margin = board_rect.left
        white_player_label_x = self.screen_width // 2 + Screen.RADIO_BUTTON_MARGIN

        # ラベル描画
        Label((left_margin, player_settings_top), _t("ui.black_player"), self.font).draw(self.screen)
        Label((white_player_label_x, player_settings_top), _t("ui.white_player"), self.font).draw(self.screen)

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
                    is_selected = isinstance(black_agent, agent_class) # pragma: no cover
                else: # pragma: no cover
                    is_selected = False # pragma: no cover

            RadioButton(radio_pos, Screen.RADIO_BUTTON_SIZE, is_selected, enabled).draw(self.screen)
            # テキストは常に有効な色で描画 (enabled フラグはボタン自体に適用)
            Label(text_pos, display_name, self.font).draw(self.screen)

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
                else: # pragma: no cover
                    is_selected = False # pragma: no cover

            RadioButton(radio_pos, Screen.RADIO_BUTTON_SIZE, is_selected, enabled).draw(self.screen)
            # テキストは常に有効な色で描画
            Label(text_pos, display_name, self.font).draw(self.screen)

    def draw_turn_message(self, game):
        """手番表示を描画する"""
        if game.game_over:
            return  # ゲームオーバー時は表示しない
        message = _t("game.black_turn") if game.turn == -1 else _t("game.white_turn")
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
             print("Warning: agent_options not found in GUI. Radio button clicks won't work.") # pragma: no cover
             return None, None # pragma: no cover

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

    # --- <<< 追加: ボタンクリック判定メソッド >>> ---
    def is_start_button_clicked(self, pos: tuple[int, int]) -> bool:
        """スタートボタンがクリックされたか判定"""
        # start_button は __init__ で生成され、draw_start_button で Rect が更新される
        # draw_start_button が呼ばれる前にクリックされる可能性があるので、ここで Rect を計算する方が安全
        start_rect = self._calculate_button_rect(is_start_button=True)
        # start_button インスタンスの is_clicked を使うのではなく、一時的な Button で判定
        return Button(start_rect, "", self.font).is_clicked(pos)
        # または、self.start_button.rect が常に最新であると仮定するなら以下でも可
        # return self.start_button.is_clicked(pos)

    def is_restart_button_clicked(self, pos: tuple[int, int], game_over: bool) -> bool:
        """リスタートボタンがクリックされたか判定"""
        button_rect = self._calculate_button_rect(False, game_over, False, False)
        # 一時的な Button インスタンスで判定
        return Button(button_rect, "", self.font).is_clicked(pos)

    def is_reset_button_clicked(self, pos: tuple[int, int], game_over: bool) -> bool:
        """リセットボタンがクリックされたか判定"""
        button_rect = self._calculate_button_rect(False, game_over, True, False)
        return Button(button_rect, "", self.font).is_clicked(pos)

    def is_quit_button_clicked(self, pos: tuple[int, int], game_over: bool) -> bool:
        """終了ボタンがクリックされたか判定"""
        button_rect = self._calculate_button_rect(False, game_over, False, True)
        return Button(button_rect, "", self.font).is_clicked(pos)

    def is_undo_button_clicked(self, pos: tuple[int, int], game_over: bool) -> bool:
        """待ったボタンがクリックされたか判定"""
        button_rect = self._calculate_button_rect(False, game_over, False, False, is_undo_button=True)
        return Button(button_rect, "", self.font).is_clicked(pos)

    def is_settings_button_clicked(self, pos: tuple[int, int]) -> bool:
        """設定ボタンがクリックされたか判定"""
        settings_rect = self._calculate_button_rect(is_settings_button=True)
        return Button(settings_rect, "", self.font).is_clicked(pos)
    # ---------------------------------------------
