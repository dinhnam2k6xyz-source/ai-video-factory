import asyncio
import os
import re
import json
import base64
import wave
import edge_tts
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import requests
import subprocess

from app.core.config import settings

class TTSEngine:
    """
    Multi-Engine TTS Router with Real CapCut/ByteDance Integration & Natural Human Pacing:
    - Engine 1: Real ByteDance / CapCut Web TTS API (Giọng Nam/Nữ đặc trưng của CapCut & TikTok).
    - Engine 2: Custom / Self-Hosted CapCut TTS Endpoint (CAPCUT_TTS_URL).
    - Engine 3: Edge-TTS Neural với kiểm soát nhịp điệu tự nhiên (0.9x - 1.2x), chống méo tiếng.
    """
    
    CAPCUT_VOICE_MAP = {
        "capcut_serious_man": "BV001_streaming",    # Nam Trầm Review Phim
        "capcut_young_girl": "BV007_streaming",     # Nữ Hoạt Bát
        "capcut_calm_dubbing": "BV004_streaming",   # Nữ Kể Chuyện
        "capcut_confident_man": "BV002_streaming",  # Nam Tự Tin
        "capcut_little_sister": "BV005_streaming",  # Cô Bé Dễ Thương
        "capcut_energetic_boy": "BV003_streaming",  # Bé Trai
    }

    VOICE_PRESETS = {
        # CapCut Presets (Fallback sang Edge-TTS nếu CapCut API bận)
        "capcut_serious_man": {"base": "vi-VN-NamMinhNeural", "rate": "+4%", "pitch": "-6Hz"},
        "capcut_young_girl": {"base": "vi-VN-HoaiMyNeural", "rate": "+8%", "pitch": "+5Hz"},
        "capcut_calm_dubbing": {"base": "vi-VN-HoaiMyNeural", "rate": "-4%", "pitch": "+0Hz"},
        "capcut_confident_man": {"base": "vi-VN-NamMinhNeural", "rate": "+10%", "pitch": "+2Hz"},
        "capcut_little_sister": {"base": "vi-VN-HoaiMyNeural", "rate": "+5%", "pitch": "+10Hz"},
        "capcut_radio_host": {"base": "vi-VN-HoaiMyNeural", "rate": "-4%", "pitch": "-3Hz"},
        "capcut_wise_old_man": {"base": "vi-VN-NamMinhNeural", "rate": "-8%", "pitch": "-10Hz"},
        "capcut_grandma": {"base": "vi-VN-HoaiMyNeural", "rate": "-8%", "pitch": "-7Hz"},
        "capcut_energetic_boy": {"base": "vi-VN-NamMinhNeural", "rate": "+10%", "pitch": "+6Hz"},
        "capcut_robot": {"base": "vi-VN-NamMinhNeural", "rate": "+12%", "pitch": "+4Hz"},

        "vi-VN-NamMinhNeural": {"base": "vi-VN-NamMinhNeural", "rate": "+0%", "pitch": "+0Hz"},
        "vi-VN-HoaiMyNeural": {"base": "vi-VN-HoaiMyNeural", "rate": "+0%", "pitch": "+0Hz"},
        "vi-VN-NamMinhNeural_cinema": {"base": "vi-VN-NamMinhNeural", "rate": "+4%", "pitch": "-5Hz"},
        "vi-VN-HoaiMyNeural_story": {"base": "vi-VN-HoaiMyNeural", "rate": "-6%", "pitch": "+0Hz"},
        "vi-VN-NamMinhNeural_tiktok": {"base": "vi-VN-NamMinhNeural", "rate": "+12%", "pitch": "+2Hz"},
    }

    def __init__(self):
        self.semaphore = asyncio.Semaphore(12)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 10; vi_VN; Pixel 4)",
            "Accept": "application/json, text/plain, */*",
        })

    def _synthesize_capcut_bytedance(self, text: str, voice_code: str, output_path: str) -> bool:
        """
        Gọi trực tiếp ByteDance / CapCut TikTok TTS API
        """
        try:
            # 1. Nếu có cấu hình CAPCUT_TTS_URL riêng
            if settings.CAPCUT_TTS_URL:
                resp = self.session.post(
                    settings.CAPCUT_TTS_URL,
                    json={"text": text, "voice": voice_code},
                    timeout=6
                )
                if resp.status_code == 200 and len(resp.content) > 500:
                    with open(output_path, "wb") as f:
                        f.write(resp.content)
                    return True

            # 2. Gọi ByteDance Web Endpoint
            url = f"https://api16-normal-c-useast1a.tiktokv.com/media/api/text/speech/invoke/?text_speaker={voice_code}&req_text={requests.utils.quote(text)}&speaker_map_type=0&aid=1233"
            resp = self.session.post(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status_code") == 0 and data.get("data", {}).get("v_str"):
                    audio_b64 = data["data"]["v_str"]
                    audio_bytes = base64.b64decode(audio_b64)
                    with open(output_path, "wb") as f:
                        f.write(audio_bytes)
                    return True
        except Exception:
            pass
        return False

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
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", "anullsrc=r=24000:cl=mono",
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
        if not text or not text.strip():
            return self._create_silent_mp3(output_path, 0.3)
            
        clean_text = text.strip()
        if not re.search(r'[\w\d]', clean_text):
            return self._create_silent_mp3(output_path, 0.3)

        # 1. Thử CapCut ByteDance TTS nếu chọn voice capcut_
        if voice_id in self.CAPCUT_VOICE_MAP:
            bytedance_voice = self.CAPCUT_VOICE_MAP[voice_id]
            ok = self._synthesize_capcut_bytedance(clean_text, bytedance_voice, output_path)
            if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 500:
                return True

        # 2. Custom TTS Server nếu có
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

        # 3. Edge-TTS với Natural Human Pacing
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
                        await asyncio.sleep(0.3 * (attempt + 1))
                    else:
                        return self._create_silent_mp3(output_path, 0.8)
                    
        return Path(output_path).exists() and Path(output_path).stat().st_size > 0

    async def generate_segment_audios(
        self,
        segments: List[Dict[str, Any]],
        speaker_profiles: Dict[str, Any],
        temp_dir: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        total = len(segments)
        completed = 0

        default_voice_id = "capcut_serious_man"
        if speaker_profiles:
            first_profile = list(speaker_profiles.values())[0]
            default_voice_id = first_profile.get("voice_id", "capcut_serious_man")

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
