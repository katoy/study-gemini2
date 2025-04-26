# ui_elements.py
import pygame
from config.theme import Color, Screen # Buttonクラスが必要とするものをインポート

class Button:
    """
    GUIのボタンを表すクラス。
    描画とクリック判定を担当する。
    """
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font,
                 bg_color=Color.BUTTON, text_color=Color.BUTTON_TEXT, border_color=Color.WHITE, border_width=Screen.BUTTON_BORDER_WIDTH):
        """
        Buttonクラスのコンストラクタ。

        Args:
            rect (pygame.Rect): ボタンの位置とサイズ。
            text (str): ボタンに表示するテキスト。
            font (pygame.font.Font): テキスト描画に使用するフォント。
            bg_color: ボタンの背景色。
            text_color: ボタンのテキスト色。
            border_color: ボタンの枠線の色。
            border_width: ボタンの枠線の太さ。
        """
        self.rect = rect
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.border_color = border_color
        self.border_width = border_width
        # テキストサーフェスと位置を事前に計算しておく
        self.text_surface = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def draw(self, screen: pygame.Surface):
        """
        ボタンをスクリーンに描画する。

        Args:
            screen (pygame.Surface): 描画対象のスクリーン。
        """
        # ボタン背景
        pygame.draw.rect(screen, self.bg_color, self.rect)
        # ボタン枠線
        pygame.draw.rect(screen, self.border_color, self.rect, self.border_width)
        # ボタンテキスト
        screen.blit(self.text_surface, self.text_rect)

    def is_clicked(self, pos: tuple[int, int]) -> bool:
        """
        指定された座標がボタンの領域内にあるか判定する。

        Args:
            pos (tuple[int, int]): クリックされた座標。

        Returns:
            bool: ボタン内であれば True、そうでなければ False。
        """
        return self.rect.collidepoint(pos)

# --- 他のUI要素クラスもここに追加していくことができます ---
# class RadioButtonGroup:
#     ...
