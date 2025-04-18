import pygame
import pygame_gui

# --- 定数 ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_CAPTION = 'Quick Start with New Window'
BACKGROUND_COLOR = pygame.Color('#000000')
FPS = 60

BUTTON_WIDTH = 100
BUTTON_HEIGHT = 50
BUTTON_TEXT = 'Open Window' # ボタンのテキストを変更

# 新しいウィンドウ用の定数
NEW_WINDOW_WIDTH = 300
NEW_WINDOW_HEIGHT = 200
NEW_WINDOW_TITLE = 'New Window'
NEW_WINDOW_LABEL_TEXT = 'This is a new window!'
# -------------

class PygameApp:
    """
    PygameとPygame GUIを使ったアプリケーションクラス。
    ボタンクリックで新しいウィンドウを開く機能を持つ。
    """

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
        self.open_window_button = None # ボタンの変数名を変更
        self.clock = None

        self.is_running = False

        # 開いているウィンドウを管理するためのリスト（オプション）
        # self.open_windows = [] # 必要に応じて使用

        self._setup_display()
        self._setup_manager()
        self._setup_game_loop()

    def _setup_display(self):
        """
        Pygameのディスプレイウィンドウと背景を設定します。
        """
        pygame.display.set_caption(WINDOW_CAPTION)
        self.window_surface = pygame.display.set_mode(self.window_size)
        self.background = pygame.Surface(self.window_size)
        self.background.fill(BACKGROUND_COLOR)

    def _setup_manager(self):
        """
        Pygame GUIマネージャーとUI要素を設定します。
        """
        self.manager = pygame_gui.UIManager(self.window_size)

        button_x = (self.width - BUTTON_WIDTH) // 2
        button_y = (self.height - BUTTON_HEIGHT) // 2
        button_rect = pygame.Rect(button_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)

        self.open_window_button = pygame_gui.elements.UIButton(
            relative_rect=button_rect,
            text=BUTTON_TEXT,
            manager=self.manager
        )

    def _setup_game_loop(self):
        """
        ゲームループに必要な変数を初期化します。
        """
        self.clock = pygame.time.Clock()
        self.is_running = True

    def _create_new_window(self):
        """
        新しいUIWindowを作成して表示します。
        """
        # ウィンドウの位置を計算（例: メインウィンドウの中央やや上）
        window_x = (self.width - NEW_WINDOW_WIDTH) // 2
        window_y = (self.height - NEW_WINDOW_HEIGHT) // 3 # 少し上に表示
        window_rect = pygame.Rect(window_x, window_y, NEW_WINDOW_WIDTH, NEW_WINDOW_HEIGHT)

        new_window = pygame_gui.elements.UIWindow(
            rect=window_rect,
            manager=self.manager,
            window_display_title=NEW_WINDOW_TITLE
        )

        # ウィンドウ内にラベルを追加
        label_rect = pygame.Rect(0, 0, NEW_WINDOW_WIDTH - 40, 50) # ウィンドウ内の相対位置とサイズ
        label_rect.center = (NEW_WINDOW_WIDTH // 2, NEW_WINDOW_HEIGHT // 3) # ラベルをウィンドウ中央に配置

        pygame_gui.elements.UILabel(
            relative_rect=label_rect,
            text=NEW_WINDOW_LABEL_TEXT,
            manager=self.manager,
            container=new_window # このウィンドウをコンテナとして指定
        )

        print(f"'{NEW_WINDOW_TITLE}' を開きました。")
        # 必要であれば、開いたウィンドウをリストに追加して管理
        # self.open_windows.append(new_window)

    def _process_events(self):
        """
        Pygameのイベントを処理します。
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False

            self.manager.process_events(event)

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                # ボタンが押されたら新しいウィンドウを作成
                if event.ui_element == self.open_window_button:
                    self._create_new_window()

            # --- UIWindowが閉じられたときのイベント処理（オプション） ---
            # if event.type == pygame_gui.UI_WINDOW_CLOSE:
            #     print(f"Window '{event.ui_element.window_display_title}' closed.")
            #     # 必要であれば、閉じたウィンドウをリストから削除
            #     # if event.ui_element in self.open_windows:
            #     #    self.open_windows.remove(event.ui_element)
            # ---------------------------------------------------------

    def _update(self, time_delta):
        """
        ゲームの状態とGUI要素を更新します。
        Args:
            time_delta (float): 前回のフレームからの経過時間（秒）。
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
            time_delta = self.clock.tick(FPS) / 1000.0
            self._process_events()
            self._update(time_delta)
            self._render()

        pygame.quit()


if __name__ == "__main__":
    print("アプリケーションを開始します...")
    app = PygameApp()
    app.run()
    print("アプリケーションを終了しました。")
