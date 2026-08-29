import json
import re
import time
import urllib.parse
import requests
from typing import Any, Dict, List, Optional

from app.core.config import settings

class Translator:
    """Dịch thông minh theo lô (Batch) sử dụng Chrome Extension Client & MyMemory dự phòng"""

    BATCH_SIZE = 25

    def __init__(self):
        self._gemini_client = None
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "*/*",
        })

    def _get_gemini(self):
        if self._gemini_client is None and settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._gemini_client = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as error:
                print(f"[Translator] Gemini init error: {error}")
        return self._gemini_client

    def translate_segments(
        self,
        segments: List[Dict[str, Any]],
        target_lang: str = "vi",
        source_lang: str = "auto",
    ) -> List[Dict[str, Any]]:
        """Dịch danh sách segments sang ngôn ngữ đích chuẩn xác"""
        if not segments:
            return segments

        # 1. Thử dịch bằng Gemini nếu có API Key
        gemini = self._get_gemini()
        if gemini:
            translated_map = self._translate_with_gemini(segments, target_lang)
            if translated_map:
                for seg in segments:
                    clean_res = self._clean_translation(translated_map.get(str(seg.get("id"))))
                    if clean_res:
                        seg["translated_text"] = clean_res
                unresolved = [s for s in segments if not s.get("translated_text")]
                if not unresolved:
                    return segments

        # 2. Dịch theo lô bằng Chrome Extension Client
        self._translate_in_batches(segments, target_lang=target_lang, source_lang=source_lang)

        # 3. Dịch bổ sung từng câu chưa dịch bằng MyMemory
        for seg in segments:
            clean_res = self._clean_translation(seg.get("translated_text"))
            if not clean_res or clean_res == self._original_text(seg):
                fallback_res = self._fetch_mymemory(self._original_text(seg), target_lang=target_lang, source_lang=source_lang)
                if fallback_res:
                    seg["translated_text"] = fallback_res
                else:
                    seg["translated_text"] = clean_res or self._original_text(seg)

        return segments

    def _translate_in_batches(self, segments: List[Dict[str, Any]], target_lang: str, source_lang: str) -> None:
        """Chia nhỏ thành các batch 25 câu để dịch nhanh và không bị rate-limit"""
        sl = self._normalise_lang(source_lang)
        tl = self._normalise_lang(target_lang)

        for i in range(0, len(segments), self.BATCH_SIZE):
            chunk = segments[i:i + self.BATCH_SIZE]
            
            texts_to_translate = []
            for s in chunk:
                original = self._original_text(s)
                cleaned_line = original.replace("\n", " ").strip()
                texts_to_translate.append(cleaned_line if cleaned_line else "...")

            joined_text = "\n".join(texts_to_translate)
            translated_lines = self._fetch_chrome_ext_translation(joined_text, target_lang=tl, source_lang=sl)

            if translated_lines and len(translated_lines) == len(chunk):
                for seg, trans in zip(chunk, translated_lines):
                    seg["translated_text"] = trans.strip()
            else:
                # Nếu dịch cả cụm bị lệch dòng, dịch từng câu đơn
                for seg in chunk:
                    orig = self._original_text(seg)
                    if not orig:
                        seg["translated_text"] = ""
                        continue
                    single_res = self._fetch_chrome_ext_single(orig, target_lang=tl, source_lang=sl)
                    if single_res:
                        seg["translated_text"] = single_res
                    else:
                        mymemory_res = self._fetch_mymemory(orig, target_lang=tl, source_lang=sl)
                        seg["translated_text"] = mymemory_res or orig

            if i + self.BATCH_SIZE < len(segments):
                time.sleep(0.1)

    def _fetch_chrome_ext_translation(self, text: str, target_lang: str, source_lang: str) -> Optional[List[str]]:
        """Gọi Google Translate Chrome Extension RPC với văn bản nhiều dòng"""
        try:
            encoded = urllib.parse.quote(text)
            url = f"https://translate.googleapis.com/translate_a/single?client=dict-chrome-ex&sl={source_lang}&tl={target_lang}&dt=t&q={encoded}"
            
            resp = self.session.get(url, timeout=12)
            if resp.status_code != 200:
                return None

            data = resp.json()
            if not data or not isinstance(data, list) or len(data) == 0:
                return None

            full_translated_text = "".join([part[0] for part in data[0] if part and part[0]])
            
            if self._is_provider_error_response(full_translated_text):
                return None

            lines = full_translated_text.split("\n")
            return lines
        except Exception as e:
            print(f"[Translator] Batch Chrome Ext fetch error: {e}")
            return None

    def _fetch_chrome_ext_single(self, text: str, target_lang: str, source_lang: str) -> Optional[str]:
        """Dịch 1 câu qua Google Translate Chrome Extension Client"""
        try:
            encoded = urllib.parse.quote(text)
            url = f"https://translate.googleapis.com/translate_a/single?client=dict-chrome-ex&sl={source_lang}&tl={target_lang}&dt=t&q={encoded}"
            
            resp = self.session.get(url, timeout=8)
            if resp.status_code != 200:
                return None

            data = resp.json()
            if not data or not isinstance(data, list) or len(data) == 0:
                return None

            result_text = "".join([part[0] for part in data[0] if part and part[0]])
            if self._is_provider_error_response(result_text):
                return None

            return result_text.strip()
        except Exception:
            return None

    def _fetch_mymemory(self, text: str, target_lang: str, source_lang: str) -> Optional[str]:
        """Dịch dự phòng qua MyMemory API"""
        try:
            sl = source_lang if source_lang != "auto" else "auto"
            tl = target_lang
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={sl}|{tl}"
            resp = self.session.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                translated = data.get("responseData", {}).get("translatedText")
                if translated and not self._is_provider_error_response(translated):
                    return translated.strip()
        except Exception:
            pass
        return None

    def _translate_with_gemini(
        self, segments: List[Dict[str, Any]], target_lang: str
    ) -> Dict[str, str]:
        gemini = self._get_gemini()
        if not gemini:
            return {}

        try:
            items_to_send = [
                {
                    "id": segment.get("id"),
                    "text": self._original_text(segment),
                    "duration": round(float(segment.get("end", 0)) - float(segment.get("start", 0)), 1),
                }
                for segment in segments
            ]
            prompt = (
                f"Bạn là chuyên gia dịch thuật và lồng tiếng video chuyên nghiệp. "
                f"Hãy dịch các câu thoại sau sang ngôn ngữ '{target_lang}' sao cho tự nhiên, "
                f"chuẩn văn phong nói và số từ/âm tiết tương đương để vừa khớp với thời gian thoại gốc.\n"
                f"Chỉ trả về JSON array hợp lệ theo format: "
                f"[{{\"id\": 0, \"translated_text\": \"...\"}}].\n\n"
                f"Danh sách câu:\n{json.dumps(items_to_send, ensure_ascii=False)}"
            )
            content = gemini.generate_content(prompt).text.strip()
            content = self._strip_code_fence(content)
            translated_items = json.loads(content)
            if not isinstance(translated_items, list):
                return {}

            return {
                str(item["id"]): item["translated_text"]
                for item in translated_items
                if isinstance(item, dict)
                and "id" in item
                and self._clean_translation(item.get("translated_text"))
            }
        except Exception as error:
            print(f"[Translator] Gemini translation error: {error}")
            return {}

    @staticmethod
    def _normalise_lang(lang: str) -> str:
        if not lang or lang == "auto":
            return "auto"
        l = lang.strip().lower()
        if l in ["zh", "cn", "zh-cn", "chinese"]:
            return "zh-CN"
        if l in ["vi", "vietnamese"]:
            return "vi"
        if l in ["en", "english"]:
            return "en"
        if l in ["ja", "japanese"]:
            return "ja"
        if l in ["ko", "korean"]:
            return "ko"
        return l

    @staticmethod
    def _original_text(segment: Dict[str, Any]) -> str:
        return str(segment.get("text") or "").strip()

    @classmethod
    def _clean_translation(cls, value: Any) -> Optional[str]:
        if not isinstance(value, str):
            return None

        translated = value.strip()
        if not translated or cls._is_provider_error_response(translated):
            return None
        return translated

    @staticmethod
    def _is_provider_error_response(value: str) -> bool:
        if not value:
            return True
        normalised = re.sub(r"\s+", " ", value).strip().lower()
        error_markers = (
            "that's an error",
            "there was an error",
            "please try again later",
            "server error",
            "internal server error",
            "too many requests",
            "rate limit exceeded",
            "access denied",
            "captcha",
            "error 500",
            "500. that's an error",
            "error 429",
            "error 403",
            "<html",
            "<!doctype html",
        )
        if any(marker in normalised for marker in error_markers):
            return True
        return bool(re.search(r"\b(?:error|http)\s*(?:code\s*)?[45]\d{2}\b", normalised))

    @staticmethod
    def _strip_code_fence(content: str) -> str:
        if not content.startswith("```"):
            return content
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

translator = Translator()
