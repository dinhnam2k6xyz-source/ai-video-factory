import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

class SubtitleGenerator:
    """
    Công cụ tạo và chèn phụ đề chuyên nghiệp vào video (In-video Subtitle Burning):
    - Karaoke Word-by-word Highlight (Chuẩn phong cách CapCut / MrBeast / TikTok Shorts)
    - Phụ đề điện ảnh Cinema Subtitles (Chuẩn Netflix / YouTube 16:9)
    - Phụ đề Song Ngữ (Bilingual Subtitles)
    - Xuất file SRT / TXT / ASS / VTT tương thích mọi phần mềm dựng phim
    """

    def format_timestamp_ass(self, seconds: float) -> str:
        """Format timestamp cho file ASS: H:MM:SS.cs"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        cs = int(round((seconds - int(seconds)) * 100))
        if cs >= 100:
            cs = 99
        return f"{hrs}:{mins:02d}:{secs:02d}.{cs:02d}"

    def format_timestamp_srt(self, seconds: float) -> str:
        """Format timestamp cho file SRT: HH:MM:SS,mmm"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        msecs = int(round((seconds - int(seconds)) * 1000))
        if msecs >= 1000:
            msecs = 999
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"

    def format_timestamp_txt(self, seconds: float) -> str:
        """Format timestamp cho file TXT: [MM:SS]"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"[{mins:02d}:{secs:02d}]"

    def clean_text(self, text: str) -> str:
        """Làm sạch ký tự đặc biệt có thể gây lỗi cú pháp ASS/FFmpeg"""
        if not text:
            return ""
        t = text.replace("{", "(").replace("}", ")").replace("\\", "/")
        return re.sub(r'\s+', ' ', t).strip()

    def generate_ass_subtitles(
        self,
        segments: List[Dict[str, Any]],
        output_ass_path: str,
        is_vertical: bool = True,
        offset_start: float = 0.0,
        style_mode: str = "karaoke"  # "karaoke", "cinema", "bilingual"
    ) -> str:
        """
        Sinh file phụ đề .ASS với hiệu ứng động Karaoke đổi màu từng từ theo thời gian nói:
        - is_vertical = True: Tối ưu 9:16 (MarginV lớn tránh che bởi UI TikTok, font to, chữ hoa)
        - is_vertical = False: Tối ưu 16:9 (Phụ đề điện ảnh, viền thanh thoát, cân đối khung hình)
        """
        play_res_x = 1080 if is_vertical else 1920
        play_res_y = 1920 if is_vertical else 1080
        font_size = 38 if is_vertical else 26
        margin_v = 240 if is_vertical else 55  # Tránh vùng icon TikTok ở góc dưới
        font_name = "Segoe UI, Arial, Tahoma, sans-serif"

        # ASS Header với các Style định nghĩa sẵn
        ass_header = f"""[Script Info]
Title: AI Video Factory Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TikTokKaraoke,{font_name},{font_size},&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4.0,2.0,2,30,30,{margin_v},1
Style: CinemaStyle,{font_name},{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2.5,1.5,2,40,40,{margin_v},1
Style: BilingualTop,{font_name},{font_size},&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.0,1.5,2,30,30,{margin_v + 35},1
Style: BilingualBottom,{font_name},{int(font_size * 0.75)},&H00E0E0E0,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2.0,1.0,2,30,30,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for seg in segments:
            raw_start = float(seg.get("start", 0))
            raw_end = float(seg.get("end", 0))
            
            start = max(0.0, raw_start - float(offset_start))
            end = max(start + 0.3, raw_end - float(offset_start))
            if end <= start:
                continue

            trans_text = self.clean_text(seg.get("translated_text") or seg.get("text", ""))
            orig_text = self.clean_text(seg.get("original_text") or seg.get("text", ""))

            if not trans_text:
                continue

            # 1. Chế độ Karaoke cho Shorts / TikTok (Word-by-word animated highlight)
            if style_mode == "karaoke" or is_vertical:
                words = trans_text.upper().split()
                if not words:
                    continue

                # Chia câu thành các cụm 3-5 từ để hiển thị đẹp mắt không tràn viền
                chunk_size = 4 if is_vertical else 7
                chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
                total_duration = end - start
                chunk_dur = total_duration / len(chunks)

                for c_idx, chunk in enumerate(chunks):
                    c_start = start + c_idx * chunk_dur
                    c_end = c_start + chunk_dur
                    c_total_dur_cs = int(round((c_end - c_start) * 100))
                    
                    # Tính thời lượng từng từ (centiseconds) tỷ lệ theo độ dài từ
                    word_lens = [max(1, len(w)) for w in chunk]
                    total_lens = sum(word_lens)
                    
                    karaoke_parts = []
                    allocated_cs = 0
                    for w_idx, w in enumerate(chunk):
                        if w_idx == len(chunk) - 1:
                            w_dur_cs = max(10, c_total_dur_cs - allocated_cs)
                        else:
                            w_dur_cs = max(10, int(round((word_lens[w_idx] / total_lens) * c_total_dur_cs)))
                            allocated_cs += w_dur_cs
                        karaoke_parts.append(f"{{\\k{w_dur_cs}}}{w}")

                    karaoke_text = " ".join(karaoke_parts)
                    start_str = self.format_timestamp_ass(c_start)
                    end_str = self.format_timestamp_ass(c_end)
                    events.append(f"Dialogue: 0,{start_str},{end_str},TikTokKaraoke,,0,0,0,,{karaoke_text}")

            # 2. Chế độ Song Ngữ (Bilingual)
            elif style_mode == "bilingual":
                start_str = self.format_timestamp_ass(start)
                end_str = self.format_timestamp_ass(end)
                bilingual_line = f"{trans_text}\\N{{\\rBilingualBottom}}{orig_text}"
                events.append(f"Dialogue: 0,{start_str},{end_str},BilingualTop,,0,0,0,,{bilingual_line}")

            # 3. Chế độ Cinema tiêu chuẩn (Phụ đề Video 16:9)
            else:
                start_str = self.format_timestamp_ass(start)
                end_str = self.format_timestamp_ass(end)
                events.append(f"Dialogue: 0,{start_str},{end_str},CinemaStyle,,0,0,0,,{trans_text}")

        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(events) + "\n")

        return output_ass_path

    def burn_subtitles(
        self,
        video_path: str,
        ass_path: str,
        output_path: str,
        crf: int = 20,
        preset: str = "ultrafast"
    ) -> bool:
        """
        Burn cứng phụ đề ASS vào video bằng FFmpeg:
        - Tự động chuẩn hóa đường dẫn trên Windows để tránh lỗi libass path escape
        - Sử dụng ultrafast preset và tối đa CPU threads để render trong vài giây
        """
        if not os.path.exists(ass_path) or not os.path.exists(video_path):
            print(f"[SubtitleGenerator] File không tồn tại: video={video_path}, ass={ass_path}")
            return False

        # Chuẩn hóa path cho FFmpeg filter trên Windows: thay \ thành / và escape dấu :
        clean_ass = ass_path.replace("\\", "/").replace(":", "\\:")
        
        cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-i", str(video_path),
            "-vf", f"ass='{clean_ass}'",
            "-c:v", "libx264",
            "-preset", str(preset),
            "-crf", str(crf),
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(output_path)
        ]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"[SubtitleGenerator] FFmpeg ASS Filter Error: {e.stderr}")
            # Fallback nếu libass gặp lỗi font: dùng subtitles filter
            try:
                fallback_cmd = [
                    "ffmpeg", "-y",
                    "-threads", "0",
                    "-i", str(video_path),
                    "-vf", f"subtitles='{clean_ass}'",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "22",
                    "-c:a", "copy",
                    "-movflags", "+faststart",
                    str(output_path)
                ]
                subprocess.run(fallback_cmd, capture_output=True, check=True)
                return True
            except Exception as e2:
                print(f"[SubtitleGenerator] Fallback subtitle burn failed: {e2}")
                return False

    def generate_srt(
        self,
        segments: List[Dict[str, Any]],
        output_srt_path: str,
        mode: str = "translated"  # "translated", "original", "bilingual"
    ) -> str:
        """Xuất file phụ đề chuẩn .SRT tương thích YouTube, Premiere, CapCut, DaVinci"""
        lines = []
        idx = 1

        for seg in segments:
            start = float(seg.get("start", 0))
            end = float(seg.get("end", 0))
            if end <= start:
                end = start + 1.0

            trans_text = (seg.get("translated_text") or seg.get("text", "")).strip()
            orig_text = (seg.get("original_text") or seg.get("text", "")).strip()

            if mode == "translated":
                content = trans_text
            elif mode == "original":
                content = orig_text
            else:
                content = f"{trans_text}\n{orig_text}"

            if not content:
                continue

            lines.append(str(idx))
            lines.append(f"{self.format_timestamp_srt(start)} --> {self.format_timestamp_srt(end)}")
            lines.append(content)
            lines.append("")
            idx += 1

        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return output_srt_path

    def generate_txt(
        self,
        segments: List[Dict[str, Any]],
        output_txt_path: str,
        mode: str = "translated"
    ) -> str:
        """Xuất file văn bản lời thoại .TXT hoàn chỉnh kèm mốc thời gian"""
        lines = []
        for seg in segments:
            start = float(seg.get("start", 0))
            spk = seg.get("speaker", "Speaker 1")
            
            if mode == "translated":
                text = (seg.get("translated_text") or seg.get("text", "")).strip()
            elif mode == "original":
                text = (seg.get("original_text") or seg.get("text", "")).strip()
            else:
                t1 = (seg.get("translated_text") or seg.get("text", "")).strip()
                t2 = (seg.get("original_text") or seg.get("text", "")).strip()
                text = f"{t1} ({t2})"

            if text:
                time_tag = self.format_timestamp_txt(start)
                lines.append(f"{time_tag} [{spk}]: {text}")

        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return output_txt_path
