# ui_elements.py
from __future__ import annotations
from typing import Any
import pygame
from config.theme import Color, Screen # Buttonクラスが必要とするものをインポート

class Button:
    """
    GUIのボタンを表すクラス。
    描画とクリック判定を担当する。
    """
    def __init__(self, rect: pygame.Rect, text: str, font: Any,
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

class RadioButton:
    def __init__(self, pos: tuple[int, int], size: int, selected: bool = False, enabled: bool = True):
        self.rect = pygame.Rect(pos[0], pos[1], size, size)
        self.selected = selected
        self.enabled = enabled
        self.size = size

    def draw(self, screen: pygame.Surface):
        center = self.rect.center
        outer_color = Color.DARK_BLUE if self.enabled else Color.LIGHT_BLUE
        pygame.draw.circle(screen, outer_color, center, self.size // 2, 1)
        if self.selected:
            # 選択時は背景と区別しやすい色を使用（有効時は RADIO_SELECTED、無効時は DISABLED_TEXT）
            inner_color = Color.RADIO_SELECTED if self.enabled else Color.DISABLED_TEXT
            # 半径計算を修正して確実に正しい値を得る
            inner_circle_radius = max(1, int(self.size * Screen.RADIO_BUTTON_INNER_CIRCLE_RATIO / 2))
            pygame.draw.circle(screen, inner_color, center, inner_circle_radius)

    def is_clicked(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)

class Label:
    def __init__(self, pos: tuple[int, int], text: str, font: Any, color=Color.WHITE, is_right_aligned=False):
        self.pos = pos
        self.text = text
        self.font = font
        self.color = color
        self.is_right_aligned = is_right_aligned
        self.surface = self.font.render(self.text, True, self.color)
        self.rect = self.surface.get_rect(topleft=self.pos)
        if self.is_right_aligned:
            self.rect.right = self.pos[0]

    def draw(self, screen: pygame.Surface):
        screen.blit(self.surface, self.rect)

# --- 他のUI要素クラスもここに追加していくことができます ---
# class RadioButtonGroup:
#     ...
