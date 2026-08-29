import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class SubtitleGenerator:
    """Tạo phụ đề động Karaoke dạng TikTok/CapCut và xuất file phụ đề SRT / TXT / ASS"""

    def format_timestamp_ass(self, seconds: float) -> str:
        """Format timestamp cho file ASS: H:MM:SS.cs"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        cs = int(round((seconds - int(seconds)) * 100))
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
            else: # bilingual
                content = f"{trans_text}\n{orig_text}"

            if not content:
                continue

            lines.append(str(idx))
            lines.append(f"{self.format_timestamp_srt(start)} --> {self.format_timestamp_srt(end)}")
            lines.append(content)
            lines.append("") # Empty line between entries
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
        """Xuất file văn bản lời thoại .TXT hoàn chỉnh"""
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

    def generate_ass_subtitles(
        self,
        segments: List[Dict[str, Any]],
        output_ass_path: str,
        is_vertical: bool = True,
        offset_start: float = 0.0
    ) -> str:
        """Sinh file phụ đề .ass với style chữ vàng/trắng nổi bật, viền đen dày, chuẩn TikTok"""
        font_size = 32 if is_vertical else 24
        margin_v = 180 if is_vertical else 50
        
        ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {'1080' if is_vertical else '1920'}
PlayResY: {'1920' if is_vertical else '1080'}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TikTokStyle,Montserrat Black,{font_size},&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,0,2,20,20,{margin_v},1
Style: TikTokWhite,Montserrat Black,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,0,2,20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for seg in segments:
            raw_start = float(seg.get("start", 0))
            raw_end = float(seg.get("end", 0))
            
            start = max(0.0, raw_start - float(offset_start))
            end = max(0.1, raw_end - float(offset_start))
            if end <= start:
                continue
                
            text = (seg.get("translated_text") or seg.get("text", "")).strip().upper()
            if not text:
                continue
                
            words = text.split()
            if len(words) <= 5:
                start_str = self.format_timestamp_ass(start)
                end_str = self.format_timestamp_ass(end)
                events.append(f"Dialogue: 0,{start_str},{end_str},TikTokStyle,,0,0,0,,{text}")
            else:
                chunk_size = 4
                chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
                chunk_dur = (end - start) / len(chunks)
                for c_idx, chunk in enumerate(chunks):
                    c_start = start + c_idx * chunk_dur
                    c_end = c_start + chunk_dur
                    c_text = " ".join(chunk)
                    start_str = self.format_timestamp_ass(c_start)
                    end_str = self.format_timestamp_ass(c_end)
                    style = "TikTokStyle" if c_idx % 2 == 0 else "TikTokWhite"
                    events.append(f"Dialogue: 0,{start_str},{end_str},{style},,0,0,0,,{c_text}")

        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(events) + "\n")
            
        return output_ass_path

    def burn_subtitles(self, video_path: str, ass_path: str, output_path: str) -> bool:
        """Burn cứng phụ đề vào video bằng FFmpeg ultrafast preset"""
        escaped_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")
        
        cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-i", video_path,
            "-vf", f"ass='{escaped_ass_path}'",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
            "-c:a", "copy",
            "-movflags", "+faststart",
            output_path
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception as e:
            print(f"[SubtitleGenerator] Burn subtitles failed: {e}")
            return False
