import subprocess
import os
from pathlib import Path
from typing import Tuple, Dict, Any

class AudioExtractor:
    """Trích xuất âm thanh siêu tốc (Single-Pass Audio Decode)"""
    
    @staticmethod
    def get_media_info(video_path: str) -> Dict[str, Any]:
        """Lấy thông tin thời lượng, độ phân giải và fps của video qua ffprobe"""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=width,height,r_frame_rate,codec_type",
            "-of", "json", str(video_path)
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
            return {"duration": 60.0, "width": 1920, "height": 1080, "fps": 30.0, "error": str(e)}

    @staticmethod
    def extract_audio_single_pass(video_path: str, temp_dir: Path) -> Tuple[str, str]:
        """
        Single-Pass Audio Extraction:
        Chỉ giải mã video đúng 1 LẦN DUY NHẤT để xuất cả vocals.wav (16k mono cho ASR) và bgm.wav (44.1k stereo)
        """
        vocals_path = str(temp_dir / "vocals.wav")
        bgm_path = str(temp_dir / "bgm.wav")
        
        cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-i", str(video_path),
            "-vn",
            "-map", "0:a:0?", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", vocals_path,
            "-map", "0:a:0?", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", bgm_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return vocals_path, bgm_path
        except Exception as e:
            print(f"[AudioExtractor] Multi-output extract failed: {e}, falling back...")
            # Fallback nếu video không có audio track
            AudioExtractor.extract_audio(video_path, vocals_path)
            AudioExtractor.extract_audio(video_path, bgm_path)
            return vocals_path, bgm_path

    @staticmethod
    def extract_audio(video_path: str, output_audio_path: str) -> bool:
        """Trích xuất file âm thanh WAV 16kHz mono chuẩn cho ASR"""
        cmd = [
            "ffmpeg", "-y", "-threads", "0", "-i", str(video_path),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            str(output_audio_path)
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception as e:
            print(f"Error extracting audio: {e}")
            return False

    @staticmethod
    def separate_vocals_and_bgm(video_path: str, temp_dir: Path) -> Tuple[str, str]:
        return AudioExtractor.extract_audio_single_pass(video_path, temp_dir)

audio_extractor = AudioExtractor()
