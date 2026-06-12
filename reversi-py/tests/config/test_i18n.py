import locale
from config.i18n import Translator, _get_translator
import config.i18n as i18n_module


def test_translator_load_default_ja(tmp_path):
    # Setup mock translation files
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    (translations_dir / "main.ja.json").write_text('{"ja": {"test": "テスト"}}', encoding="utf-8")

    translator = Translator(translations_dir=str(translations_dir), lang_code="ja")

    assert translator.translate("test") == "テスト"


def test_translator_fallback_to_default_on_missing_key(tmp_path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    (translations_dir / "main.ja.json").write_text('{"ja": {"test": "テスト"}}', encoding="utf-8")

    translator = Translator(translations_dir=str(translations_dir), lang_code="ja")

    assert translator.translate("missing", default="Fallback") == "Fallback"


def test_global_t_helper(tmp_path, monkeypatch):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    (translations_dir / "main.ja.json").write_text('{"ja": {"test": "テスト"}}', encoding="utf-8")

    # We need to ensure the global translator is initialized with this mock dir
    import config.i18n as i18n
    monkeypatch.setattr(i18n, "TRANSLATIONS_DIR", str(translations_dir))
    i18n._translator = i18n.Translator(translations_dir=str(translations_dir), lang_code="ja")

    assert i18n._t("test") == "テスト"


def test_locale_detection_exception_uses_ja(tmp_path, monkeypatch):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    (translations_dir / "main.ja.json").write_text('{"ja": {"hello": "こんにちは"}}', encoding="utf-8")

    # make locale.getlocale raise
    def broken_getlocale():
        raise RuntimeError("locale error")

    monkeypatch.setattr(locale, "getlocale", broken_getlocale)

    translator = Translator(translations_dir=str(translations_dir), lang_code=None)
    assert translator.locale == "ja"
    assert translator.translate("hello") == "こんにちは"


def test_load_translations_invalid_format(tmp_path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    # top level value for 'en' is not a dict
    (translations_dir / "main.en.json").write_text('{"en": "not-a-dict"}', encoding="utf-8")

    translator = Translator(translations_dir=str(translations_dir), lang_code="en")
    assert translator.translations == {}


def test_load_translations_json_decode_error(tmp_path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    # invalid JSON to trigger JSONDecodeError
    (translations_dir / "main.ja.json").write_text('{ this is not: json', encoding="utf-8")

    translator = Translator(translations_dir=str(translations_dir), lang_code="ja")
    assert translator.translations == {}


def test_translate_formatting_and_keyerror(tmp_path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    (translations_dir / "main.ja.json").write_text(
        '{"ja": {"greet": "Hello {name}", "incomplete": "{missing}"}}',
        encoding="utf-8",
    )

    translator = Translator(translations_dir=str(translations_dir), lang_code="ja")
    assert translator.translate("greet", name="Alice") == "Hello Alice"
    # missing placeholder with kwargs should return the raw template (KeyError handled)
    assert translator.translate("incomplete", dummy=1) == "{missing}"


def test_translate_nested_keys(tmp_path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    (translations_dir / "main.ja.json").write_text(
        '{"ja": {"parent": {"child": "value"}}}', encoding="utf-8"
    )
    translator = Translator(translations_dir=str(translations_dir), lang_code="ja")
    assert translator.translate("parent.child") == "value"


def test_locale_fallback_to_ja_when_missing_locale_file(tmp_path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    (translations_dir / "main.ja.json").write_text('{"ja": {"test": "テスト"}}', encoding="utf-8")

    # Request 'en' while only 'ja' exists -> should fallback to ja
    translator = Translator(translations_dir=str(translations_dir), lang_code="en")
    assert translator.locale == "ja"
    assert translator.translate("test") == "テスト"


def test_locale_detection_none_returns_ja(tmp_path, monkeypatch):
    """locale.getlocale() が (None, ...) を返す場合のカバレッジ"""
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    (translations_dir / "main.ja.json").write_text('{"ja": {"test": "テスト"}}', encoding="utf-8")

    # Mock locale.getlocale to return (None, None)
    def mock_getlocale():
        return (None, None)

    monkeypatch.setattr(locale, "getlocale", mock_getlocale)

    translator = Translator(translations_dir=str(translations_dir), lang_code=None)
    assert translator.locale == "ja"


def test_get_translator_lazy_initialization(tmp_path, monkeypatch):
    """_get_translator の遅延初期化をテスト"""
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    (translations_dir / "main.ja.json").write_text('{"ja": {"test": "テスト"}}', encoding="utf-8")

    # Reset global _translator
    original_translator = i18n_module._translator
    original_dir = i18n_module.TRANSLATIONS_DIR
    try:
        i18n_module._translator = None
        i18n_module.TRANSLATIONS_DIR = str(translations_dir)

        # First call should initialize _translator
        translator1 = _get_translator()
        assert translator1 is not None

        # Second call should return the same instance
        translator2 = _get_translator()
        assert translator1 is translator2
    finally:
        i18n_module._translator = original_translator
        i18n_module.TRANSLATIONS_DIR = original_dir
