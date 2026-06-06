import pytest
import os
import json
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
    import config.i18n as i18n
    monkeypatch.setattr(i18n, "TRANSLATIONS_DIR", str(translations_dir))
    i18n._translator = i18n.Translator(translations_dir=str(translations_dir), locale="ja")
    
    assert i18n._t("test") == "テスト"
