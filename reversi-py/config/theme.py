class Color:
    """
    ゲームで使用する色を定義するクラス。
    """
    BACKGROUND = (32, 32, 32)       # 画面全体の背景色
    BOARD      = (0, 102, 0)        # 盤面の背景色
    BLACK      = (0, 0, 0)           # 黒石の色
    WHITE      = (255, 255, 255)       # 白石の色
    GRAY       = (128, 128, 128)     # 合法手マーカーの色
    DARK_BLUE  = (0, 0, 128)       # 濃い青色 (選択状態のラジオボタンなど)
    LIGHT_BLUE = (173, 216, 230)     # 薄い青色 (非選択状態のラジオボタンなど)
    DISABLED_TEXT = (192, 192, 192) # 無効なテキストの色
    BUTTON = (64, 64, 64)          # ボタンの背景色
    BUTTON_TEXT = (200, 200, 200)     # ボタンのテキスト色
    MODAL_BACKGROUND = (0, 0, 0, 128) # モーダルダイアログの背景色 (半透明)
    MODAL_CONTENT = (128, 128, 128)   # モーダルダイアログのコンテンツ領域の色

class Screen:
    """
    画面サイズやUI要素のサイズを定義するクラス。
    """
    WIDTH  = 800  # 画面の幅
    HEIGHT = 600  # 画面の高さ
    BOARD_SIZE = 400  # 盤面のサイズ
    CELL_SIZE  = BOARD_SIZE // 8  # セルのサイズ
    BOARD_TOP_MARGIN = 50  # 盤面の上マージン
    TURN_MESSAGE_TOP_MARGIN = 10 # 手番メッセージの上マージン
    TURN_MESSAGE_BOTTOM_MARGIN = 10 # 手番メッセージの下マージン
    GAME_START_MESSAGE_TOP_MARGIN = 200 # ゲーム開始メッセージの上マージン
    MESSAGE_ABOVE_TURN_MARGIN = 10 # パスなどのメッセージと手番表示の間隔
    RADIO_BUTTON_SIZE = 20 # ラジオボタンのサイズ
    RADIO_BUTTON_MARGIN = 5  # ラジオボタンとテキストの間隔
    RADIO_Y_OFFSET = 30      # ラジオボタンの垂直位置オフセット
    RADIO_Y_SPACING = 30     # ラジオボタンの間隔
    RADIO_BUTTON_INNER_CIRCLE_RATIO = 0.6 # 内側の円の半径の割合
    BUTTON_MARGIN = 10 # ボタンの左右マージン
    BUTTON_VERTICAL_MARGIN = 5 # ボタンの上下マージン
    BUTTON_BORDER_WIDTH = 2  # ボタンの枠線の太さ
    BUTTON_BOTTOM_MARGIN = 10 # ボタンの下マージン
