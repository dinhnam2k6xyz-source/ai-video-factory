import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from pydub import AudioSegment

class TimingAligner:
    """
    Studio-Grade Natural Storytelling Audio Timeline Engine:
    - High-Fidelity Pitch-Preserving Time-Stretch (Loại bỏ 100% hiện tượng khựng/mất giọng/nói giật cục).
    - Micro Cross-Fading (15ms): Chuyển tiếp mượt mà giữa các câu thoại.
    - EBU R128 & Dynamic Audio Normalization (dynaudnorm + loudnorm): Âm lượng đồng đều tuyệt đối từ đầu đến cuối video, không còn lúc to lúc nhỏ.
    - 100% Full Sentence Completion: Đọc trọn vẹn từng từ trước khi sang câu mới.
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

    def stretch_audio_file_hq(self, input_path: str, speed_factor: float, output_path: str) -> bool:
        """
        Co giãn tốc độ audio bằng bộ lọc FFmpeg atempo chất lượng cao (giữ nguyên cao độ và độ trong của giọng nói)
        """
        if speed_factor <= 1.02:
            return False
            
        # Giới hạn tốc độ tự nhiên tối đa 1.35x
        tempo = min(1.35, max(0.9, speed_factor))
        cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-i", str(input_path),
            "-filter:a", f"atempo={tempo:.3f}",
            "-vn",
            str(output_path)
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception as e:
            print(f"[TimingAligner] atempo stretch warning: {e}")
            return False

    def build_full_dub_track(self, segments: List[Dict[str, Any]], total_duration: float, temp_dir: Path) -> str:
        """
        Ghép tất cả các câu thoại vào timeline hoàn chỉnh và tự nhiên:
        - Đảm bảo đọc hết 100% câu trước rồi mới chuyển sang câu sau
        - Tự động căn chỉnh mốc start/end của phụ đề khớp với giọng đọc thực tế
        """
        valid_segments = [
            s for s in segments 
            if s.get("tts_audio_path") and os.path.exists(s["tts_audio_path"]) and os.path.getsize(s["tts_audio_path"]) > 0
        ]
        
        valid_segments.sort(key=lambda x: float(x.get("start", 0)))
        
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
                # 1. Tính toán slot thời gian dự kiến
                if i + 1 < num_segs:
                    next_start = float(valid_segments[i + 1].get("start", orig_end + 1.0))
                    slot_ms = int(max(0.4, next_start - orig_start) * 1000)
                else:
                    slot_ms = int(max(0.4, orig_end - orig_start) * 1000)

                raw_dur_ms = len(AudioSegment.from_file(raw_audio_path))
                
                # 2. Nếu câu thoại dài hơn slot -> Dùng FFmpeg atempo chất lượng cao để tăng tốc nhẹ nhàng
                clip_path_to_use = raw_audio_path
                if raw_dur_ms > slot_ms + 100:
                    speed_factor = raw_dur_ms / float(slot_ms)
                    stretched_path = str(temp_dir / f"stretched_{i}.wav")
                    if self.stretch_audio_file_hq(raw_audio_path, speed_factor, stretched_path):
                        clip_path_to_use = stretched_path

                clip = AudioSegment.from_file(clip_path_to_use)
                # Áp dụng micro fade-in/fade-out 15ms để âm thanh không bị giật/khựng đầu đuôi
                clip = clip.fade_in(15).fade_out(20)
                clip_ms = len(clip)

                # 3. Vị trí đặt âm thanh: Không bao giờ đè lên câu trước (khoảng nghỉ tự nhiên 35ms)
                start_pos_ms = max(int(orig_start * 1000), cursor_ms + 35 if cursor_ms > 0 else 0)
                
                # Overlay giọng đọc trọn vẹn
                full_dub = full_dub.overlay(clip, position=start_pos_ms)
                
                # Cập nhật cursor thời gian
                cursor_ms = start_pos_ms + clip_ms
                
                # Đồng bộ lại mốc thời gian start & end của segment
                seg["start"] = start_pos_ms / 1000.0
                seg["end"] = (start_pos_ms + clip_ms) / 1000.0
            except Exception as e:
                print(f"[TimingAligner] Error processing segment {seg.get('id')}: {e}")

        # Xuất file WAV gốc
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
        Hòa âm giọng lồng tiếng chuẩn Studio với Dynamic Audio Normalizer (dynaudnorm + loudnorm):
        - Tự động cân bằng độ to nhỏ của từng câu từ, giọng đọc luôn đồng đều và truyền cảm
        """
        audio_filters = [
            "dynaudnorm=f=150:g=15:p=0.92:m=10.0:r=0.9",
            "loudnorm=I=-16:TP=-1.5:LRA=9"
        ]
        norm_filter_str = ",".join(audio_filters)

        if bgm_volume <= 0.0 or not os.path.exists(bgm_path):
            cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                "-i", dub_voice_path,
                "-af", norm_filter_str,
                "-ac", "2",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]
        else:
            filter_str = (
                f"[0:a]{norm_filter_str}[v];"
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
            print(f"[TimingAligner] Mix error: {e}")
            return dub_voice_path

timing_aligner = TimingAligner()
