# gui.py
import pygame  # noqa: E402
pygame.init()  # pygame 初期化を先に実行して pygame.font モジュールの循環インポートを回避

from pathlib import Path  # noqa: E402
from typing import TYPE_CHECKING, Optional  # noqa: E402
# --- config.agents からヘルパー関数をインポート ---
from config.agents_config import get_agent_options  # noqa: E402
# --- config.theme からインポート ---
from config.theme import Color, Screen  # noqa: E402
# --- config.i18n からインポート ---
from config.i18n import _t  # noqa: E402
# <<< 追加: ui_elements から UI要素をインポート >>>
from ui_elements import Button, RadioButton, Label  # noqa: E402
# ---------------------------------------------

if TYPE_CHECKING:
    from analysis.models import GameAnalysis

class GameGUI:
    """Pygame ベースのリバーシゲーム UI。

    責務：
    1. レイアウト計算：ウィンドウサイズ、要素の配置座標を計算
    2. UI描画：盤面、石、ボタン、テキストなどを pygame に描画
    3. 入力処理：マウスクリックから盤面座標やボタンクリックを検出

    構造：
    - __init__ 直後：初期化・キャッシュ設定
    - _calculate_* メソッド：レイアウト計算（座標・サイズ）
    - draw_* メソッド：UI 要素の描画
    - get_clicked_* メソッド：入力検出（マウス座標 → 盤面/UI 要素）

    注記：
    将来的に GameLayout クラスに計算ロジックを分離予定。
    現在は単一クラスで管理し、メソッドを責務別にグループ化。
    """
    def __init__(self, screen_width=Screen.WIDTH, screen_height=Screen.HEIGHT, allow_width_shrink: bool = False):
        """Game GUI initializer.

        Args:
            screen_width (int): Requested initial width.
            screen_height (int): Requested initial height.
            allow_width_shrink (bool): If True, GUI will reduce the requested
                screen_width down to the minimal width needed (helpful for
                default-app behavior to remove large side margins). Tests and
                callers that pass an explicit width should keep this False to
                preserve explicit sizing.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        # --- エージェントオプションをキャッシュ ---
        # compute_min_height や player settings 計算で agent_options を参照するため
        self.agent_options = get_agent_options()
        # フォントを先に読み込み、必要な最小高さを計算してウィンドウ高さを調整する
        self.font = self._load_font(font_size=18)
        # agent ラベル用の小さいフォント
        self.agent_label_font = self._load_font(font_size=14)
        # テキスト描画のキャッシング（毎フレーム同じテキストの render を避ける）
        self._text_cache: dict[tuple[str, tuple[int, int, int]], pygame.Surface] = {}
        # 盤面領域計算のキャッシング（ウィンドウサイズが変わらなければ再計算を避ける）
        self._board_rect_cache: pygame.Rect | None = None
        self._cached_screen_size: tuple[int, int] | None = None
        # ボタン領域計算のキャッシング（状態とウィンドウサイズが変わらなければ再計算を避ける）
        self._button_rect_cache: dict[tuple[bool, ...], pygame.Rect] = {}
        # Button / Label インスタンスのキャッシング
        # （毎フレームの生成は font.render を伴い高コストなため）
        self._button_cache: dict[tuple, Button] = {}
        self._label_cache: dict[tuple, Label] = {}
        # プレイヤー設定のスクロール位置（ピクセル）
        self._player_settings_scroll = 0
        # 解説パネルのスクロール位置（ピクセル）
        self._analysis_scroll = 0
        # 必要な高さを計算し、指定された高さより大きければ調整する
        required_height = self._compute_min_height()
        if self.screen_height < required_height:
            self.screen_height = required_height
        # 必要な最小幅を計算して、指定された幅が大きすぎる場合は縮小して余白を小さくする
        required_width = self._compute_min_width()
        # Shrink width only if caller explicitly opted in to avoid surprising tests/callers
        if allow_width_shrink and self.screen_width > required_width:
            self.screen_width = required_width

        # ディスプレイを初期化
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Reversi")
        self.cell_size = Screen.CELL_SIZE # Screen.CELL_SIZE を使用

        # --- ボタンインスタンスの生成 (Start ボタンのみ) ---
        # Start ボタンの Rect を計算
        start_rect = self._calculate_button_rect(is_start_button=True)
        # Start Button インスタンスを生成して保持
        self.start_button = Button(start_rect, _t("ui.start"), self.font)
        # 他のボタン (Restart, Reset, Quit) は描画時に都度生成する方針
        # -------------------------------------------------

    # === ヘルパー ===
    def _get_rendered_text(self, text, color=Color.WHITE):
        """テキストを描画し、キャッシュする"""
        cache_key = (text, color)
        if cache_key not in self._text_cache:
            self._text_cache[cache_key] = self.font.render(text, True, color)
        return self._text_cache[cache_key]

    def _get_button(self, rect: pygame.Rect, text: str) -> Button:
        """Button インスタンスをキャッシュから取得する（なければ生成）"""
        cache_key = (rect.x, rect.y, rect.width, rect.height, text)
        if cache_key not in self._button_cache:
            self._button_cache[cache_key] = Button(rect, text, self.font)
        return self._button_cache[cache_key]

    def _get_label(self, pos, text, color=Color.WHITE, is_right_aligned=False, font=None) -> Label:
        """Label インスタンスをキャッシュから取得する（なければ生成）"""
        if font is None:
            font = self.font
        cache_key = (pos, text, color, is_right_aligned, id(font))
        if cache_key not in self._label_cache:
            self._label_cache[cache_key] = Label(pos, text, font, color, is_right_aligned)
        return self._label_cache[cache_key]

    # === レイアウト計算・初期化 ===
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
        text_surface = self._get_rendered_text("Button", Color.BUTTON_TEXT)
        return text_surface.get_height() + Screen.BUTTON_VERTICAL_MARGIN * 2 + Screen.BUTTON_BORDER_WIDTH * 2

    def _calculate_player_settings_height(self):
        """プレイヤー設定UIの高さを計算する"""
        font_height = self.font.get_height()
        num_options = len(self.agent_options) # self.agent_options を使う
        if num_options == 0:
            return font_height # ラベル分のみ
        # ラベル高さ + オフセット + (ラジオボタン数-1)*間隔 + ラジオボタンサイズ
        return font_height + Screen.RADIO_Y_OFFSET + Screen.RADIO_Y_SPACING * (num_options - 1) + Screen.RADIO_BUTTON_SIZE

    def _calculate_player_settings_header_height(self):
        """プレイヤー設定UIのヘッダー（黒/白プレイヤーのラベル）と余白の高さを計算する"""
        return self.font.get_height() + Screen.RADIO_Y_OFFSET

    def _calculate_player_settings_list_height(self):
        """ラジオボタン一覧（ヘッダーを除く）の高さを計算する"""
        if not self.agent_options:
            return 0
        return self._calculate_player_settings_height() - self._calculate_player_settings_header_height()

    def _calculate_player_settings_viewport_height(self):
        """ラジオボタン一覧の表示領域の高さを計算する"""
        return min(self._calculate_player_settings_list_height(), Screen.PLAYER_SETTINGS_VIEWPORT_MAX_HEIGHT)

    def _calculate_player_settings_layout_height(self):
        """ヘッダーと表示領域を合わせたプレイヤー設定UIの画面上の高さを計算する"""
        if not self.agent_options:
            return self.font.get_height()
        return self._calculate_player_settings_header_height() + self._calculate_player_settings_viewport_height()

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


    def _load_font(self, font_size=14):
        """同梱された日本語フォントをロードする

        Prefer pygame.font when available (helps tests that mock it).
        Falls back to pygame._freetype only if pygame.font.* is unusable.
        """
        script_dir = Path(__file__).parent
        font_dir = script_dir / "fonts"
        font_filename = "NotoSansJP-Regular.ttf"
        font_path = font_dir / font_filename

        # Evaluate existence once to avoid multiple stat calls (tests assert single call)
        try:
            font_exists = font_path.exists()
        except Exception:
            font_exists = False

        # Detect if pygame.font module is usable; if accessing it raises a
        # NotImplementedError (circular import), skip direct pygame.font usage.
        font_module_unusable = False
        try:
            _ = hasattr(pygame, 'font')
        except Exception:
            font_module_unusable = True

        # 1) If bundled font file exists, try loading via pygame.font.Font(path)
        if not font_module_unusable and font_exists:
            try:
                font_obj = pygame.font.Font(str(font_path), font_size)
                if hasattr(font_obj, 'render') and hasattr(font_obj, 'get_height'):
                    return font_obj
            except Exception as e:
                # Failed to load bundled font via pygame.font; log and continue to SysFont
                print(f"同梱フォントの読み込みに失敗しました ({font_path}): {e}")
                print("デフォルトフォント（英語）を使用します。")

        # If bundled font not found, inform and try SysFont
        if not font_module_unusable and not font_exists:
            print(f"同梱フォントファイルが見つかりません: {font_path}")
            print("デフォルトフォント（英語）を使用します。")

        # 2) Try system font via pygame.font.SysFont if available
        if not font_module_unusable:
            try:
                if hasattr(pygame.font, 'SysFont'):
                    sys_font = pygame.font.SysFont('sans', font_size)
                    return sys_font
            except Exception:
                # SysFont failed; log and fall through to other fallbacks
                print("システムフォントも利用できません。")
                pass

        # 3) If SysFont failed or not present, try pygame.font.Font(None) as last pygame.font fallback
        if not font_module_unusable:
            try:
                print("pygame デフォルトフォントを使用します。")
                fallback_font = pygame.font.Font(None, font_size)
                return fallback_font
            except Exception:
                # If this fails due to font module unavailability, proceed to freetype
                font_module_unusable = True

        # 4) Try pygame._freetype and wrap it to mimic pygame.font.Font API
        try:
            import pygame._freetype as _freetype
            _freetype.init()

            class _FTFontWrapper:
                def __init__(self, ff):
                    self._ff = ff

                def render(self, text, antialias, color, background=None):
                    try:
                        result = self._ff.render(text, fgcolor=color, bgcolor=background)
                    except TypeError:
                        result = self._ff.render(text, color, background)
                    if isinstance(result, tuple):
                        return result[0]
                    return result

                def get_height(self):
                    try:
                        return int(self._ff.get_sized_height())
                    except Exception:
                        return int(getattr(self._ff, 'height', font_size))

            if font_exists:
                ff_font = _freetype.Font(str(font_path), font_size)
            else:
                ff_font = _freetype.Font(None, font_size)
            return _FTFontWrapper(ff_font)
        except Exception as e:
            print(f"freetype font load failed: {e}")

        # 5) Final fallback: if nothing else worked, try to use pygame.font.Font(None)
        try:
            print("pygame デフォルトフォントを使用します。")
            return pygame.font.Font(None, font_size)
        except Exception:
            # As last resort, try SysFont
            try:
                return pygame.font.SysFont('sans', font_size)
            except Exception:
                # If everything fails, raise the original error
                raise

    def _compute_min_height(self):
        """計算: すべてのUI要素が表示されるために必要な最小ウィンドウ高さを返す

        Uses a conservative estimate (prefers the default BOARD_SIZE up to available
        width) to determine the minimum height required. This avoids circular
        calls with _calculate_board_rect during initialization.
        """
        font_height = self.font.get_height()
        # choose a candidate board size based on available width but not exceeding default
        candidate_board = min(Screen.BOARD_SIZE, max(8 * 10, self.screen_width - Screen.SIDE_PADDING * 2))
        # compute positions as if board size were candidate_board
        board_top = Screen.BOARD_TOP_MARGIN
        board_bottom = board_top + candidate_board
        stone_count_y = board_bottom + Screen.TURN_MESSAGE_TOP_MARGIN
        turn_message_center_y = stone_count_y + font_height + Screen.TURN_MESSAGE_TOP_MARGIN + font_height // 2
        button_height = self._calculate_button_height()
        buttons_bottom = turn_message_center_y + font_height // 2 + Screen.TURN_MESSAGE_BOTTOM_MARGIN + button_height
        player_settings_height = self._calculate_player_settings_layout_height()
        player_settings_top = buttons_bottom + Screen.BUTTON_BOTTOM_MARGIN
        player_settings_bottom = player_settings_top + player_settings_height
        needed = max(buttons_bottom, player_settings_bottom)
        return int(needed + 20)

    def _calculate_board_rect(self):
        """盤面の描画領域(Rect)を計算する

        Chooses the largest square board (multiple of 8) that fits within both
        the current screen width (respecting SIDE_PADDING) and the available
        vertical space so that the UI below the board still fits.
        """
        # キャッシュがあり、ウィンドウサイズが変わっていなければキャッシュを返す
        current_size = (self.screen_width, self.screen_height)
        if self._board_rect_cache is not None and self._cached_screen_size == current_size:
            return self._board_rect_cache

        font_height = self.font.get_height()
        side_pad = getattr(Screen, 'SIDE_PADDING', 20)
        max_by_width = max(8 * 10, self.screen_width - 2 * side_pad)  # at least 80

        # maximum starting candidate: don't exceed screen height minus basic UI area
        # Start from the smaller of max_by_width and screen height minus top margin
        start_candidate = min(max_by_width, max(8 * 10, self.screen_height - Screen.BOARD_TOP_MARGIN - 100))

        def required_height_for_board(B: int) -> int:
            board_top = Screen.BOARD_TOP_MARGIN
            board_bottom = board_top + B
            stone_count_y = board_bottom + Screen.TURN_MESSAGE_TOP_MARGIN
            turn_message_center_y = stone_count_y + font_height + Screen.TURN_MESSAGE_TOP_MARGIN + font_height // 2
            button_height = self._calculate_button_height()
            buttons_bottom = turn_message_center_y + font_height // 2 + Screen.TURN_MESSAGE_BOTTOM_MARGIN + button_height
            player_settings_height = self._calculate_player_settings_layout_height()
            player_settings_top = buttons_bottom + Screen.BUTTON_BOTTOM_MARGIN
            player_settings_bottom = player_settings_top + player_settings_height
            needed = max(buttons_bottom, player_settings_bottom)
            return int(needed + 20)

        chosen_B = None
        # iterate down in multiples of 8 to ensure integer cell sizes
        candidate = int(start_candidate) - (int(start_candidate) % 8)
        while candidate >= 8 * 8:  # at least 8 cells of size >=8
            req_h = required_height_for_board(candidate)
            if req_h <= self.screen_height:
                chosen_B = candidate
                break
            candidate -= 8

        if chosen_B is None:
            # fallback: use the default BOARD_SIZE but respect side padding
            chosen_B = min(Screen.BOARD_SIZE, max_by_width)
            # round down to multiple of 8
            chosen_B -= chosen_B % 8

        # update cell size for this GUI instance
        self.cell_size = max(1, chosen_B // 8)
        # ensure minimum side padding on both sides while keeping board centered when possible
        centered_left = (self.screen_width - chosen_B) // 2
        min_left = side_pad
        max_left = max(side_pad, self.screen_width - side_pad - chosen_B)
        if centered_left < min_left:
            board_left = min_left
        elif centered_left > max_left:
            board_left = max_left
        else:
            board_left = centered_left
        board_top = Screen.BOARD_TOP_MARGIN
        board_rect = pygame.Rect(board_left, board_top, chosen_B, chosen_B)
        # キャッシュに保存
        self._board_rect_cache = board_rect
        self._cached_screen_size = current_size
        return board_rect

    def _compute_min_width(self):
        """最小表示幅を計算する

        Returns the minimal window width necessary to display the board at its
        preferred size (up to Screen.BOARD_SIZE) while respecting SIDE_PADDING.
        Ensures there is enough room for the bottom control buttons and the
        two player-setting columns so buttons/labels won't be clipped or
        overlap when the window is automatically shrunk.
        """
        side_pad = getattr(Screen, 'SIDE_PADDING', 20)

        # Board-based minimum: keep default board size visible with side paddings
        board_min = Screen.BOARD_SIZE + side_pad * 2

        # Button-based minimum: calculate using font metrics (4 buttons in a row)
        try:
            base_text_surface = self._get_rendered_text(_t("ui.restart"), Color.BUTTON_TEXT)
            button_width = base_text_surface.get_width() + Screen.BUTTON_MARGIN * 2 + Screen.BUTTON_BORDER_WIDTH * 2
            total_button_width = button_width * 4 + Screen.BUTTON_MARGIN * 3
            button_min = total_button_width + side_pad * 2
        except Exception:
            # If font/render isn't available for some reason, fall back to board_min
            button_min = board_min

        # Player-settings minimum: ensure both left/right columns can display radio + label
        try:
            max_label_width = 0
            for _, display_name in self.agent_options:
                surf = self._get_rendered_text(display_name, Color.BUTTON_TEXT)
                max_label_width = max(max_label_width, surf.get_width())
            # radio + margin + label + badge padding (safe over-approximation)
            column_width = Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN + max_label_width + getattr(Screen, 'BADGE_PADDING_X', 0) + getattr(Screen, 'BADGE_MARGIN', 0)
            column_width = max(column_width, 100)
            players_min = column_width * 2 + side_pad * 2 + Screen.RADIO_BUTTON_MARGIN
        except Exception:
            players_min = board_min

        min_width = int(max(board_min, button_min, players_min, 8 * 10 + side_pad * 2))
        return min_width

    def _get_player_settings_content_top(self, player_settings_top: int) -> int:
        """ラジオボタン行の先頭Y座標を返す（ヘッダーラベルの下）"""
        return player_settings_top + self._calculate_player_settings_header_height()

    def _get_player_settings_max_scroll(self, player_settings_top: int) -> int:
        """プレイヤー設定の最大スクロール量を返す"""
        list_height = self._calculate_player_settings_list_height()
        viewport_height = self._calculate_player_settings_viewport_height()
        return max(0, list_height - viewport_height)

    def _clamp_player_settings_scroll(self, player_settings_top: int) -> None:
        """スクロール位置を表示領域に収める"""
        max_scroll = self._get_player_settings_max_scroll(player_settings_top)
        if max_scroll <= 0:
            self._player_settings_scroll = 0
            return
        self._player_settings_scroll = max(0, min(self._player_settings_scroll, max_scroll))

    def scroll_player_settings(self, scroll_delta: int, player_settings_top: int) -> bool:
        """プレイヤー設定をスクロールする

        Args:
            scroll_delta (int): 下方向への移動量。正の値で下にスクロール。
            player_settings_top (int): プレイヤー設定UIの上端Y座標。

        Returns:
            bool: スクロール位置が変わった場合に True。
        """
        max_scroll = self._get_player_settings_max_scroll(player_settings_top)
        if max_scroll <= 0:
            self._player_settings_scroll = 0
            return False

        new_scroll = max(0, min(self._player_settings_scroll + scroll_delta, max_scroll))
        changed = new_scroll != self._player_settings_scroll
        self._player_settings_scroll = new_scroll
        return changed

    def is_player_settings_point(self, click_pos: tuple[int, int], player_settings_top: int) -> bool:
        """プレイヤー設定の表示領域内か判定する"""
        board_rect = self._calculate_board_rect()
        content_top = self._get_player_settings_content_top(player_settings_top)
        viewport_height = self._calculate_player_settings_viewport_height()
        viewport_rect = pygame.Rect(
            board_rect.left,
            content_top,
            self.screen_width - board_rect.left - Screen.SIDE_PADDING,
            viewport_height,
        )
        return bool(viewport_rect.collidepoint(click_pos))

    def _draw_player_settings_scrollbar(self, player_settings_top: int) -> None:
        """スクロール可能な場合にスクロールバーを描画する"""
        max_scroll = self._get_player_settings_max_scroll(player_settings_top)
        if max_scroll <= 0:
            return

        content_top = self._get_player_settings_content_top(player_settings_top)
        viewport_height = self._calculate_player_settings_viewport_height()
        track_width = Screen.PLAYER_SETTINGS_SCROLLBAR_WIDTH
        track_margin = Screen.PLAYER_SETTINGS_SCROLLBAR_MARGIN
        track_left = self.screen_width - Screen.SIDE_PADDING - track_width - track_margin
        track_rect = pygame.Rect(track_left, content_top, track_width, viewport_height)
        pygame.draw.rect(self.screen, Color.SCROLLBAR_TRACK, track_rect)

        list_height = self._calculate_player_settings_list_height()
        thumb_height = max(20, int(viewport_height * viewport_height / list_height))
        thumb_height = min(thumb_height, viewport_height)
        thumb_space = max(0, viewport_height - thumb_height)
        thumb_top = content_top
        if max_scroll > 0:
            thumb_top += int(thumb_space * (self._player_settings_scroll / max_scroll))
        thumb_rect = pygame.Rect(track_left, thumb_top, track_width, thumb_height)
        pygame.draw.rect(self.screen, Color.SCROLLBAR_THUMB, thumb_rect)

    # === 描画 ===
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

    def _stone_radius(self) -> int:
        """石の描画半径を返す。極小セルでも見えなくならないよう下限を設ける"""
        return max(2, self.cell_size // 2 - 5)

    def _draw_stone(self, board_rect, row, col, color):
        """指定された位置に石を描画する"""
        center = (
            board_rect.left + col * self.cell_size + self.cell_size // 2,
            board_rect.top + row * self.cell_size + self.cell_size // 2
        )
        pygame.draw.circle(self.screen, color, center, self._stone_radius()) # 石の半径

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
        self._get_label((left_margin, stone_count_y), _t("game.black_stones", count=black_count), Color.BLACK).draw(self.screen)
        # 白石数 (右寄せ)
        self._get_label((self.screen_width - left_margin, stone_count_y), _t("game.white_stones", count=white_count), Color.WHITE, is_right_aligned=True).draw(self.screen)

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
            text_surface = self._get_rendered_text(message, Color.WHITE)
            # メッセージの位置を状況に応じて計算
            y_pos = self._get_message_y_position(is_game_start, is_game_over)
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, y_pos))
            self.screen.blit(text_surface, text_rect)

    # === 入力処理 ===
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
        max_radius = self._stone_radius()

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
        max_radius = self._stone_radius()

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
        self._get_button(button_rect, _t("ui.undo")).draw(self.screen)

    def draw_restart_button(self, game_over=False):
        """リスタートボタンを描画する"""
        button_rect = self._calculate_button_rect(False, game_over, False, False)
        self._get_button(button_rect, _t("ui.restart")).draw(self.screen)

    def draw_reset_button(self, game_over=False):
        """リセットボタンを描画する"""
        button_rect = self._calculate_button_rect(False, game_over, True, False)
        self._get_button(button_rect, _t("ui.reset")).draw(self.screen)

    def draw_quit_button(self, game_over=False):
        """終了ボタンを描画する"""
        button_rect = self._calculate_button_rect(False, game_over, False, True)
        self._get_button(button_rect, _t("ui.quit")).draw(self.screen)
    # ---------------------------------

    def _calculate_button_rect(self, is_start_button=False, game_over=False, is_reset_button=False, is_quit_button=False, is_undo_button=False):
        """ボタンの描画領域(Rect)を計算する"""
        # キャッシュキーを作成（パラメータとウィンドウサイズを含む）
        cache_key = (is_start_button, game_over, is_reset_button, is_quit_button, is_undo_button, self.screen_width, self.screen_height)
        if cache_key in self._button_rect_cache:
            return self._button_rect_cache[cache_key]

        # 固定幅にする (例: "リスタート" の幅を基準にする)
        base_text_surface = self._get_rendered_text(_t("ui.restart"), Color.BUTTON_TEXT)
        button_width = base_text_surface.get_width() + Screen.BUTTON_MARGIN * 2 + Screen.BUTTON_BORDER_WIDTH * 2
        button_height = self._calculate_button_height()

        if is_start_button:
            # ゲーム開始ボタンは画面中央付近
            button_x = (self.screen_width - button_width) // 2
            # プレイヤー設定の上に配置
            player_settings_top = self._calculate_player_settings_top()
            button_y = player_settings_top - button_height - Screen.BUTTON_BOTTOM_MARGIN

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

        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        # キャッシュに保存
        self._button_rect_cache[cache_key] = button_rect
        return button_rect
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
        content_top = self._get_player_settings_content_top(player_settings_top)
        viewport_height = self._calculate_player_settings_viewport_height()
        self._clamp_player_settings_scroll(player_settings_top)

        # Header labels for player columns (keep objects to compute badge placement)
        self._get_label((left_margin, player_settings_top), _t("ui.black_player")).draw(self.screen)
        self._get_label((white_player_label_x, player_settings_top), _t("ui.white_player")).draw(self.screen)

        # ラジオボタンの間隔とテキスト位置オフセット
        radio_y_spacing = Screen.RADIO_Y_SPACING
        radio_text_x_offset = Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN
        clip_rect = pygame.Rect(
            left_margin,
            content_top,
            self.screen_width - left_margin - Screen.SIDE_PADDING,
            viewport_height,
        )
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(clip_rect)

        try:
            # 現在選択されているエージェント ID を取得
            black_agent_id = game.agent_ids[-1]
            white_agent_id = game.agent_ids[1]

            scroll_offset = self._player_settings_scroll
            # 黒プレイヤーのラジオボタンを描画
            for i, (agent_id, display_name) in enumerate(self.agent_options):
                radio_y = content_top + i * radio_y_spacing - scroll_offset
                radio_pos = (left_margin, radio_y)
                text_pos = (left_margin + radio_text_x_offset, radio_y)

                # 選択状態の判定 (agent_id を直接比較)
                is_selected = (agent_id == black_agent_id)

                RadioButton(radio_pos, Screen.RADIO_BUTTON_SIZE, is_selected, enabled).draw(self.screen)
                # テキストは常に有効な色で描画 (enabled フラグはボタン自体に適用)
                self._get_label(text_pos, display_name, font=self.agent_label_font).draw(self.screen)

            # 白プレイヤーのラジオボタンを描画
            for i, (agent_id, display_name) in enumerate(self.agent_options):
                radio_y = content_top + i * radio_y_spacing - scroll_offset
                radio_pos = (white_player_label_x, radio_y)
                text_pos = (white_player_label_x + radio_text_x_offset, radio_y)

                # 選択状態の判定 (agent_id を直接比較)
                is_selected = (agent_id == white_agent_id)

                RadioButton(radio_pos, Screen.RADIO_BUTTON_SIZE, is_selected, enabled).draw(self.screen)
                # テキストは常に有効な色で描画
                self._get_label(text_pos, display_name, font=self.agent_label_font).draw(self.screen)
        finally:
            self.screen.set_clip(previous_clip)

        self._draw_player_settings_scrollbar(player_settings_top)

    def draw_turn_message(self, game):
        """手番表示を描画する"""
        if game.game_over:
            return  # ゲームオーバー時は表示しない
        message = _t("game.black_turn") if game.turn == -1 else _t("game.white_turn")
        text_surface = self._get_rendered_text(message, Color.WHITE)
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
        content_top = self._get_player_settings_content_top(player_settings_top)
        radio_y_spacing = Screen.RADIO_Y_SPACING
        radio_button_size = Screen.RADIO_BUTTON_SIZE
        self._clamp_player_settings_scroll(player_settings_top)
        scroll_offset = self._player_settings_scroll

        for i, (agent_id, _) in enumerate(self.agent_options):
            radio_y = content_top + i * radio_y_spacing - scroll_offset

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
        # draw_start_button が呼ばれる前にクリックされる可能性があるので、ここで Rect を計算する方が安全
        start_rect = self._calculate_button_rect(is_start_button=True)
        return bool(start_rect.collidepoint(pos))

    def is_restart_button_clicked(self, pos: tuple[int, int], game_over: bool) -> bool:
        """リスタートボタンがクリックされたか判定"""
        button_rect = self._calculate_button_rect(False, game_over, False, False)
        return bool(button_rect.collidepoint(pos))

    def is_reset_button_clicked(self, pos: tuple[int, int], game_over: bool) -> bool:
        """リセットボタンがクリックされたか判定"""
        button_rect = self._calculate_button_rect(False, game_over, True, False)
        return bool(button_rect.collidepoint(pos))

    def is_quit_button_clicked(self, pos: tuple[int, int], game_over: bool) -> bool:
        """終了ボタンがクリックされたか判定"""
        button_rect = self._calculate_button_rect(False, game_over, False, True)
        return bool(button_rect.collidepoint(pos))

    def is_undo_button_clicked(self, pos: tuple[int, int], game_over: bool) -> bool:
        """待ったボタンがクリックされたか判定"""
        button_rect = self._calculate_button_rect(False, game_over, False, False, is_undo_button=True)
        return bool(button_rect.collidepoint(pos))

    # === 解説モード ===

    def _get_button_fit(self, rect: pygame.Rect, text: str) -> Button:
        """文字幅に応じてフォントを自動調整した Button を返す。"""
        font = (
            self.agent_label_font
            if self.font.size(text)[0] > rect.width - 8
            else self.font
        )
        cache_key = (rect.x, rect.y, rect.width, rect.height, text, id(font))
        if cache_key not in self._button_cache:
            self._button_cache[cache_key] = Button(rect, text, font)
        return self._button_cache[cache_key]

    def draw_analyze_button(self, game_over: bool = True) -> None:
        """終局画面の左端スロットに解説ボタンを描画する。"""
        button_rect = self._calculate_button_rect(
            False, game_over, False, False, is_undo_button=True
        )
        self._get_button_fit(button_rect, _t("ui.analyze")).draw(self.screen)

    def is_analyze_button_clicked(
        self, pos: tuple[int, int], game_over: bool = True
    ) -> bool:
        """解説ボタンがクリックされたか判定する。"""
        button_rect = self._calculate_button_rect(
            False, game_over, False, False, is_undo_button=True
        )
        return bool(button_rect.collidepoint(pos))

    def _get_analysis_button_specs(self) -> list[tuple[str, str, pygame.Rect]]:
        """解説モード用 4 ボタンの (アクション名, ラベル, Rect) を返す。"""
        return [
            (
                "prev_mistake",
                _t("ui.prev_mistake"),
                self._calculate_button_rect(False, True, False, False, is_undo_button=True),
            ),
            (
                "next_mistake",
                _t("ui.next_mistake"),
                self._calculate_button_rect(False, True, False, False),
            ),
            (
                "resume",
                _t("ui.resume_here"),
                self._calculate_button_rect(False, True, True, False),
            ),
            (
                "close",
                _t("ui.close_analysis"),
                self._calculate_button_rect(False, True, False, True),
            ),
        ]

    def draw_analysis_buttons(self) -> None:
        """解説モード用の操作ボタン行を描画する。"""
        for _, label, rect in self._get_analysis_button_specs():
            self._get_button_fit(rect, label).draw(self.screen)

    def get_clicked_analysis_button(self, pos: tuple[int, int]) -> Optional[str]:
        """クリックされた解説モードボタンのアクション名を返す。"""
        for action, _, rect in self._get_analysis_button_specs():
            if rect.collidepoint(pos):
                return action
        return None

    def _get_resume_pending_button_specs(self) -> list[tuple[str, str, pygame.Rect]]:
        """打ち直し準備状態用 4 ボタンの (アクション名, ラベル, Rect) を返す。"""
        return [
            (
                "back_to_analysis",
                _t("ui.back_to_analysis"),
                self._calculate_button_rect(False, False, False, False, is_undo_button=True),
            ),
            (
                "confirm_resume",
                _t("ui.confirm_resume"),
                self._calculate_button_rect(False, False, False, False),
            ),
            (
                "reset",
                _t("ui.reset"),
                self._calculate_button_rect(False, False, True, False),
            ),
            (
                "quit",
                _t("ui.quit"),
                self._calculate_button_rect(False, False, False, True),
            ),
        ]

    def draw_resume_pending_buttons(self) -> None:
        """打ち直し準備状態用のボタン行を描画する。"""
        for _, label, rect in self._get_resume_pending_button_specs():
            self._get_button_fit(rect, label).draw(self.screen)

    def get_clicked_resume_pending_button(self, pos: tuple[int, int]) -> Optional[str]:
        """クリックされた打ち直し準備ボタンのアクション名を返す。"""
        for action, _, rect in self._get_resume_pending_button_specs():
            if rect.collidepoint(pos):
                return action
        return None

    def _draw_board_coordinates(self, board_rect: pygame.Rect) -> None:
        """盤面の列 (A〜H)・行 (1〜8) 座標ラベルを描画する。"""
        col_y = max(4, board_rect.top - 20)
        row_x = max(2, board_rect.left - 16)
        for i in range(8):
            col_surf = self.agent_label_font.render(chr(ord("A") + i), True, Color.WHITE)
            col_rect = col_surf.get_rect(
                center=(
                    board_rect.left + i * self.cell_size + self.cell_size // 2,
                    col_y + col_surf.get_height() // 2,
                )
            )
            self.screen.blit(col_surf, col_rect)

            row_surf = self.agent_label_font.render(str(i + 1), True, Color.WHITE)
            row_rect = row_surf.get_rect(
                center=(
                    row_x + row_surf.get_width() // 2,
                    board_rect.top + i * self.cell_size + self.cell_size // 2,
                )
            )
            self.screen.blit(row_surf, row_rect)

    def _cell_rect(self, board_rect: pygame.Rect, row: int, col: int) -> pygame.Rect:
        return pygame.Rect(
            board_rect.left + col * self.cell_size,
            board_rect.top + row * self.cell_size,
            self.cell_size,
            self.cell_size,
        )

    def draw_analysis_board(
        self,
        board_data: list[list[int]],
        black_count: int,
        white_count: int,
        played_move: Optional[tuple[int, int]] = None,
        best_move: Optional[tuple[int, int]] = None,
        last_pv_move: Optional[tuple[int, int]] = None,
    ) -> None:
        """解説モード用の盤面・座標・手ハイライト・石数を描画する。"""
        board_rect = self._calculate_board_rect()
        self._draw_board_background(board_rect)
        self._draw_board_grid(board_rect)
        self._draw_stones(board_data, board_rect)
        self._draw_board_coordinates(board_rect)

        if best_move is not None:
            r, c = best_move
            center = (
                board_rect.left + c * self.cell_size + self.cell_size // 2,
                board_rect.top + r * self.cell_size + self.cell_size // 2,
            )
            outer_r = max(4, self.cell_size // 2 - 4)
            inner_r = max(2, self.cell_size // 7)
            pygame.draw.circle(self.screen, Color.ANALYSIS_BEST_COLOR, center, outer_r, 3)
            pygame.draw.circle(self.screen, Color.ANALYSIS_BEST_COLOR, center, inner_r)

        if played_move is not None:
            rect = self._cell_rect(board_rect, played_move[0], played_move[1]).inflate(-4, -4)
            pygame.draw.rect(self.screen, Color.ANALYSIS_PLAYED_COLOR, rect, 3)
            inset = max(4, self.cell_size // 5)
            cell = self._cell_rect(board_rect, played_move[0], played_move[1])
            pygame.draw.line(
                self.screen,
                Color.ANALYSIS_PLAYED_COLOR,
                (cell.left + inset, cell.top + inset),
                (cell.right - inset, cell.bottom - inset),
                2,
            )
            pygame.draw.line(
                self.screen,
                Color.ANALYSIS_PLAYED_COLOR,
                (cell.right - inset, cell.top + inset),
                (cell.left + inset, cell.bottom - inset),
                2,
            )

        if last_pv_move is not None:
            rect = self._cell_rect(board_rect, last_pv_move[0], last_pv_move[1]).inflate(-6, -6)
            pygame.draw.rect(self.screen, Color.ANALYSIS_REFUTATION_COLOR, rect, 3)

        stone_count_y = board_rect.bottom + Screen.TURN_MESSAGE_TOP_MARGIN
        left_margin = board_rect.left
        self._get_label(
            (left_margin, stone_count_y),
            _t("game.black_stones", count=black_count),
            Color.BLACK,
        ).draw(self.screen)
        self._get_label(
            (self.screen_width - left_margin, stone_count_y),
            _t("game.white_stones", count=white_count),
            Color.WHITE,
            is_right_aligned=True,
        ).draw(self.screen)

    def _analysis_panel_rect(self, panel_top: int) -> pygame.Rect:
        """下部解説パネル全体の領域を計算する。"""
        board_rect = self._calculate_board_rect()
        left = min(board_rect.left, Screen.SIDE_PADDING * 2)
        width = max(200, self.screen_width - left * 2)
        height = max(120, self.screen_height - panel_top - 10)
        return pygame.Rect(left, panel_top, width, height)

    def _analysis_nav_rects(
        self, panel_rect: pygame.Rect, has_pv: bool
    ) -> dict[str, pygame.Rect]:
        """解説パネル上部のナビゲーションバー（< / タイムライン / > / 手順確認）領域を返す。"""
        nav_y = panel_rect.top + 6
        nav_h = 26
        btn_w = 28
        gap = 6
        pad = 8
        pv_w = 80 if has_pv else 0

        step_prev = pygame.Rect(panel_rect.left + pad, nav_y, btn_w, nav_h)
        right_edge = panel_rect.right - pad
        rects: dict[str, pygame.Rect] = {"step_prev": step_prev}
        if has_pv:
            pv_rect = pygame.Rect(right_edge - pv_w, nav_y, pv_w, nav_h)
            rects["toggle_pv"] = pv_rect
            right_edge = pv_rect.left - gap

        step_next = pygame.Rect(right_edge - btn_w, nav_y, btn_w, nav_h)
        rects["step_next"] = step_next

        tl_left = step_prev.right + gap
        tl_width = max(40, step_next.left - gap - tl_left)
        rects["timeline"] = pygame.Rect(tl_left, nav_y + 4, tl_width, nav_h - 8)
        return rects

    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        """日本語テキストを pixel 幅 max_width 以内で折り返す。"""
        lines: list[str] = []
        for raw_line in text.splitlines():
            if not raw_line:
                lines.append("")
                continue
            buf = ""
            for ch in raw_line:
                candidate = buf + ch
                if self.agent_label_font.size(candidate)[0] <= max_width or not buf:
                    buf = candidate
                else:
                    lines.append(buf)
                    buf = ch
            if buf:
                lines.append(buf)
        return lines

    def _build_analysis_body_lines(
        self,
        analysis: "GameAnalysis",
        move_index: int,
        pv_step: int,
        total_moves: int,
        move_turn: int,
        played_move: tuple[int, int],
    ) -> list[tuple[str, tuple[int, int, int]]]:
        """解説パネルに表示する (テキスト, 文字色) の行リストを構築する。"""
        turn_str = "黒" if move_turn == -1 else "白"
        coord = f"{chr(ord('A') + played_move[1])}{played_move[0] + 1}"
        header = f"第{move_index + 1}/{total_moves}手 [{turn_str}]  実戦: {coord}"
        if pv_step > 0:
            header += f"  （手順確認 {pv_step}手目）"

        max_w = self._analysis_panel_rect(0).width - 28
        result: list[tuple[str, tuple[int, int, int]]] = [
            (header, Color.ANALYSIS_HEADER_COLOR),
        ]
        for line in self._wrap_text(f"総評: {analysis.headline}", max_w):
            result.append((line, Color.WHITE))

        branch_parts: list[str] = []
        for idx, prefix in (
            (analysis.missed_win_move_index, "勝ち逃し"),
            (analysis.loss_sealed_move_index, "負け決定"),
            (analysis.draw_sealed_move_index, "アイコ決定"),
        ):
            if idx is not None and idx in analysis.moves_by_index:
                bm = analysis.moves_by_index[idx]
                bm_lbl = f"{chr(ord('A') + bm.played_move[1])}{bm.played_move[0] + 1}"
                branch_parts.append(f"{prefix}=第{bm.move_number}手 {bm_lbl}")
        if branch_parts:
            branch_line = f"勝敗分岐: {' / '.join(branch_parts)}"
            for line in self._wrap_text(branch_line, max_w):
                result.append((line, Color.ANALYSIS_HEADER_COLOR))

        ma = analysis.moves_by_index.get(move_index)
        if ma is not None:
            for line in self._wrap_text(ma.explanation, max_w):
                result.append((line, Color.WHITE))
        else:
            note = (
                "この局面は詳細解析の対象外（勝者の着手、または合法手が 1 手のみ）です。"
                "「ここから打つ」を押すとこの局面から打ち直すことができます。"
            )
            for line in self._wrap_text(note, max_w):
                result.append((line, Color.DISABLED_TEXT))
        return result

    def reset_analysis_scroll(self) -> None:
        """解説パネルのスクロール位置を先頭に戻す。"""
        self._analysis_scroll = 0

    def is_analysis_panel_point(self, pos: tuple[int, int], panel_top: int) -> bool:
        """指定座標が解説パネル領域内か判定する。"""
        return bool(self._analysis_panel_rect(panel_top).collidepoint(pos))

    def scroll_analysis_panel(self, scroll_delta: int, panel_top: int) -> bool:
        """解説パネルのスクロール位置を更新する。"""
        new_scroll = max(0, self._analysis_scroll + scroll_delta)
        changed = new_scroll != self._analysis_scroll
        self._analysis_scroll = new_scroll
        return changed

    def get_clicked_analysis_nav(
        self,
        pos: tuple[int, int],
        panel_top: int,
        total_moves: int,
        has_pv: bool,
    ) -> tuple[Optional[str], Optional[int]]:
        """解説パネル上段ナビゲーションバーのクリック判定を行う。"""
        panel_rect = self._analysis_panel_rect(panel_top)
        rects = self._analysis_nav_rects(panel_rect, has_pv)
        if rects["step_prev"].collidepoint(pos):
            return "step_prev", None
        if rects["step_next"].collidepoint(pos):
            return "step_next", None
        if "toggle_pv" in rects and rects["toggle_pv"].collidepoint(pos):
            return "toggle_pv", None
        tl = rects["timeline"]
        if tl.inflate(0, 8).collidepoint(pos) and total_moves > 0:
            ratio = (pos[0] - tl.left) / max(1, tl.width)
            idx = max(0, min(total_moves - 1, int(ratio * total_moves)))
            return "jump_move", idx
        return None, None

    def draw_analysis_panel(
        self,
        analysis: "GameAnalysis",
        move_index: int,
        pv_step: int,
        total_moves: int,
        move_turn: int,
        played_move: tuple[int, int],
        panel_top: int,
    ) -> None:
        """下部解説パネル（タイムラインバー＋解説テキスト）を描画する。"""
        panel_rect = self._analysis_panel_rect(panel_top)
        pygame.draw.rect(self.screen, Color.ANALYSIS_PANEL_BG, panel_rect)
        pygame.draw.rect(self.screen, Color.ANALYSIS_PANEL_BORDER, panel_rect, 1)

        ma = analysis.moves_by_index.get(move_index)
        has_pv = bool(ma is not None and ma.pv)
        rects = self._analysis_nav_rects(panel_rect, has_pv)

        # ナビゲーションボタン
        self._get_button_fit(rects["step_prev"], "<").draw(self.screen)
        self._get_button_fit(rects["step_next"], ">").draw(self.screen)
        if has_pv:
            pv_label = _t("ui.show_before") if pv_step > 0 else _t("ui.show_pv")
            self._get_button_fit(rects["toggle_pv"], pv_label).draw(self.screen)

        # タイムラインバー
        tl = rects["timeline"]
        pygame.draw.rect(self.screen, Color.ANALYSIS_TIMELINE_BG, tl)
        if total_moves > 0:
            for m in analysis.key_mistakes:
                mx = tl.left + int((m.move_index + 0.5) / total_moves * tl.width)
                pygame.draw.line(
                    self.screen,
                    Color.ANALYSIS_PLAYED_COLOR,
                    (mx, tl.top - 2),
                    (mx, tl.bottom + 2),
                    3,
                )
            cx = tl.left + int((move_index + 0.5) / total_moves * tl.width)
            cursor_rect = pygame.Rect(cx - 3, tl.top - 3, 6, tl.height + 6)
            pygame.draw.rect(self.screen, Color.ANALYSIS_TIMELINE_ACTIVE, cursor_rect)
        pygame.draw.rect(self.screen, Color.ANALYSIS_PANEL_BORDER, tl, 1)

        # 本文領域の描画
        body_top = rects["step_prev"].bottom + 6
        body_rect = pygame.Rect(
            panel_rect.left + 10,
            body_top,
            panel_rect.width - 20,
            max(20, panel_rect.bottom - body_top - 6),
        )
        lines = self._build_analysis_body_lines(
            analysis, move_index, pv_step, total_moves, move_turn, played_move
        )
        line_h = self.agent_label_font.get_height() + 4
        total_h = len(lines) * line_h
        max_scroll = max(0, total_h - body_rect.height)
        self._analysis_scroll = max(0, min(self._analysis_scroll, max_scroll))

        prev_clip = self.screen.get_clip()
        self.screen.set_clip(body_rect)
        try:
            y = body_rect.top - self._analysis_scroll
            for text, color in lines:
                if y + line_h >= body_rect.top and y <= body_rect.bottom:
                    surf = self.agent_label_font.render(text, True, color)
                    self.screen.blit(surf, (body_rect.left, y))
                y += line_h
        finally:
            self.screen.set_clip(prev_clip)

        if max_scroll > 0:
            track = pygame.Rect(panel_rect.right - 8, body_rect.top, 4, body_rect.height)
            pygame.draw.rect(self.screen, Color.SCROLLBAR_TRACK, track)
            thumb_h = max(16, int(body_rect.height * body_rect.height / total_h))
            thumb_y = body_rect.top + int(
                (body_rect.height - thumb_h) * (self._analysis_scroll / max_scroll)
            )
            pygame.draw.rect(
                self.screen,
                Color.SCROLLBAR_THUMB,
                pygame.Rect(track.left, thumb_y, 4, thumb_h),
            )

    # ---------------------------------------------
