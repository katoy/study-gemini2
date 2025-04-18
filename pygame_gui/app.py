# app.py
import pygame
import pygame_gui

# layout_constantsから必要な定数をインポート
from layout_constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_CAPTION,
    BACKGROUND_COLOR_HEX, # HEX文字列をインポート
    FPS,
    MAIN_BUTTON_WIDTH,
    MAIN_BUTTON_HEIGHT,
    MAIN_BUTTON_TEXT,
    POPUP_WINDOW_WIDTH,
    POPUP_WINDOW_HEIGHT,
    POPUP_WINDOW_TITLE
)

# PopupWindowクラスをインポート
from popup_window import PopupWindow

# pygame.Colorオブジェクトはここで生成
BACKGROUND_COLOR = pygame.Color(BACKGROUND_COLOR_HEX)

class PygameApp:
    """
    PygameとPygame GUIを使ったアプリケーションクラス。
    ボタンクリックでPopupWindowを開く機能を持つ。
    """
    # __init__メソッドのデフォルト引数を定数から取得するように変更
    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        """
        アプリケーションを初期化します。
        """
        pygame.init()

        self.width = width
        self.height = height
        self.window_size = (self.width, self.height)

        self.window_surface = None
        self.background = None
        self.manager = None
        self.open_popup_button = None
        self.clock = None

        self.is_running = False
        self.active_popups: list[PopupWindow] = []

        self._setup_display()
        self._setup_manager()
        self._setup_game_loop()

    def _setup_display(self):
        """
        Pygameのディスプレイウィンドウと背景を設定します。
        """
        pygame.display.set_caption(WINDOW_CAPTION) # インポートした定数を使用
        self.window_surface = pygame.display.set_mode(self.window_size)
        self.background = pygame.Surface(self.window_size)
        self.background.fill(BACKGROUND_COLOR) # 生成したColorオブジェクトを使用

    def _setup_manager(self):
        """
        Pygame GUIマネージャーとメインUI要素を設定します。
        """
        self.manager = pygame_gui.UIManager(self.window_size)

        # インポートした定数を使用
        button_x = (self.width - MAIN_BUTTON_WIDTH) // 2
        button_y = (self.height - MAIN_BUTTON_HEIGHT) // 2
        button_rect = pygame.Rect(button_x, button_y, MAIN_BUTTON_WIDTH, MAIN_BUTTON_HEIGHT)

        self.open_popup_button = pygame_gui.elements.UIButton(
            relative_rect=button_rect,
            text=MAIN_BUTTON_TEXT, # インポートした定数を使用
            manager=self.manager,
            object_id='#open_popup_button'
        )

    def _setup_game_loop(self):
        """
        ゲームループに必要な変数を初期化します。
        """
        self.clock = pygame.time.Clock()
        self.is_running = True

    def _create_popup_window(self):
        """
        新しいPopupWindowを作成して表示します。
        """
        # インポートした定数を使用
        popup_x = (self.width - POPUP_WINDOW_WIDTH) // 2
        popup_y = (self.height - POPUP_WINDOW_HEIGHT) // 3
        popup_rect = pygame.Rect(popup_x, popup_y, POPUP_WINDOW_WIDTH, POPUP_WINDOW_HEIGHT)

        # インポートしたPopupWindowクラスと定数を使用
        new_popup = PopupWindow(self.manager, popup_rect, POPUP_WINDOW_TITLE)
        self.active_popups.append(new_popup)

    def _process_events(self):
        """
        Pygameのイベントを処理します。
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False

            self.manager.process_events(event)

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.open_popup_button:
                    self._create_popup_window()

            if event.type == pygame_gui.UI_WINDOW_CLOSE:
                closed_window_element = event.ui_element
                popup_to_remove = None
                for popup in self.active_popups:
                    if popup.window == closed_window_element:
                        popup_to_remove = popup
                        break
                if popup_to_remove:
                    popup_to_remove.kill()

        self.active_popups = [popup for popup in self.active_popups if popup.is_alive]

    def _update(self, time_delta):
        """
        ゲームの状態とGUI要素を更新します。
        """
        self.manager.update(time_delta)

    def _render(self):
        """
        画面に要素を描画します。
        """
        self.window_surface.blit(self.background, (0, 0))
        self.manager.draw_ui(self.window_surface)
        pygame.display.update()

    def run(self):
        """
        メインのゲームループを実行します。
        """
        while self.is_running:
            # インポートした定数を使用
            time_delta = self.clock.tick(FPS) / 1000.0
            self._process_events()
            self._update(time_delta)
            self._render()

        pygame.quit()
