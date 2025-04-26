# config/theme.py
import pygame # 念のためインポート

# 色の定義
class Color:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 128, 0)
    GRAY = (128, 128, 128)
    RED = pygame.Color('red')
    BOARD = (0, 128, 0)
    BACKGROUND = (100, 100, 100)
    BUTTON = (50, 50, 50)
    BUTTON_TEXT = (200, 200, 200)
    DISABLED_TEXT = (100, 100, 100)
    DARK_BLUE = (0, 0, 128)
    LIGHT_BLUE = (173, 216, 230)

# 画面サイズとマージンの定義
class Screen:
    WIDTH = 450
    HEIGHT = 780 # UI要素が収まるように調整
    BOARD_SIZE = 400
    BOARD_TOP_MARGIN = 0
    BUTTON_MARGIN = 10
    BUTTON_VERTICAL_MARGIN = 3
    # --- マージン定義 ---
    TURN_MESSAGE_TOP_MARGIN = 10 # 石数表示と手番表示の間のマージン
    TURN_MESSAGE_BOTTOM_MARGIN = 15 # 手番表示とボタンの間のマージン
    BUTTON_BOTTOM_MARGIN = 15 # ボタンとプレイヤー設定UIの間のマージン
    PLAYER_SETTINGS_BOTTOM_MARGIN = 20 # プレイヤー設定UIとメッセージの間のマージン (現在は未使用)
    MESSAGE_MARGIN = 20 # メッセージと下端 or 他要素とのマージン (現在は未使用)
    MESSAGE_ABOVE_TURN_MARGIN = 10 # メッセージと手番表示の間のマージン (追加)
    # --------------------
    GAME_START_MESSAGE_TOP_MARGIN = 200
    RADIO_BUTTON_SIZE = 24
    RADIO_BUTTON_MARGIN = 10
    BUTTON_BORDER_WIDTH = 2
    CELL_SIZE = BOARD_SIZE // 8
    RADIO_BUTTON_INNER_CIRCLE_RATIO = 0.4
    RADIO_Y_OFFSET = 30
    RADIO_Y_SPACING = 30
