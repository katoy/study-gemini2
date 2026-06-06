import json
import os
import locale
from typing import Any, Dict, Optional

class Translator:
    def __init__(self, translations_dir: str = "data/translations", lang_code: Optional[str] = None):
        self.translations_dir = translations_dir
        if lang_code is None:
            # Try to detect system locale
            try:
                # getdefaultlocale is deprecated in 3.11, but still works for now.
                # A better way would be locale.getlocale() or similar, 
                # but getdefaultlocale is common for detecting system language.
                lang, _ = locale.getdefaultlocale()
                self.locale = lang[:2] if lang else "ja"
            except Exception:
                self.locale = "ja"
        else:
            self.locale = lang_code
        
        self.translations: Dict[str, Any] = {}
        self.load_translations()

    def load_translations(self):
        filename = f"main.{self.locale}.json"
        path = os.path.join(self.translations_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    translations = data.get(self.locale)
                    if isinstance(translations, dict):
                        self.translations = translations
                    else:
                        self.translations = {}
            except (json.JSONDecodeError, IOError):
                self.translations = {}
        else:
            # Fallback to ja if requested locale not found
            if self.locale != "ja":
                self.locale = "ja"
                self.load_translations()

    def translate(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        keys = key.split('.')
        value: Any = self.translations
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break
        
        if value is None:
            return default if default is not None else key
        
        if kwargs:
            try:
                return str(value).format(**kwargs)
            except (KeyError, ValueError):
                return str(value)
        return str(value)

TRANSLATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "translations")
_translator: Optional[Translator] = None

def _get_translator() -> Translator:
    """遅延初期化により、モジュール読み込み時の状態汚染を防止"""
    global _translator
    if _translator is None:
        _translator = Translator(translations_dir=TRANSLATIONS_DIR)
    return _translator

def _t(key: str, default: Optional[str] = None, **kwargs) -> str:
    return _get_translator().translate(key, default, **kwargs)
