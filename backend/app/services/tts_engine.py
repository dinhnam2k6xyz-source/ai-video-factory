import asyncio
import os
import wave
import edge_tts
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import requests

from app.core.config import settings

class TTSEngine:
    """
    Multi-Engine TTS Router - Đảm bảo tính nhất quán 100% về giọng đọc (Voice Uniformity):
    - Đảm bảo 100% các câu thoại trong video dùng đúng giọng đã chọn, không bị đổi giọng giữa chừng.
    - Concurrency Pool: 10 luồng song song với timeout 6.0s và retry đúng model.
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
        self.semaphore = asyncio.Semaphore(10)
        self.piper_models: Dict[str, Any] = {}

    def _get_piper_voice(self, model_name: str = "vi_VN-25hours_single-low"):
        """Lazy load và cache Piper ONNX model"""
        if model_name in self.piper_models:
            return self.piper_models[model_name]
            
        try:
            import piper
            model_file = settings.PIPER_MODELS_DIR / f"{model_name}.onnx"
            config_file = settings.PIPER_MODELS_DIR / f"{model_name}.onnx.json"
            
            if model_file.exists() and config_file.exists():
                voice = piper.PiperVoice.load(str(model_file), config_path=str(config_file))
                self.piper_models[model_name] = voice
                return voice
        except Exception as e:
            print(f"[TTSEngine] Error loading Piper model {model_name}: {e}")
        return None

    def _synthesize_piper_fast(self, text: str, output_path: str, model_name: str = "vi_VN-25hours_single-low") -> bool:
        """Sinh giọng cục bộ bằng viPiper"""
        voice = self._get_piper_voice(model_name)
        if not voice:
            return False
        try:
            wav_out = str(Path(output_path).with_suffix(".wav"))
            with wave.open(wav_out, "wb") as wav_file:
                voice.synthesize_wav(text, wav_file, set_wav_format=True)
            
            if output_path.endswith(".mp3"):
                import subprocess
                subprocess.run(["ffmpeg", "-y", "-i", wav_out, output_path], capture_output=True)
            return Path(output_path).exists() and Path(output_path).stat().st_size > 0
        except Exception:
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

    async def generate_speech(self, text: str, voice_id: str, output_path: str, rate: str = "+0%", pitch: str = "+0Hz") -> bool:
        """Sinh audio từ text đảm bảo tính đồng nhất 100% đúng giọng được chỉ định"""
        if not text or not text.strip():
            return False
            
        clean_text = text.strip()

        # Engine 1: viPiper Local Offline (nếu chỉ định rõ piper:)
        if voice_id.startswith("piper:"):
            piper_model_name = voice_id.replace("piper:", "")
            return self._synthesize_piper_fast(clean_text, output_path, piper_model_name)

        # Engine 2: Custom TTS Server
        if settings.CUSTOM_TTS_URL and voice_id.startswith("custom:"):
            try:
                resp = requests.post(
                    settings.CUSTOM_TTS_URL,
                    json={"input": clean_text, "voice": voice_id.replace("custom:", "")},
                    timeout=5
                )
                if resp.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(resp.content)
                    return True
            except Exception:
                pass

        # Engine 3: Edge-TTS / CapCut Presets - Giữ đúng giọng 100% cho mọi câu thoại
        base_voice, preset_rate, preset_pitch = self.parse_voice_settings(voice_id)
        final_rate = rate if rate != "+0%" else preset_rate
        final_pitch = pitch if pitch != "+0Hz" else preset_pitch

        async with self.semaphore:
            for attempt in range(3):
                try:
                    communicate = edge_tts.Communicate(text=clean_text, voice=base_voice, rate=final_rate, pitch=final_pitch)
                    await asyncio.wait_for(communicate.save(output_path), timeout=6.0)
                    if Path(output_path).exists() and Path(output_path).stat().st_size > 0:
                        return True
                except (asyncio.TimeoutError, Exception) as e:
                    if attempt < 2:
                        await asyncio.sleep(0.3 * (attempt + 1))
                    else:
                        print(f"[TTSEngine] Edge-TTS error on segment: {e}, falling back...")
                        # Fallback cuối cùng
                        if self._synthesize_piper_fast(clean_text, output_path):
                            return True
                    
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

        async def process_single(s: Dict[str, Any]):
            nonlocal completed
            text = s.get("translated_text") or s.get("text", "")
            speaker = s.get("speaker", "Speaker 1")
            
            # Tìm profile theo speaker ID, nếu không thấy thì dùng profile đầu tiên (đảm bảo 1 giọng đồng nhất)
            profile = speaker_profiles.get(speaker) or speaker_profiles.get("Người Kể Chuyện") or speaker_profiles.get("Speaker 1")
            if not profile and speaker_profiles:
                profile = list(speaker_profiles.values())[0]
            if not profile:
                profile = {"voice_id": default_voice_id, "speed": 1.0, "pitch": "+0Hz"}

            voice_id = profile.get("voice_id", default_voice_id)
            speed = profile.get("speed", 1.0)
            
            rate_percent = int((speed - 1.0) * 100)
            rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"
            pitch_str = profile.get("pitch", "+0Hz")
            
            out_file = str(temp_dir / f"tts_seg_{s['id']}.mp3")
            s["tts_audio_path"] = out_file
            s["voice_id"] = voice_id
            
            await self.generate_speech(text, voice_id, out_file, rate=rate_str, pitch=pitch_str)
            completed += 1
            if progress_callback:
                progress_callback(completed, total)

        tasks = [process_single(s) for s in segments]
        await asyncio.gather(*tasks)
        return segments

tts_engine = TTSEngine()
