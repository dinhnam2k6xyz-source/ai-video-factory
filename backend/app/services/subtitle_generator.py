import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

class SubtitleGenerator:
    """
    VideoLingo & Video-Subtitle-Remover Hybrid Engine:
    - Smart Subtitle Masking (Làm mờ phụ đề gốc bằng Gaussian Blur gblur)
    - Netflix-Standard Subtitle Layout (Tự động ngắt 2 dòng cân đối, tối đa 38 ký tự/dòng)
    - Dynamic Karaoke Word-by-Word Animated Highlight (TikTok / Shorts 9:16)
    - Cinema Film Subtitles (Phụ đề điện ảnh tinh tế cho video 16:9)
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

    def format_cinema_lines(self, text: str, max_chars: int = 38) -> str:
        """
        VideoLingo Netflix Subtitle Splitter:
        Tự động ngắt dòng cân đối tại vị trí tự nhiên giữa câu nếu vượt quá max_chars
        """
        words = text.split()
        if len(text) <= max_chars or len(words) <= 5:
            return text

        mid = len(text) // 2
        best_split = len(words) // 2
        best_diff = float("inf")
        char_count = 0
        
        for i, w in enumerate(words[:-1]):
            char_count += len(w) + 1
            diff = abs(char_count - mid)
            if w.endswith((",", ".", "!", "?", ":", ";")):
                diff -= 5
            if diff < best_diff:
                best_diff = diff
                best_split = i + 1

        line1 = " ".join(words[:best_split])
        line2 = " ".join(words[best_split:])
        return f"{line1}\\N{line2}"

    def generate_ass_subtitles(
        self,
        segments: List[Dict[str, Any]],
        output_ass_path: str,
        is_vertical: bool = True,
        offset_start: float = 0.0,
        style_mode: str = "karaoke"  # "karaoke", "cinema", "bilingual"
    ) -> str:
        """
        Sinh file phụ đề .ASS chuẩn Netflix / VideoLingo
        """
        play_res_x = 1080 if is_vertical else 1920
        play_res_y = 1920 if is_vertical else 1080
        font_size = 38 if is_vertical else 26
        margin_v = 240 if is_vertical else 55
        font_name = "Segoe UI, Arial, Tahoma, sans-serif"

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

                chunk_size = 4 if is_vertical else 7
                chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
                total_duration = end - start
                chunk_dur = total_duration / len(chunks)

                for c_idx, chunk in enumerate(chunks):
                    c_start = start + c_idx * chunk_dur
                    c_end = c_start + chunk_dur
                    c_total_dur_cs = int(round((c_end - c_start) * 100))
                    
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
                formatted_trans = self.format_cinema_lines(trans_text, max_chars=36)
                bilingual_line = f"{formatted_trans}\\N{{\\rBilingualBottom}}{orig_text}"
                events.append(f"Dialogue: 0,{start_str},{end_str},BilingualTop,,0,0,0,,{bilingual_line}")

            # 3. Chế độ Cinema tiêu chuẩn (VideoLingo Netflix Subtitle Split)
            else:
                start_str = self.format_timestamp_ass(start)
                end_str = self.format_timestamp_ass(end)
                formatted_trans = self.format_cinema_lines(trans_text, max_chars=38)
                events.append(f"Dialogue: 0,{start_str},{end_str},CinemaStyle,,0,0,0,,{formatted_trans}")

        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(events) + "\n")

        return output_ass_path

    def burn_subtitles(
        self,
        video_path: str,
        ass_path: str,
        output_path: str,
        blur_original_subtitles: bool = True,
        crf: int = 21,
        preset: str = "ultrafast"
    ) -> bool:
        """
        Burn phụ đề ASS vào video kết hợp làm mờ phụ đề gốc (Gaussian Blur Mask):
        - Nếu blur_original_subtitles=True: Làm mờ vùng đáy 16% (chứa chữ Trung/Anh gốc) bằng gblur=sigma=14
          và đè phụ đề tiếng Việt đã dịch lên trên cực kỳ tinh tế, không để lộ chữ cũ.
        """
        if not os.path.exists(ass_path) or not os.path.exists(video_path):
            return False

        clean_ass = ass_path.replace("\\", "/").replace(":", "\\:")
        
        if blur_original_subtitles:
            # Làm mờ dải đáy 16% video (khu vực chứa phụ đề gốc)
            filter_complex = f"[0:v]split[base][sub];[sub]crop=in_w:in_h*0.16:0:in_h*0.82,gblur=sigma=14[blurred];[base][blurred]overlay=0:main_h*0.82,ass='{clean_ass}'[v_out]"
            cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                "-i", str(video_path),
                "-filter_complex", filter_complex,
                "-map", "[v_out]",
                "-map", "0:a?",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", str(preset),
                "-crf", str(crf),
                "-c:a", "copy",
                "-movflags", "+faststart",
                str(output_path)
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                "-i", str(video_path),
                "-vf", f"ass='{clean_ass}'",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", str(preset),
                "-crf", str(crf),
                "-c:a", "copy",
                "-movflags", "+faststart",
                str(output_path)
            ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except Exception as e:
            print(f"[SubtitleGenerator] Burn with blur error: {e}, falling back...")
            try:
                fallback_cmd = [
                    "ffmpeg", "-y",
                    "-threads", "0",
                    "-i", str(video_path),
                    "-vf", f"ass='{clean_ass}'",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-preset", "ultrafast",
                    "-crf", "22",
                    "-c:a", "copy",
                    "-movflags", "+faststart",
                    str(output_path)
                ]
                subprocess.run(fallback_cmd, capture_output=True, check=True)
                return True
            except Exception:
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

subtitle_generator = SubtitleGenerator()
