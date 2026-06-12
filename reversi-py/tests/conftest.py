# tests/conftest.py
import sys
import os
from unittest.mock import MagicMock

# GUI テスト用の環境変数を先に設定
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

# pygame を初期化（環境変数の設定後）
import pygame

pygame.init()

# pygame.font.Font の circular import 問題を回避
# pygame.font.Font を呼び出し可能なモックに設定
def mock_get_rect(**kwargs):
    rect = pygame.Rect(0, 0, 100, 24)
    for key, value in kwargs.items():
        setattr(rect, key, value)
    return rect

_surface_mock = MagicMock(spec=pygame.Surface)
_surface_mock.get_rect.side_effect = mock_get_rect

_font_instance_mock = MagicMock()
_font_instance_mock.render = MagicMock(return_value=_surface_mock)
_font_instance_mock.get_height = MagicMock(return_value=24)

pygame.font.Font = MagicMock(return_value=_font_instance_mock)  # type: ignore
pygame.font.SysFont = MagicMock(return_value=_font_instance_mock)  # type: ignore

# テストから参照できるようにグローバル変数として保持
_FONT_MOCK = _font_instance_mock


def pytest_configure(config):
    """pytest セッション開始時に実行"""
    # テスト用のグローバル設定
    sys.modules['test_gui_mocks'] = sys.modules[__name__]
