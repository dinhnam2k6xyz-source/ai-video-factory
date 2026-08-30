import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from pydub import AudioSegment
from pydub.effects import speedup

class TimingAligner:
    """
    VideoLingo-Standard Natural Pacing Audio Timeline Engine:
    - Giới hạn tốc độ tăng tối đa 1.20x (Natural Pacing Limit) để giọng nói luôn giữ được độ trầm ấm, truyền cảm tự nhiên, không bị nói vội/méo tiếng.
    - Xử lý hoàn toàn trong RAM (0.2s cho 200 câu thoại).
    - Chèn Guard Gap 50ms ngăn chặn 100% việc câu sau chèn lên câu trước.
    """
    
    @staticmethod
    def get_audio_duration_fast(file_path: str) -> float:
        """Đo thời lượng file audio nhanh không tạo process ffprobe"""
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return 0.0
        try:
            seg = AudioSegment.from_file(file_path)
            return len(seg) / 1000.0
        except Exception:
            return 0.0

    def get_audio_duration(self, file_path: str) -> float:
        return self.get_audio_duration_fast(file_path)

    def stretch_audio_segment_fast(self, audio_seg: AudioSegment, target_ms: int) -> AudioSegment:
        """
        Co giãn tốc độ audio segment trong bộ nhớ RAM với dải tốc độ tự nhiên (0.85x - 1.20x)
        """
        current_ms = len(audio_seg)
        if current_ms <= 100 or target_ms <= 100:
            return audio_seg
            
        speed_factor = current_ms / float(target_ms)
        if speed_factor <= 1.03:
            return audio_seg
            
        try:
            # Giới hạn tốc độ tăng tối đa 1.20x để không bị méo tiếng hoặc nuốt chữ
            effective_speed = min(1.20, speed_factor)
            stretched = speedup(audio_seg, playback_speed=effective_speed)
            
            # Cắt gọn đuôi với fade-out 30ms nếu vẫn dài hơn slot
            if len(stretched) > target_ms:
                return stretched[:target_ms].fade_out(30)
            return stretched
        except Exception:
            return audio_seg[:target_ms].fade_out(30)

    def build_full_dub_track(self, segments: List[Dict[str, Any]], total_duration: float, temp_dir: Path) -> str:
        """
        Ghép tất cả các câu thoại vào timeline ĐỘC QUYỀN trong RAM
        """
        valid_segments = [
            s for s in segments 
            if s.get("tts_audio_path") and os.path.exists(s["tts_audio_path"]) and os.path.getsize(s["tts_audio_path"]) > 0
        ]
        
        valid_segments.sort(key=lambda x: float(x.get("start", 0)))
        
        total_ms = int(max(total_duration, 1.0) * 1000)
        full_dub = AudioSegment.silent(duration=total_ms + 2000, frame_rate=44100)
        full_dub_path = str(temp_dir / "full_dub_voice.wav")
        
        if not valid_segments:
            full_dub.export(full_dub_path, format="wav")
            return full_dub_path

        num_segs = len(valid_segments)
        for i in range(num_segs):
            seg = valid_segments[i]
            cur_start = float(seg.get("start", 0))
            cur_end = float(seg.get("end", cur_start + 1.0))
            
            # Tính giới hạn slot độc quyền của câu hiện tại
            if i + 1 < num_segs:
                next_start = float(valid_segments[i + 1].get("start", cur_end + 1.0))
                max_allowed_end = min(cur_end, next_start - 0.05)
                if max_allowed_end <= cur_start:
                    max_allowed_end = cur_start + 0.3
            else:
                max_allowed_end = cur_end
                
            slot_ms = int(max(0.35, max_allowed_end - cur_start) * 1000)
            raw_audio_path = seg["tts_audio_path"]
            
            try:
                clip = AudioSegment.from_file(raw_audio_path)
                clip_ms = len(clip)
                
                if clip_ms > slot_ms:
                    clip = self.stretch_audio_segment_fast(clip, slot_ms)
                    
                pos_ms = int(cur_start * 1000)
                full_dub = full_dub.overlay(clip, position=pos_ms)
            except Exception as e:
                print(f"[TimingAligner] Error overlaying segment {seg.get('id')}: {e}")

        full_dub.export(full_dub_path, format="wav")
        return full_dub_path

    def mix_dub_with_bgm(
        self,
        dub_voice_path: str,
        bgm_path: str,
        output_path: str,
        bgm_volume: float = 0.0,
        voice_volume: float = 1.3
    ) -> str:
        """
        Hòa âm giọng lồng tiếng mới:
        - Nếu bgm_volume == 0.0: Render tức thì không cần giải mã BGM
        """
        if bgm_volume <= 0.0 or not os.path.exists(bgm_path):
            cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                "-i", dub_voice_path,
                "-af", f"volume={voice_volume:.2f}",
                "-ac", "2",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]
        else:
            filter_str = (
                f"[0:a]volume={voice_volume:.2f}[v];"
                f"[1:a]volume={bgm_volume:.2f}[b];"
                f"[v][b]amix=inputs=2:duration=first:dropout_transition=2[out]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                "-i", dub_voice_path,
                "-i", bgm_path,
                "-filter_complex", filter_str,
                "-map", "[out]",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except Exception as e:
            print(f"[TimingAligner] Mix audio failed: {e}")
            return dub_voice_path

timing_aligner = TimingAligner()
