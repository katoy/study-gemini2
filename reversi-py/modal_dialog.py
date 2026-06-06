import pygame
from typing import Any
from config.theme import Color

class ModalDialog:
    """
    モーダルダイアログを表すクラス。
    画面全体を覆う半透明の背景と、その上に表示されるコンテンツ領域を持つ。
    """
    def __init__(self, rect: pygame.Rect, font: pygame.font.Font, bg_color=Color.MODAL_BACKGROUND):
        """
        ModalDialogクラスのコンストラクタ。

        Args:
            rect (pygame.Rect): ダイアログの位置とサイズ。
            font (pygame.font.Font): テキスト描画に使用するフォント。
            bg_color: ダイアログの背景色。
        """
        self.rect = rect
        self.font = font
        self.bg_color = bg_color
        self.content: list[Any] = []  # UI要素を格納するリスト

    def add_element(self, element):
        """
        ダイアログにUI要素を追加する。

        Args:
            element: 追加するUI要素（Button, Labelなど）。
        """
        self.content.append(element)

    def draw(self, screen: pygame.Surface):
        """
        ダイアログをスクリーンに描画する。

        Args:
            screen (pygame.Surface): 描画対象のスクリーン。
        """
        # 半透明の背景を描画
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill(self.bg_color)
        screen.blit(overlay, (0, 0))

        # コンテンツ領域を描画
        pygame.draw.rect(screen, Color.MODAL_CONTENT, self.rect)

        # UI要素を描画
        for element in self.content:
            if hasattr(element, 'draw') and callable(element.draw):
                element.draw(screen)

    def is_clicked(self, pos: tuple[int, int]) -> bool:
        """
        指定された座標がダイアログの領域内にあるか判定する。

        Args:
            pos (tuple[int, int]): クリックされた座標。

        Returns:
            bool: ダイアログ内であれば True、そうでなければ False。
        """
        return self.rect.collidepoint(pos)
