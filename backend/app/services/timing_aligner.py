import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any
from pydub import AudioSegment

class TimingAligner:
    """
    Exclusive Timeline Audio Engine (Chống Chồng Giọng & Tràn Slot 100%):
    - Đảm bảo mỗi câu thoại có Timeline Slot độc quyền (Slot_A.end <= Slot_B.start)
    - Tự động Time-Stretch (atempo) co giãn tốc độ để audio không bao giờ tràn sang câu kế tiếp
    - Chèn khoảng lặng bảo vệ (Guard Gap 50ms) giữa các nhân vật
    - Triệt tiêu hoàn toàn âm thanh gốc (Zero Voice Bleed)
    """
    
    @staticmethod
    def get_audio_duration(file_path: str) -> float:
        """Đo thời lượng chính xác của 1 file âm thanh bằng ffprobe"""
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return 0.0
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(res.stdout.strip())
        except Exception:
            return 0.0

    def align_and_stretch_audio(self, input_audio: str, target_duration: float, output_audio: str) -> str:
        """
        Co giãn tốc độ audio bằng bộ lọc atempo của FFmpeg mà không làm đổi cao độ (pitch).
        Hỗ trợ đa tầng atempo cho tốc độ từ 0.5x đến 3.0x để đảm bảo vừa khít slot thời gian.
        """
        current_duration = self.get_audio_duration(input_audio)
        if current_duration <= 0.1 or target_duration <= 0.1:
            return input_audio
            
        speed_factor = current_duration / target_duration
        
        # Xây dựng filter atempo đa tầng (atempo của ffmpeg hỗ trợ 0.5 - 2.0 cho mỗi node)
        if speed_factor <= 0.5:
            filter_str = "atempo=0.5"
        elif speed_factor <= 2.0:
            filter_str = f"atempo={speed_factor:.3f}"
        else:
            # Nếu câu dịch quá dài so với slot gốc, ghép 2 tầng atempo (ví dụ: atempo=2.0,atempo=1.2)
            first_factor = 2.0
            second_factor = min(1.5, speed_factor / 2.0)
            filter_str = f"atempo={first_factor:.3f},atempo={second_factor:.3f}"

        cmd = [
            "ffmpeg", "-y",
            "-i", input_audio,
            "-filter:a", filter_str,
            "-vn", output_audio
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_audio
        except Exception as e:
            print(f"[TimingAligner] atempo stretch error: {e}")
            return input_audio

    def build_full_dub_track(self, segments: List[Dict[str, Any]], total_duration: float, temp_dir: Path) -> str:
        """
        Ghép tất cả các câu thoại vào timeline ĐỘC QUYỀN.
        Quy tắc nghiêm ngặt:
        1. Câu A kết thúc <= Câu B bắt đầu (End_A <= Start_B - 0.05s).
        2. Nếu audio câu A dài hơn slot cho phép, lập tức co giãn (stretch) và cắt gọn fade-out,
           tuyệt đối không để âm thanh tràn sang câu tiếp theo.
        """
        valid_segments = [
            s for s in segments 
            if s.get("tts_audio_path") and os.path.exists(s["tts_audio_path"]) and os.path.getsize(s["tts_audio_path"]) > 0
        ]
        
        # Sắp xếp các phân đoạn theo thứ tự thời gian tăng dần
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
            
            # Tính giới hạn thời gian tối đa cho slot của câu hiện tại
            if i + 1 < num_segs:
                next_start = float(valid_segments[i + 1].get("start", cur_end + 1.0))
                # Để lại khoảng nghỉ an toàn 50ms trước câu tiếp theo
                max_allowed_end = min(cur_end, next_start - 0.05)
                if max_allowed_end <= cur_start:
                    max_allowed_end = cur_start + 0.3
            else:
                max_allowed_end = cur_end
                
            slot_duration = max(0.35, max_allowed_end - cur_start)
            raw_audio_path = seg["tts_audio_path"]
            raw_duration = self.get_audio_duration(raw_audio_path)
            
            stretched_path = str(temp_dir / f"stretched_seg_{seg['id']}.wav")
            
            # Nếu thời lượng audio thực tế vượt quá slot cho phép, co giãn tốc độ
            if raw_duration > slot_duration:
                self.align_and_stretch_audio(raw_audio_path, slot_duration, stretched_path)
                final_clip_path = stretched_path if os.path.exists(stretched_path) else raw_audio_path
            else:
                final_clip_path = raw_audio_path

            try:
                clip = AudioSegment.from_file(final_clip_path)
                
                # Giới hạn độ dài clip không được vượt quá slot ms (cắt và fade-out 20ms nếu cần)
                max_slot_ms = int(slot_duration * 1000)
                if len(clip) > max_slot_ms:
                    clip = clip[:max_slot_ms].fade_out(20)
                    
                start_ms = int(cur_start * 1000)
                full_dub = full_dub.overlay(clip, position=start_ms)
            except Exception as e:
                print(f"[TimingAligner] Error overlaying segment {seg.get('id')}: {e}")

        full_dub.export(full_dub_path, format="wav")
        return full_dub_path

    def mix_dub_with_bgm(self, dub_voice_path: str, bgm_path: str, output_path: str, bgm_volume: float = 0.0, voice_volume: float = 1.3) -> bool:
        """
        Hòa âm lồng tiếng mới:
        - Mặc định bgm_volume=0.0 để triệt tiêu 100% giọng gốc tránh bị echo/chồng tiếng
        - Giọng lồng tiếng mới rõ ràng, sắc nét (voice_volume=1.3)
        """
        if not os.path.exists(bgm_path) or os.path.getsize(bgm_path) == 0 or bgm_volume <= 0.01:
            cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                "-i", dub_voice_path,
                "-filter:a", f"volume={voice_volume:.2f}",
                "-acodec", "aac", "-b:a", "192k",
                output_path
            ]
            subprocess.run(cmd, capture_output=True)
            return True

        cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-i", dub_voice_path,
            "-i", bgm_path,
            "-filter_complex",
            f"[0:a]volume={voice_volume}[v];[1:a]volume={bgm_volume}[bg];[v][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "[aout]",
            "-acodec", "aac", "-b:a", "192k",
            output_path
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception as e:
            print(f"[TimingAligner] Mix error: {e}")
            subprocess.run(["ffmpeg", "-y", "-threads", "0", "-i", dub_voice_path, "-acodec", "aac", output_path], capture_output=True)
            return False

timing_aligner = TimingAligner()
