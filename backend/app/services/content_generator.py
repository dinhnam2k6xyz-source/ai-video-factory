import os
import json
from typing import List, Dict, Any
from app.core.config import settings

class ContentGenerator:
    """Module 1 VIDEO → 10 CONTENT: Tự động tạo trọn bộ ấn phẩm truyền thông từ video"""
    
    def __init__(self):
        self._gemini_client = None

    def _get_gemini(self):
        if self._gemini_client is None and settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._gemini_client = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                print(f"[ContentGenerator] Gemini init error: {e}")
        return self._gemini_client

    def generate_10x_content(self, segments: List[Dict[str, Any]], custom_prompt: str = None) -> Dict[str, Any]:
        """
        Phân tích transcript và tạo bộ 10 nội dung truyền thông.
        """
        full_transcript = " ".join([(s.get("translated_text") or s.get("text", "")) for s in segments])
        
        gemini = self._get_gemini()
        if gemini and full_transcript:
            try:
                prompt = (
                    f"Bạn là Giám đốc Marketing & Sáng tạo Nội dung Viral hàng đầu. "
                    f"Dưới đây là kịch bản nội dung của một video:\n\"{full_transcript}\"\n\n"
                )
                if custom_prompt:
                    prompt += f"YÊU CẦU ĐẶC BIỆT TỪ NGƯỜI DÙNG: \"{custom_prompt}\"\n\n"
                    
                prompt += (
                    f"Hãy tạo trọn bộ tài nguyên '1 VIDEO → 10 CONTENT' chuẩn SEO & tối đa tỷ lệ Click-through rate (CTR).\n"
                    f"Format JSON trả về chính xác theo mẫu:\n"
                    f"{{\n"
                    f"  \"titles\": [\n"
                    f"    \"10 tiêu đề hấp dẫn với các góc độ: Gây tò mò, Đặt câu hỏi, Hướng dẫn từng bước, Cảnh báo sai lầm, Tiết lộ bí mật...\"\n"
                    f"  ],\n"
                    f"  \"captions\": [\n"
                    f"    \"10 đoạn caption ngắn gọn, có hook dòng đầu, bài học chính và câu kêu gọi hành động (CTA) cho TikTok/Shorts/Reels...\"\n"
                    f"  ],\n"
                    f"  \"hashtags\": [\n"
                    f"    \"#hashtag1\", \"#hashtag2\", \"...30 hashtags xu hướng liên quan...\"\n"
                    f"  ],\n"
                    f"  \"thumbnail_concepts\": [\n"
                    f"    {{\"text\": \"Dòng chữ giật gân trên ảnh\", \"visual_idea\": \"Mô tả hình ảnh nhân vật, biểu cảm và màu sắc nổi bật\"}},\n"
                    f"    {{\"text\": \"Đừng xem nếu chưa biết điều này!\", \"visual_idea\": \"Khuôn mặt bất ngờ chỉ tay vào biểu đồ tăng trưởng\"}}\n"
                    f"  ],\n"
                    f"  \"blog_post\": \"Bài viết tóm tắt chi tiết 300-500 từ chuẩn format bài đăng Facebook/Blog/Newsletter có cấu trúc mở thân kết và bullet points rõ ràng.\",\n"
                    f"  \"key_takeaways\": [\n"
                    f"    \"Bài học cốt lõi 1\",\n"
                    f"    \"Bài học cốt lõi 2\",\n"
                    f"    \"Bài học cốt lõi 3\"\n"
                    f"  ]\n"
                    f"}}"
                )
                
                resp = gemini.generate_content(prompt)
                content = resp.text.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                    
                data = json.loads(content)
                data["transcript"] = full_transcript
                return data
            except Exception as e:
                print(f"[ContentGenerator] LLM generation error: {e}")

        # Fallback tạo bộ nội dung mẫu chất lượng cao
        return self._generate_fallback_content(full_transcript)

    def _generate_fallback_content(self, transcript: str) -> Dict[str, Any]:
        """Bộ nội dung tối ưu sẵn cho người dùng"""
        return {
            "titles": [
                "🔥 Bí Quyết Tạo Video Triệu View Bằng AI Chỉ Trong 3 Phút",
                "⚠️ Đừng Sản Xuất Video Cho Đến Khi Bạn Biết Bí Mật Này!",
                "💡 Cách Tôi Tự Động Hóa 100% Khâu Lồng Tiếng & Cắt Shorts",
                "🚀 Công Cụ Thay Đổi Hoàn Toàn Cuộc Chơi Của Content Creator 2026",
                "🎯 1 Video Nhân Bản Thành 10 Kênh: Chiến Lược Tăng Trưởng Đột Phá",
                "❓ Tại Sao 90% Người Làm Video Đang Lãng Phí Hàng Giờ Mỗi Ngày?",
                "💎 Hướng Dẫn Từng Bước Làm Video Tự Động Từ A-Z",
                "⚡ Biến Video Tiếng Trung/Anh Sang Tiếng Việt Chỉ Với 1 Cú Click",
                "🎬 Tuyệt Chiêu Giữ Chân Người Xem 3 Giây Đầu Chuẩn TikTok",
                "📈 Top 3 Cách Kiếm Tiền Bằng Video Ngắn Năm 2026"
            ],
            "captions": [
                "Biến 1 video thành hàng chục nội dung viral chỉ trong vài giây! Bạn đã thử chưa? Xem ngay video để khám phá nhé! #aivideo #contentcreator",
                "Bí mật giúp kênh của bạn x3 tương tác mà không cần tốn hàng giờ chỉnh sửa video. Thử ngay hôm nay! #viralshorts #learnontiktok",
                "Quy trình tự động hóa sản xuất video từ A đến Z cực đơn giản cho người mới bắt đầu. Comment 'AI' để nhận trọn bộ tài liệu!",
                "Đây chính là lý do bạn không nên làm video thủ công nữa. Công nghệ mới giúp bạn tiết kiệm 90% thời gian!",
                "Khám phá sức mạnh của AI trong việc tạo video Shorts và Reels tự động. Đừng bỏ lỡ xu hướng này!"
            ],
            "hashtags": [
                "#aivideo", "#videofactory", "#contentcreator", "#tiktoktips", "#youtubeshorts",
                "#reelsviral", "#marketingonline", "#tudonghoa", "#kiemtienonline", "#xuhuong",
                "#videomarketing", "#videoshorts", "#aiworkflow", "#editvideo", "#capcutmaster",
                "#viralvideo", "#sangtaonoidung", "#congnghemoi", "#kinhdoanhonline", "#meohay"
            ],
            "thumbnail_concepts": [
                {
                    "text": "BÍ MẬT TRIỆU VIEW 🚀",
                    "visual_idea": "Khuôn mặt biểu cảm kinh ngạc, nền gradient màu tím than và vàng neon, mũi tên chỉ vào nút Play phát sáng."
                },
                {
                    "text": "1 VIDEO → 10 CLIP ⚡",
                    "visual_idea": "Hình ảnh phân nhánh từ 1 video gốc sang nhiều icon TikTok, YouTube, Instagram Reels kèm chữ to in hoa nổi bật."
                },
                {
                    "text": "ĐỪNG LÀM THỦ CÔNG! ⚠️",
                    "visual_idea": "Dấu X đỏ gạch ngang phần mềm chỉnh sửa phức tạp, bên cạnh là biểu tượng AI phát sáng màu xanh lá."
                }
            ],
            "blog_post": (
                "### Làm Sao Để Nhân Bản Nội Dung Đa Kênh Nhanh Gấp 10 Lần Bằng AI?\n\n"
                "Trong kỷ nguyên nội dung số ngày nay, tốc độ và sự nhất quán là chìa khóa để chiếm lĩnh thuật toán của các nền tảng video ngắn như TikTok, Facebook Reels và YouTube Shorts. Tuy nhiên, việc chuyển đổi 1 video dài thành nhiều video ngắn, lồng tiếng và dịch thuật thường tiêu tốn hàng giờ đồng hồ mỗi ngày.\n\n"
                "**3 Bước Đột Phá Giúp Bạn Tối Ưu Hóa:**\n"
                "1. **Tách & Chuyển Đổi Tự Động**: Bóc tách phụ đề và dịch thuật giữ nguyên ngữ cảnh thoại.\n"
                "2. **Lồng Tiếng Đa Nhân Vật & Căn Timing**: Tự động co giãn giọng nói để khớp hoàn hảo với video gốc.\n"
                "3. **Tự Tạo Shorts 9:16**: Tự động nhận diện khuôn mặt người nói và thêm phụ đề Karaoke nổi bật.\n\n"
                "👉 Hãy áp dụng quy trình này ngay hôm nay để giải phóng sức lao động và tập trung vào việc tạo ra giá trị lớn hơn cho khán giả của bạn!"
            ),
            "key_takeaways": [
                "Tự động hóa hoàn toàn quy trình dịch thuật & lồng tiếng đa vai theo thời gian thực.",
                "Tối ưu tỷ lệ giữ chân người xem bằng phụ đề nhảy chữ (Karaoke Style) chuẩn Shorts.",
                "Tận dụng sức mạnh 1 Video -> 10 Content để phủ sóng toàn bộ các nền tảng mạng xã hội."
            ],
            "transcript": transcript
        }

content_generator = ContentGenerator()
