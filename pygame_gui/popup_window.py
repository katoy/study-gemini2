# popup_window.py
import pygame
import pygame_gui

# --- ポップアップウィンドウ関連の定数 ---
POPUP_WINDOW_WIDTH = 300
POPUP_WINDOW_HEIGHT = 200
POPUP_WINDOW_TITLE = 'Popup Window'
POPUP_WINDOW_LABEL_TEXT = 'This is a popup window!'
# -------------

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
        self.is_alive = True # ウィンドウがアクティブかどうかのフラグ

        # UIWindowを作成
        self.window = pygame_gui.elements.UIWindow(
            rect=rect,
            manager=self.manager,
            window_display_title=title,
            object_id='#popup_window' # スタイリング用にIDを付与（オプション）
        )

        # ウィンドウ内にラベルを追加
        label_margin = 10 # ウィンドウ境界からのマージン
        label_width = rect.width - (label_margin * 2)
        label_height = 50
        label_rect = pygame.Rect(label_margin, label_margin, label_width, label_height)

        self.label = pygame_gui.elements.UILabel(
            relative_rect=label_rect,
            text=POPUP_WINDOW_LABEL_TEXT, # このファイル内の定数を参照
            manager=self.manager,
            container=self.window,
            object_id='@popup_label'
        )

        # --- 今後、このウィンドウに追加する要素をここに追加 ---
        # 例: ボタン、入力フィールドなど
        # ---------------------------------------------------

        print(f"PopupWindow '{title}' created.")

    def process_event(self, event: pygame.event.Event) -> None:
        """
        このウィンドウに関連するイベントを処理します（必要に応じて）。
        """
        pass # 基本的な処理はUIManagerが行う

    def update(self, time_delta: float) -> None:
        """
        ウィンドウの状態を更新します（必要に応じて）。
        """
        pass

    def kill(self) -> None:
        """
        ウィンドウとその中のUI要素を破棄します。
        """
        if self.is_alive:
            self.window.kill()
            self.is_alive = False
            print(f"PopupWindow '{self.window.window_display_title}' killed.")

