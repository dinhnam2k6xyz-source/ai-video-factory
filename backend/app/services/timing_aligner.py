import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from pydub import AudioSegment
from pydub.effects import speedup

class TimingAligner:
    """
    VideoLingo & Netflix-Standard Non-Destructive Audio Timeline Engine:
    - 100% Full Word Completion (Tuyệt đối không cắt đuôi, đảm bảo đọc trọn vẹn từng từ).
    - Dynamic Smart Speedup (0.90x - 1.38x): Tự động tăng tốc độ đọc mượt mà khi câu dài.
    - Adaptive Non-Overlapping Timeline: Tự động dời câu kế tiếp sau khoảng thở tự nhiên (30-50ms).
    - Đồng bộ mốc thời gian phụ đề khớp từng mili-giây với giọng đọc thực tế.
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
        Co giãn tốc độ audio segment trong bộ nhớ RAM (0.90x - 1.38x) và KHÔNG BAO GIỜ CẮT BỎ TỪ
        """
        current_ms = len(audio_seg)
        if current_ms <= 80 or target_ms <= 80:
            return audio_seg
            
        speed_factor = current_ms / float(target_ms)
        if speed_factor <= 1.02:
            return audio_seg
            
        try:
            # Tăng tốc độ đọc tự nhiên lên tối đa 1.38x để đọc kịp thời lượng
            effective_speed = min(1.38, max(1.03, speed_factor))
            stretched = speedup(audio_seg, playback_speed=effective_speed)
            return stretched
        except Exception as e:
            print(f"[TimingAligner] Speedup warning: {e}")
            return audio_seg

    def build_full_dub_track(self, segments: List[Dict[str, Any]], total_duration: float, temp_dir: Path) -> str:
        """
        Ghép tất cả các câu thoại vào timeline hoàn chỉnh:
        - Đảm bảo đọc hết 100% câu trước rồi mới chuyển sang câu sau
        - Tự động căn chỉnh mốc start/end của phụ đề khớp với giọng đọc thực tế
        """
        valid_segments = [
            s for s in segments 
            if s.get("tts_audio_path") and os.path.exists(s["tts_audio_path"]) and os.path.getsize(s["tts_audio_path"]) > 0
        ]
        
        valid_segments.sort(key=lambda x: float(x.get("start", 0)))
        
        # Dự trù tổng thời lượng an toàn
        total_ms = int(max(total_duration, 1.0) * 1000)
        full_dub = AudioSegment.silent(duration=total_ms + 10000, frame_rate=44100)
        full_dub_path = str(temp_dir / "full_dub_voice.wav")
        
        if not valid_segments:
            full_dub.export(full_dub_path, format="wav")
            return full_dub_path

        cursor_ms = 0
        num_segs = len(valid_segments)

        for i in range(num_segs):
            seg = valid_segments[i]
            orig_start = float(seg.get("start", 0))
            orig_end = float(seg.get("end", orig_start + 1.0))
            
            raw_audio_path = seg["tts_audio_path"]
            try:
                clip = AudioSegment.from_file(raw_audio_path)
                clip_ms = len(clip)
                
                # Tính toán slot thời gian dự kiến
                if i + 1 < num_segs:
                    next_start = float(valid_segments[i + 1].get("start", orig_end + 1.0))
                    slot_ms = int(max(0.4, next_start - orig_start) * 1000)
                else:
                    slot_ms = int(max(0.4, orig_end - orig_start) * 1000)

                # Nếu câu thoại dài hơn slot -> Tăng tốc độ đọc tự nhiên (lên đến 1.38x) để đọc trọn vẹn
                if clip_ms > slot_ms:
                    clip = self.stretch_audio_segment_fast(clip, slot_ms)
                    clip_ms = len(clip)

                # Vị trí đặt âm thanh: Không bao giờ đè lên câu trước (giữ khoảng nghỉ 40ms)
                start_pos_ms = max(int(orig_start * 1000), cursor_ms + 40 if cursor_ms > 0 else 0)
                
                # Overlay giọng đọc trọn vẹn (không cắt đuôi)
                full_dub = full_dub.overlay(clip, position=start_pos_ms)
                
                # Cập nhật cursor thời gian
                cursor_ms = start_pos_ms + clip_ms
                
                # Đồng bộ lại mốc thời gian start & end của segment để phụ đề hiển thị khớp tuyệt đối
                seg["start"] = start_pos_ms / 1000.0
                seg["end"] = (start_pos_ms + clip_ms) / 1000.0
            except Exception as e:
                print(f"[TimingAligner] Error processing segment {seg.get('id')}: {e}")

        # Cắt đúng thời lượng video nếu dài hơn (hoặc giữ tối thiểu bằng video)
        final_track = full_dub[:max(total_ms, cursor_ms + 500)]
        final_track.export(full_dub_path, format="wav")
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
        except Exception:
            return dub_voice_path

timing_aligner = TimingAligner()
