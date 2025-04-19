# config.py

class LayoutConfig:
    """レイアウト関連の定数を管理するクラス"""
    WINDOW_WIDTH = 600      # メインウィンドウの幅
    WINDOW_HEIGHT = 400     # メインウィンドウの高さ
    DIALOG_WIDTH = 400      # 設定ダイアログの幅
    DIALOG_HEIGHT = 300     # 設定ダイアログの高さ
    BUTTON_WIDTH = 150      # ボタンの幅
    BUTTON_HEIGHT = 50      # ボタンの高さ
    MARGIN = 10             # UI要素間の標準マージン (BUTTON_MARGIN から変更)

    # --- フォント設定 ---
    FONT_NAME = "NotoSansJP-Regular.ttf" # ★★★ 使用するフォントファイル名を追加 ★★★
    FONT_SIZE = 16          # ★★★ 標準フォントサイズを追加 (preload_fonts で使用) ★★★
    # FONT_SIZE_NORMAL = 14   # 必要であれば残す or FONT_SIZE に統一
    # FONT_SIZE_LARGE = 18    # 必要であれば残す or FONT_SIZE に統一

    # --- main.py 用レイアウト ---
    BUTTON_Y = WINDOW_HEIGHT - BUTTON_HEIGHT - MARGIN * 2 # ボタンのY座標 (例)
