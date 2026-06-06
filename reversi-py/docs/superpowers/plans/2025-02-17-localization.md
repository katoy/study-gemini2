# Localization (i18n) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a centralized localization system (i18n) to support multiple languages in the Reversi game.

**Architecture:** Create a `Translator` singleton in `config/i18n.py` that loads translations from JSON files in `data/translations/`. Provide a global `_t` helper function for easy translation lookups.

**Tech Stack:** Python (standard library: `json`, `locale`, `os`)

---

### Task 1: Create `config/i18n.py`

**Files:**
- Create: `config/i18n.py`
- Test: `tests/config/test_i18n.py`

- [ ] **Step 1: Write failing tests for `Translator`**

```python
import pytest
from config.i18n import Translator, _t

def test_translator_load_default_ja(tmp_path):
    # Setup mock translation files
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    (translations_dir / "main.ja.json").write_text('{"ja": {"test": "テスト"}}', encoding="utf-8")
    
    translator = Translator(translations_dir=str(translations_dir), locale="ja")
    assert translator.translate("test") == "テスト"

def test_translator_fallback_to_default_on_missing_key(tmp_path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    (translations_dir / "main.ja.json").write_text('{"ja": {"test": "テスト"}}', encoding="utf-8")
    
    translator = Translator(translations_dir=str(translations_dir), locale="ja")
    assert translator.translate("missing", default="Fallback") == "Fallback"

def test_global_t_helper(tmp_path, monkeypatch):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    (translations_dir / "main.ja.json").write_text('{"ja": {"test": "テスト"}}', encoding="utf-8")
    
    # We need to ensure the global translator is initialized with this mock dir
    from config import i18n
    monkeypatch.setattr(i18n, "TRANSLATIONS_DIR", str(translations_dir))
    i18n._translator = i18n.Translator(locale="ja")
    
    assert i18n._t("test") == "テスト"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/config/test_i18n.py -v`
Expected: FAIL (ModuleNotFoundError or AttributeError)

- [ ] **Step 3: Implement `Translator` class and `_t` helper**

```python
import json
import os
import locale
from typing import Any, Dict, Optional

class Translator:
    def __init__(self, translations_dir: str = "data/translations", locale: Optional[str] = None):
        self.translations_dir = translations_dir
        if locale is None:
            # Try to detect system locale
            try:
                lang, _ = locale.getdefaultlocale()
                self.locale = lang[:2] if lang else "ja"
            except:
                self.locale = "ja"
        else:
            self.locale = locale
        
        self.translations: Dict[str, Any] = {}
        self.load_translations()

    def load_translations(self):
        filename = f"main.{self.locale}.json"
        path = os.path.join(self.translations_dir, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.translations = data.get(self.locale, {})
        else:
            # Fallback to ja if requested locale not found
            if self.locale != "ja":
                self.locale = "ja"
                self.load_translations()

    def translate(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        keys = key.split('.')
        value = self.translations
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
            except KeyError:
                return str(value)
        return str(value)

TRANSLATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "translations")
_translator = Translator(translations_dir=TRANSLATIONS_DIR)

def _t(key: str, default: Optional[str] = None, **kwargs) -> str:
    return _translator.translate(key, default, **kwargs)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/config/test_i18n.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add config/i18n.py tests/config/test_i18n.py
git commit -m "feat: implement Translator class and _t helper"
```

---

### Task 2: Update Translation Files

**Files:**
- Modify: `data/translations/main.ja.json`
- Modify: `data/translations/main.en.json`

- [ ] **Step 1: Update `data/translations/main.ja.json`**

```json
{
  "ja": {
    "window_title": "モーダルダイアログ サンプル",
    "settings_button": "設定",
    "quit_button": "終了",
    "game": {
      "black_turn": "黒の番です",
      "white_turn": "白の番です",
      "black_win": "黒の勝ちです！",
      "white_win": "白の勝ちです！",
      "draw": "引き分けです！",
      "black_pass": "黒はパスです。",
      "white_pass": "白はパスです。",
      "black_stones": "黒: {count}",
      "white_stones": "白: {count}"
    },
    "ui": {
      "start": "ゲーム開始",
      "restart": "リスタート",
      "reset": "リセット",
      "quit": "終了",
      "undo": "待った",
      "black_player": "黒プレイヤー",
      "white_player": "白プレイヤー"
    }
  }
}
```

- [ ] **Step 2: Update `data/translations/main.en.json`**

```json
{
  "en": {
    "window_title": "Modal Dialog Sample",
    "settings_button": "Settings",
    "quit_button": "Quit",
    "game": {
      "black_turn": "Black's turn",
      "white_turn": "White's turn",
      "black_win": "Black wins!",
      "white_win": "White wins!",
      "draw": "Draw!",
      "black_pass": "Black passed.",
      "white_pass": "White passed.",
      "black_stones": "Black: {count}",
      "white_stones": "White: {count}"
    },
    "ui": {
      "start": "Start",
      "restart": "Restart",
      "reset": "Reset",
      "quit": "Quit",
      "undo": "Undo",
      "black_player": "Black Player",
      "white_player": "White Player"
    }
  }
}
```

- [ ] **Step 3: Add integration test for loaded translations**

Add to `tests/config/test_i18n.py`:

```python
def test_real_translations_loaded():
    # This test assumes the real files are in data/translations/
    # and they have the expected structure.
    from config.i18n import _t
    # Default is likely ja
    val = _t("ui.start")
    assert val in ["ゲーム開始", "Start"]
```

- [ ] **Step 4: Run all tests**

Run: `pytest tests/config/test_i18n.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add data/translations/main.ja.json data/translations/main.en.json tests/config/test_i18n.py
git commit -m "feat: update translation files with game and ui keys"
```
