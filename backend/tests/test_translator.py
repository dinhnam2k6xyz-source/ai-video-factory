import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import deep_translator  # noqa: F401
except ModuleNotFoundError:
    # Các kiểm thử này mock toàn bộ provider; stub giúp chạy được cả khi máy kiểm
    # thử chưa cài dependency runtime của ứng dụng.
    provider_module = types.ModuleType("deep_translator")

    class UnavailableProvider:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("Translation provider is not installed")

    provider_module.GoogleTranslator = UnavailableProvider
    provider_module.MyMemoryTranslator = UnavailableProvider
    sys.modules["deep_translator"] = provider_module

from app.services.translator import Translator


ERROR_500 = "Error 500 (Server Error)!!500. That's an error. Please try again later."


class ErrorProvider:
    def __init__(self, **_kwargs):
        pass

    def translate(self, _text):
        return ERROR_500


class VietnameseFallback:
    def __init__(self, **_kwargs):
        pass

    def translate(self, _text):
        return "Bản dịch dự phòng"


class TranslatorTests(unittest.TestCase):
    def setUp(self):
        self.translator = Translator()

    @patch("app.services.translator.time.sleep")
    @patch("app.services.translator.MyMemoryTranslator", ErrorProvider)
    @patch("app.services.translator.GoogleTranslator", ErrorProvider)
    @patch.object(Translator, "_get_gemini", return_value=None)
    def test_provider_error_is_never_used_as_a_translation(self, *_mocks):
        segments = [{"id": 1, "start": 0, "end": 1, "text": "天安门"}]

        translated = self.translator.translate_segments(segments, source_lang="zh", target_lang="vi")

        self.assertEqual(translated[0]["translated_text"], "天安门")
        self.assertNotIn("Error 500", translated[0]["translated_text"])

    @patch("app.services.translator.time.sleep")
    @patch("app.services.translator.MyMemoryTranslator", VietnameseFallback)
    @patch("app.services.translator.GoogleTranslator", ErrorProvider)
    @patch.object(Translator, "_get_gemini", return_value=None)
    def test_uses_independent_fallback_after_google_error(self, *_mocks):
        segments = [{"id": 1, "start": 0, "end": 1, "text": "你好"}]

        translated = self.translator.translate_segments(segments, source_lang="zh", target_lang="vi")

        self.assertEqual(translated[0]["translated_text"], "Bản dịch dự phòng")

    @patch("app.services.translator.GoogleTranslator")
    def test_same_language_does_not_call_a_provider(self, google_translator):
        segments = [{"id": 1, "start": 0, "end": 1, "text": "Xin chào"}]

        translated = self.translator.translate_segments(segments, source_lang="vi", target_lang="vi")

        self.assertEqual(translated[0]["translated_text"], "Xin chào")
        google_translator.assert_not_called()


if __name__ == "__main__":
    unittest.main()
