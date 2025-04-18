import pygame
import pygame_gui

# --- 定数 ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_CAPTION = 'Quick Start Refactored'
BACKGROUND_COLOR = pygame.Color('#000000')
FPS = 60

BUTTON_WIDTH = 100
BUTTON_HEIGHT = 50
BUTTON_TEXT = 'Say Hello'
# -------------

class PygameApp:
    """
    PygameとPygame GUIを使ったシンプルなアプリケーションクラス。
    """

    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        """
        アプリケーションを初期化します。
        """
        pygame.init() # Pygameを初期化

        self.width = width
        self.height = height
        self.window_size = (self.width, self.height)

        # Pygame関連の属性を初期化（Noneで初期化しておくと後で分かりやすい）
        self.window_surface = None
        self.background = None
        self.manager = None
        self.hello_button = None
        self.clock = None

        self.is_running = False # アプリケーションが実行中かどうかのフラグ

        # セットアップメソッドの呼び出し
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

        # ボタンを画面中央に配置するための計算
        button_x = (self.width - BUTTON_WIDTH) // 2
        button_y = (self.height - BUTTON_HEIGHT) // 2
        button_rect = pygame.Rect(button_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)

        self.hello_button = pygame_gui.elements.UIButton(
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

    def _process_events(self):
        """
        Pygameのイベントを処理します。
        """
        for event in pygame.event.get():
            # 終了イベント
            if event.type == pygame.QUIT:
                self.is_running = False

            # Pygame GUIのイベント処理
            self.manager.process_events(event)

            # ボタンクリックイベントの処理
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.hello_button:
                    print('Hello World!') # ボタンが押された時のアクション

            # --- 他のイベント処理をここに追加 ---
            # 例: キーボード入力、マウスイベントなど
            # if event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_SPACE:
            #         print("Space bar pressed!")
            # ------------------------------------

    def _update(self, time_delta):
        """
        ゲームの状態とGUI要素を更新します。
        Args:
            time_delta (float): 前回のフレームからの経過時間（秒）。
        """
        self.manager.update(time_delta)
        # --- 他のゲームロジックの更新をここに追加 ---
        # 例: キャラクターの位置更新、スコア計算など
        # ----------------------------------------

    def _render(self):
        """
        画面に要素を描画します。
        """
        # 背景を描画
        self.window_surface.blit(self.background, (0, 0))
        # GUI要素を描画
        self.manager.draw_ui(self.window_surface)
        # 画面を更新
        pygame.display.update()

    def run(self):
        """
        メインのゲームループを実行します。
        """
        while self.is_running:
            # フレームレート制御と時間差（デルタタイム）の計算
            time_delta = self.clock.tick(FPS) / 1000.0 # ミリ秒を秒に変換

            # イベント処理
            self._process_events()

            # 更新処理
            self._update(time_delta)

            # 描画処理
            self._render()

        # ループ終了後にPygameを終了
        pygame.quit()


if __name__ == "__main__":
    print("アプリケーションを開始します...")
    app = PygameApp()
    app.run()
    print("アプリケーションを終了しました。")
