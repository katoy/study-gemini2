# config.py

class LayoutConfig:
    """
    アプリケーションのレイアウトとUI要素のサイズに関する定数を管理します。

    このクラスの定数は、ウィンドウ、ダイアログ、ボタンなどの
    サイズやマージン、および使用するフォント情報を定義します。
    """
    # --- ウィンドウとダイアログのサイズ ---
    WINDOW_WIDTH = 600      # メインウィンドウの幅 (ピクセル)
    WINDOW_HEIGHT = 400     # メインウィンドウの高さ (ピクセル)
    DIALOG_WIDTH = 400      # 設定ダイアログの幅 (ピクセル)
    DIALOG_HEIGHT = 300     # 設定ダイアログの高さ (ピクセル)

    # --- UI要素のサイズとマージン ---
    BUTTON_WIDTH = 150      # 標準的なボタンの幅 (ピクセル)
    BUTTON_HEIGHT = 50      # 標準的なボタンの高さ (ピクセル)
    MARGIN = 10             # UI要素間の標準的なマージン (ピクセル)

    # --- settings_dialog.py 用のレイアウト定数 ---
    # ↓↓↓ ここから追加 ↓↓↓
    DIALOG_LABEL_HEIGHT = 30        # ダイアログ内のラベルの高さ
    DIALOG_ENTRY_HEIGHT = 30        # ダイアログ内のテキスト入力欄の高さ
    DIALOG_RADIO_PANEL_HEIGHT = 50  # ダイアログ内のラジオボタンパネルの高さ
    DIALOG_RADIO_BUTTON_WIDTH = 110 # ダイアログ内のラジオボタンの幅
    DIALOG_RADIO_BUTTON_HEIGHT = 30 # ダイアログ内のラジオボタンの高さ
    DIALOG_ACTION_BUTTON_WIDTH = 100 # ダイアログ内のOK/キャンセルボタンの幅
    DIALOG_ACTION_BUTTON_HEIGHT = 40 # ダイアログ内のOK/キャンセルボタンの高さ
    # ↑↑↑ ここまで追加 ↑↑↑

    # --- フォント設定 ---
    FONT_NAME = "NotoSansJP-Regular.ttf" # デフォルトフォントのファイル名
    FONT_SIZE = 16          # 標準フォントサイズ (ポイント)

    # --- main.py 用の計算済みレイアウト値 ---
    BUTTON_Y = WINDOW_HEIGHT - BUTTON_HEIGHT - MARGIN * 2

# --- User Settings Defaults ---
DEFAULT_SETTINGS_FILENAME = "user_settings.json"
DEFAULT_USER_NAME = "User"
DEFAULT_OPTION_KEY = "#settings.option_a"
