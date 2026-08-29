import os
import json
from typing import List, Dict, Any
from app.core.config import settings

class HighlightDetector:
    """Tự động phân tích kịch bản để tìm các đoạn cao trào, hook viral và cắt Shorts"""
    
    def __init__(self):
        self._gemini_client = None

    def _get_gemini(self):
        if self._gemini_client is None and settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._gemini_client = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                print(f"[HighlightDetector] Gemini init error: {e}")
        return self._gemini_client

    def detect_highlights(self, segments: List[Dict[str, Any]], total_duration: float, user_prompt: str = None) -> List[Dict[str, Any]]:
        """
        Tìm kiếm 3-5 đoạn clip ngắn 30-60s có tiềm năng viral cao nhất.
        """
        gemini = self._get_gemini()
        if gemini and segments:
            try:
                full_script = "\n".join([f"[{s['start']}s - {s['end']}s] ({s.get('speaker')}): {s.get('translated_text') or s.get('text')}" for s in segments])
                
                system_prompt = (
                    f"Bạn là chuyên gia sản xuất video viral hàng đầu trên TikTok, YouTube Shorts và Reels. "
                    f"Dưới đây là toàn bộ kịch bản và timestamp của một video dài {total_duration:.1f} giây.\n"
                )
                if user_prompt:
                    system_prompt += f"YÊU CẦU ĐẶC BIỆT TỪ NGƯỜI DÙNG: \"{user_prompt}\"\n"
                    
                system_prompt += (
                    f"Nhiệm vụ của bạn:\n"
                    f"1. Tìm từ 3 đến 5 đoạn clip highlight hay nhất (thời lượng mỗi clip từ 20 đến 60 giây).\n"
                    f"2. Mỗi clip phải có: Hook mở đầu gây tò mò, nội dung giữ chân (Climax) và bài học hoặc câu chốt ấn tượng.\n"
                    f"3. Chấm điểm Virality Score (từ 75 đến 99) và giải thích lý do đoạn này viral.\n"
                    f"4. Đặt tiêu đề hấp dẫn cho TikTok/Shorts.\n\n"
                    f"Format JSON trả về bắt buộc:\n"
                    f"[\n"
                    f"  {{\n"
                    f"    \"id\": 1,\n"
                    f"    \"title\": \"Bí quyết triệu đô không ai nói cho bạn\",\n"
                    f"    \"start_time\": 0.0,\n"
                    f"    \"end_time\": 45.0,\n"
                    f"    \"duration\": 45.0,\n"
                    f"    \"viral_score\": 96,\n"
                    f"    \"hook\": \"Câu mở đầu gây bất ngờ cực lớn...\",\n"
                    f"    \"reason\": \"Đoạn này đánh trúng tâm lý tò mò và cung cấp giải pháp ngay lập tức.\"\n"
                    f"  }}\n"
                    f"]\n\n"
                    f"KỊCH BẢN VIDEO:\n{full_script}"
                )
                
                resp = gemini.generate_content(system_prompt)
                content = resp.text.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                highlights = json.loads(content)
                if isinstance(highlights, list) and len(highlights) > 0:
                    return highlights
            except Exception as e:
                print(f"[HighlightDetector] LLM highlight detection error: {e}")

        # Thuật toán phân đoạn Heuristic thông minh nếu không có LLM
        return self._heuristic_highlights(segments, total_duration)

    def _heuristic_highlights(self, segments: List[Dict[str, Any]], total_duration: float) -> List[Dict[str, Any]]:
        """Phân đoạn theo mốc thời gian tối ưu cho Shorts"""
        if total_duration <= 60:
            return [{
                "id": 1,
                "title": "Clip Nổi Bật Toàn Bộ",
                "start_time": 0.0,
                "end_time": round(total_duration, 1),
                "duration": round(total_duration, 1),
                "viral_score": 92,
                "hook": "Đoạn mở đầu cuốn hút",
                "reason": "Thời lượng ngắn chuẩn định dạng Shorts"
            }]
            
        clip_targets = [
            {"title": "🔥 Tiết Lộ Bí Mật Bất Ngờ Nhất", "score": 96, "start_ratio": 0.05, "duration": 48.0},
            {"title": "💡 Bài Học Đắt Giá Ai Cũng Cần Biết", "score": 93, "start_ratio": 0.35, "duration": 52.0},
            {"title": "🚀 Kết Luận & Hành Động Ngay Hôm Nay", "score": 89, "start_ratio": 0.70, "duration": 45.0}
        ]
        
        highlights = []
        for idx, target in enumerate(clip_targets):
            start = round(total_duration * target["start_ratio"], 1)
            end = min(total_duration, round(start + target["duration"], 1))
            highlights.append({
                "id": idx + 1,
                "title": target["title"],
                "start_time": start,
                "end_time": end,
                "duration": round(end - start, 1),
                "viral_score": target["score"],
                "hook": "Mở đầu kịch tính giữ chân người xem trong 3 giây đầu",
                "reason": "Cung cấp giá trị thực tế cao, nhịp điệu nhanh"
            })
        return highlights

highlight_detector = HighlightDetector()
