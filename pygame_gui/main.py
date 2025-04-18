# main.py
from app import PygameApp # app.pyからPygameAppクラスをインポート

if __name__ == "__main__":
    print("アプリケーションを開始します...")
    # PygameAppのインスタンスを作成して実行
    app = PygameApp()
    app.run()
    print("アプリケーションを終了しました。")
