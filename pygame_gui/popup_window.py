# popup_window.py
import pygame
import pygame_gui

# layout_constantsから必要な定数をインポート
from layout_constants import (
    POPUP_WINDOW_LABEL_TEXT,
    # 必要に応じて他の定数もインポート可能
)

class PopupWindow:
    """
    ポップアップ表示されるUIWindowとその内部要素を管理するクラス。
    """
    def __init__(self, manager: pygame_gui.UIManager, rect: pygame.Rect, title: str):
        """
        PopupWindowを初期化します。

        Args:
            manager: Pygame GUIのUIManagerインスタンス。
            rect: ウィンドウの位置とサイズを指定するpygame.Rect。
            title: ウィンドウのタイトルバーに表示される文字列。
        """
        self.manager = manager
        self.is_alive = True

        self.window = pygame_gui.elements.UIWindow(
            rect=rect,
            manager=self.manager,
            window_display_title=title,
            object_id='#popup_window'
        )

        label_margin = 10
        label_width = rect.width - (label_margin * 2)
        label_height = 50
        label_rect = pygame.Rect(label_margin, label_margin, label_width, label_height)

        self.label = pygame_gui.elements.UILabel(
            relative_rect=label_rect,
            text=POPUP_WINDOW_LABEL_TEXT, # インポートした定数を使用
            manager=self.manager,
            container=self.window,
            object_id='@popup_label'
        )

        print(f"PopupWindow '{title}' created.")

    def process_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, time_delta: float) -> None:
        pass

    def kill(self) -> None:
        if self.is_alive:
            self.window.kill()
            self.is_alive = False
            print(f"PopupWindow '{self.window.window_display_title}' killed.")
