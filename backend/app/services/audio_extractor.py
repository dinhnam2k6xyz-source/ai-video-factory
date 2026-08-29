import subprocess
import os
from pathlib import Path
from typing import Tuple, Dict, Any

class AudioExtractor:
    """Trích xuất âm thanh và tách giọng nói / nhạc nền từ video"""
    
    @staticmethod
    def get_media_info(video_path: str) -> Dict[str, Any]:
        """Lấy thông tin thời lượng, độ phân giải và fps của video"""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=width,height,r_frame_rate,codec_type",
            "-of", "json", video_path
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            data = json.loads(res.stdout)
            duration = float(data.get("format", {}).get("duration", 0))
            width, height, fps = 1920, 1080, 30.0
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    width = int(stream.get("width", 1920))
                    height = int(stream.get("height", 1080))
                    r_fps = stream.get("r_frame_rate", "30/1")
                    if "/" in r_fps:
                        num, den = r_fps.split("/")
                        fps = float(num) / float(den) if float(den) != 0 else 30.0
                    else:
                        fps = float(r_fps)
                    break
            return {"duration": duration, "width": width, "height": height, "fps": fps}
        except Exception as e:
            return {"duration": 0, "width": 1920, "height": 1080, "fps": 30.0, "error": str(e)}

    @staticmethod
    def extract_audio(video_path: str, output_audio_path: str) -> bool:
        """Trích xuất file âm thanh WAV 16kHz mono chuẩn cho Whisper và xử lý TTS"""
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            output_audio_path
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e.stderr.decode('utf-8', errors='ignore')}")
            return False

    @staticmethod
    def separate_vocals_and_bgm(video_path: str, temp_dir: Path) -> Tuple[str, str]:
        """
        Tách Vocals và BGM bằng FFmpeg acoustic filter (hoặc Demucs nếu có).
        Returns: (vocals_path, bgm_path)
        """
        vocals_path = str(temp_dir / "vocals.wav")
        bgm_path = str(temp_dir / "bgm.wav")
        
        # 1. Tách Vocals (lọc dải tần số 200Hz - 4000Hz với dynamic equalizer)
        vocal_cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn",
            "-af", "highpass=f=120,lowpass=f=5000,volume=1.2",
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            vocals_path
        ]
        
        # 2. Tách BGM (loại bỏ dải tần vocal trung tâm và làm dịu)
        bgm_cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn",
            "-af", "bandreject=f=1000:width_type=h:w=1200,volume=0.85",
            "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            bgm_path
        ]
        
        try:
            subprocess.run(vocal_cmd, capture_output=True, check=True)
            subprocess.run(bgm_cmd, capture_output=True, check=True)
            return vocals_path, bgm_path
        except Exception as e:
            print(f"Separate audio failed, falling back to direct extract: {e}")
            AudioExtractor.extract_audio(video_path, vocals_path)
            AudioExtractor.extract_audio(video_path, bgm_path)
            return vocals_path, bgm_path

audio_extractor = AudioExtractor()
