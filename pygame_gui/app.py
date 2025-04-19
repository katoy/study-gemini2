# app.py
import pygame
import pygame_gui

# layout_constantsから必要な定数をインポート
from layout_constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_CAPTION,
    BACKGROUND_COLOR_HEX,
    FPS,
    MAIN_BUTTON_WIDTH,
    MAIN_BUTTON_HEIGHT,
    MAIN_BUTTON_TEXT,
    QUIT_BUTTON_WIDTH,
    QUIT_BUTTON_HEIGHT,
    QUIT_BUTTON_TEXT,
    QUIT_BUTTON_MARGIN,
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
    ボタンクリックでPopupWindowを開く機能と終了機能を持つ。
    ポップアップ表示中はメインボタンを無効化する（モーダル）。
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
        self.open_popup_button = None
        self.quit_button = None
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
        pygame.display.set_caption(WINDOW_CAPTION)
        self.window_surface = pygame.display.set_mode(self.window_size)
        self.background = pygame.Surface(self.window_size)
        self.background.fill(BACKGROUND_COLOR)

    def _setup_manager(self):
        """
        Pygame GUIマネージャーとメインUI要素を設定します。
        """
        self.manager = pygame_gui.UIManager(self.window_size)

        # --- ポップアップを開くボタン ---
        open_button_x = (self.width - MAIN_BUTTON_WIDTH) // 2
        open_button_y = (self.height - MAIN_BUTTON_HEIGHT) // 2
        open_button_rect = pygame.Rect(open_button_x, open_button_y, MAIN_BUTTON_WIDTH, MAIN_BUTTON_HEIGHT)

        self.open_popup_button = pygame_gui.elements.UIButton(
            relative_rect=open_button_rect,
            text=MAIN_BUTTON_TEXT,
            manager=self.manager,
            object_id='#open_popup_button'
        )

        # --- 終了ボタン ---
        quit_button_rect = pygame.Rect(
            (0, 0),
            (QUIT_BUTTON_WIDTH, QUIT_BUTTON_HEIGHT)
        )
        quit_button_rect.bottomright = (-QUIT_BUTTON_MARGIN, -QUIT_BUTTON_MARGIN)

        self.quit_button = pygame_gui.elements.UIButton(
            relative_rect=quit_button_rect,
            text=QUIT_BUTTON_TEXT,
            manager=self.manager,
            object_id='#quit_button',
            anchors={'left': 'right',
                     'right': 'right',
                     'top': 'bottom',
                     'bottom': 'bottom'}
        )

    def _setup_game_loop(self):
        """
        ゲームループに必要な変数を初期化します。
        """
        self.clock = pygame.time.Clock()
        self.is_running = True

    def _create_popup_window(self):
        """
        新しいPopupWindowを作成して表示し、必要であればメインボタンを無効化します。
        """
        # --- モーダル化: 最初のポップアップ表示時にボタンを無効化 ---
        if not self.active_popups: # まだアクティブなポップアップがない場合
            print("Disabling main buttons...")
            if self.open_popup_button:
                self.open_popup_button.disable()
            if self.quit_button:
                self.quit_button.disable()
        # ---

        popup_x = (self.width - POPUP_WINDOW_WIDTH) // 2
        popup_y = (self.height - POPUP_WINDOW_HEIGHT) // 3
        popup_rect = pygame.Rect(popup_x, popup_y, POPUP_WINDOW_WIDTH, POPUP_WINDOW_HEIGHT)

        new_popup = PopupWindow(self.manager, popup_rect, POPUP_WINDOW_TITLE)
        self.active_popups.append(new_popup)

    def _process_events(self):
        """
        Pygameのイベントを処理します。ポップアップが閉じられた際にボタンを再有効化します。
        """
        popup_closed_this_frame = False # このフレームでポップアップが閉じたかどうかのフラグ

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                return

            self.manager.process_events(event)

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                # ポップアップを開くボタン (有効な場合のみ反応)
                if event.ui_element == self.open_popup_button and self.open_popup_button.is_enabled:
                    self._create_popup_window()
                # 終了ボタン (有効な場合のみ反応)
                elif event.ui_element == self.quit_button and self.quit_button.is_enabled:
                    print("Quit button pressed. Exiting application...")
                    self.is_running = False
                    return

            if event.type == pygame_gui.UI_WINDOW_CLOSE:
                closed_window_element = event.ui_element
                popup_to_remove = None
                for popup in self.active_popups:
                    if popup.window == closed_window_element:
                        popup_to_remove = popup
                        break
                if popup_to_remove:
                    popup_to_remove.kill()
                    # kill()を呼んだだけではリストから消えないので、
                    # 後続のリスト更新処理で実際に消えることを確認するためにフラグを立てる
                    popup_closed_this_frame = True

        # killされたポップアップをリストから削除
        initial_popup_count = len(self.active_popups)
        self.active_popups = [popup for popup in self.active_popups if popup.is_alive]
        # フラグが立っており、かつ実際にリストの要素数が減った場合のみ「閉じた」と判定
        popup_closed_this_frame = popup_closed_this_frame and (len(self.active_popups) < initial_popup_count)

        # --- モーダル化: 全てのポップアップが閉じられたらボタンを有効化 ---
        # このフレームでポップアップが閉じられ、かつアクティブなポップアップがもうない場合
        if popup_closed_this_frame and not self.active_popups:
            print("Enabling main buttons...")
            if self.open_popup_button:
                self.open_popup_button.enable()
            if self.quit_button:
                self.quit_button.enable()
        # ---

    def _update(self, time_delta):
        """
        ゲームの状態とGUI要素を更新します。
        """
        if not self.is_running:
            return
        self.manager.update(time_delta)

    def _render(self):
        """
        画面に要素を描画します。
        """
        if not self.is_running:
             return
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

        print("Exiting Pygame...")
        pygame.quit()

