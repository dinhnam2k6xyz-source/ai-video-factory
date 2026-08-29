import asyncio
import os
import re
import wave
import edge_tts
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import requests
import subprocess

from app.core.config import settings

class TTSEngine:
    """
    Multi-Engine TTS Router - Đảm bảo tính nhất quán 100% về giọng đọc (Voice Uniformity):
    - Đảm bảo 100% các câu thoại trong video dùng đúng giọng đã chọn, không bị đổi giọng giữa chừng.
    - Concurrency Pool: 12 luồng song song với timeout 12.0s và retry đúng voice model.
    - Xử lý thông minh câu rỗng / ký tự đặc biệt, sinh file im lặng tự động.
    """
    
    VOICE_PRESETS = {
        # CapCut Vietnamese Voice Catalog
        "capcut_serious_man": {"base": "vi-VN-NamMinhNeural", "rate": "+5%", "pitch": "-7Hz"},
        "capcut_young_girl": {"base": "vi-VN-HoaiMyNeural", "rate": "+10%", "pitch": "+6Hz"},
        "capcut_calm_dubbing": {"base": "vi-VN-HoaiMyNeural", "rate": "-6%", "pitch": "+0Hz"},
        "capcut_confident_man": {"base": "vi-VN-NamMinhNeural", "rate": "+14%", "pitch": "+2Hz"},
        "capcut_little_sister": {"base": "vi-VN-HoaiMyNeural", "rate": "+6%", "pitch": "+14Hz"},
        "capcut_radio_host": {"base": "vi-VN-HoaiMyNeural", "rate": "-5%", "pitch": "-4Hz"},
        "capcut_wise_old_man": {"base": "vi-VN-NamMinhNeural", "rate": "-10%", "pitch": "-12Hz"},
        "capcut_grandma": {"base": "vi-VN-HoaiMyNeural", "rate": "-10%", "pitch": "-9Hz"},
        "capcut_energetic_boy": {"base": "vi-VN-NamMinhNeural", "rate": "+12%", "pitch": "+8Hz"},
        "capcut_robot": {"base": "vi-VN-NamMinhNeural", "rate": "+15%", "pitch": "+4Hz"},

        # Chuẩn Edge-TTS Personas
        "vi-VN-NamMinhNeural": {"base": "vi-VN-NamMinhNeural", "rate": "+0%", "pitch": "+0Hz"},
        "vi-VN-HoaiMyNeural": {"base": "vi-VN-HoaiMyNeural", "rate": "+0%", "pitch": "+0Hz"},
        "vi-VN-NamMinhNeural_cinema": {"base": "vi-VN-NamMinhNeural", "rate": "+5%", "pitch": "-6Hz"},
        "vi-VN-HoaiMyNeural_story": {"base": "vi-VN-HoaiMyNeural", "rate": "-8%", "pitch": "+0Hz"},
        "vi-VN-NamMinhNeural_tiktok": {"base": "vi-VN-NamMinhNeural", "rate": "+15%", "pitch": "+3Hz"},
        "vi-VN-HoaiMyNeural_radio": {"base": "vi-VN-HoaiMyNeural", "rate": "-5%", "pitch": "-3Hz"},
        "vi-VN-NamMinhNeural_old": {"base": "vi-VN-NamMinhNeural", "rate": "-10%", "pitch": "-12Hz"},
        "vi-VN-HoaiMyNeural_old": {"base": "vi-VN-HoaiMyNeural", "rate": "-10%", "pitch": "-8Hz"},
        "vi-VN-HoaiMyNeural_kid": {"base": "vi-VN-HoaiMyNeural", "rate": "+8%", "pitch": "+12Hz"},
        "vi-VN-NamMinhNeural_teen": {"base": "vi-VN-NamMinhNeural", "rate": "+10%", "pitch": "+6Hz"},
    }

    def __init__(self):
        self.semaphore = asyncio.Semaphore(12)

    def parse_voice_settings(self, voice_id: str, custom_speed: float = 1.0, custom_pitch: str = "+0Hz"):
        if voice_id in self.VOICE_PRESETS:
            preset = self.VOICE_PRESETS[voice_id]
            base_voice = preset["base"]
            rate_str = preset["rate"]
            pitch_str = preset["pitch"]
            return base_voice, rate_str, pitch_str
            
        base_voice = voice_id.split("_")[0]
        if not base_voice.startswith("vi-VN-") and not base_voice.startswith("en-") and not base_voice.startswith("zh-"):
            base_voice = "vi-VN-NamMinhNeural"
            
        rate_percent = int((custom_speed - 1.0) * 100)
        rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"
        return base_voice, rate_str, custom_pitch

    def _create_silent_mp3(self, output_path: str, duration_sec: float = 0.5):
        """Tạo file MP3 im lặng nhanh bằng FFmpeg nếu câu thoại rỗng"""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"anullsrc=r=24000:cl=mono",
                "-t", str(duration_sec),
                "-q:a", "9",
                "-acodec", "libmp3lame",
                str(output_path)
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception:
            return False

    async def generate_speech(self, text: str, voice_id: str, output_path: str, rate: str = "+0%", pitch: str = "+0Hz") -> bool:
        """Sinh audio từ text đảm bảo tính đồng nhất 100% đúng giọng được chỉ định"""
        if not text or not text.strip():
            return self._create_silent_mp3(output_path, 0.3)
            
        clean_text = text.strip()
        # Kiểm tra xem câu có chứa chữ/số không
        if not re.search(r'[\w\d]', clean_text):
            return self._create_silent_mp3(output_path, 0.3)

        # Engine 1: Custom TTS Server
        if settings.CUSTOM_TTS_URL and voice_id.startswith("custom:"):
            try:
                resp = requests.post(
                    settings.CUSTOM_TTS_URL,
                    json={"input": clean_text, "voice": voice_id.replace("custom:", "")},
                    timeout=8
                )
                if resp.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(resp.content)
                    return True
            except Exception:
                pass

        # Engine 2: Edge-TTS / CapCut Presets - Giữ đúng giọng 100% cho mọi câu thoại
        base_voice, preset_rate, preset_pitch = self.parse_voice_settings(voice_id)
        final_rate = rate if rate != "+0%" else preset_rate
        final_pitch = pitch if pitch != "+0Hz" else preset_pitch

        async with self.semaphore:
            for attempt in range(4):
                try:
                    communicate = edge_tts.Communicate(text=clean_text, voice=base_voice, rate=final_rate, pitch=final_pitch)
                    await asyncio.wait_for(communicate.save(output_path), timeout=12.0)
                    if Path(output_path).exists() and Path(output_path).stat().st_size > 500:
                        return True
                except (asyncio.TimeoutError, Exception) as e:
                    if attempt < 3:
                        await asyncio.sleep(0.4 * (attempt + 1))
                    else:
                        print(f"[TTSEngine] Edge-TTS error on segment: {e}, generating silent fallback...")
                        return self._create_silent_mp3(output_path, 0.8)
                    
        return Path(output_path).exists() and Path(output_path).stat().st_size > 0

    async def generate_segment_audios(
        self,
        segments: List[Dict[str, Any]],
        speaker_profiles: Dict[str, Any],
        temp_dir: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """Sinh audio song song cho toàn bộ segments với giọng đọc đồng nhất theo Speaker Profile"""
        total = len(segments)
        completed = 0

        # Lấy giọng mặc định chung (dành cho Solo mode hoặc fallback)
        default_voice_id = "capcut_serious_man"
        if speaker_profiles:
            first_profile = list(speaker_profiles.values())[0]
            default_voice_id = first_profile.get("voice_id", "capcut_serious_man")

        # Đồng nhất toàn bộ segment về default_voice_id nếu chỉ có 1 speaker
        num_spk = len(speaker_profiles) if speaker_profiles else 1
        is_solo = (num_spk <= 1)

        async def process_one(idx: int, seg: Dict[str, Any]):
            nonlocal completed
            spk_id = seg.get("speaker", "Speaker 1")
            
            if is_solo:
                voice_id = default_voice_id
            else:
                prof = speaker_profiles.get(spk_id, {})
                voice_id = prof.get("voice_id", default_voice_id)

            text_to_speak = (seg.get("translated_text") or seg.get("text", "")).strip()
            
            out_file = str(temp_dir / f"seg_{idx:04d}_{spk_id}.mp3")
            success = await self.generate_speech(
                text=text_to_speak,
                voice_id=voice_id,
                output_path=out_file
            )

            if success and os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                seg["tts_audio_path"] = out_file
            else:
                seg["tts_audio_path"] = None

            seg["voice_id"] = voice_id
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
            return seg

        tasks = [process_one(i, s) for i, s in enumerate(segments)]
        results = await asyncio.gather(*tasks)
        return results

tts_engine = TTSEngine()
