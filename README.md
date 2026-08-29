# 🎬 AI VIDEO FACTORY
### Nền Tảng Tự Động Hóa Sản Xuất Video Bằng AI: Lồng Tiếng Đa Vai + Auto Shorts 9:16 + 10x Content Multiplier

---

## 🌟 Tính Năng Nổi Bật

1. **Phân Tách & Bóc Phụ Đề Đa Nhân Vật (Whisper + Diarization)**
   - Tự động tách dải âm thanh giọng nói (Vocals) và Nhạc nền (BGM) để giữ nguyên âm hưởng gốc.
   - Trích xuất phụ đề chi tiết từng từ (Word-level timestamps).
   - Nhận diện và phân biệt từng người nói (Speaker 1, Speaker 2,...).

2. **Dịch Thuật & AI Lồng Tiếng Đa Vai (Smart Multi-Voice Dubbing)**
   - Dịch thuật ngữ cảnh thông minh, đo đếm số lượng từ/âm tiết để tương thích với thời lượng nói gốc.
   - Lồng tiếng Việt chất lượng cao bằng `edge-tts` (Hoài My - Nữ truyền cảm, Nam Minh - Nam trầm ấm).
   - Cho phép nghe thử (Preview) giọng đọc trực tiếp trên giao diện.

3. **Thuật Toán Căn Timing Tự Động (Pacing Sync & Ducking)**
   - Tự động co giãn tốc độ audio bằng FFmpeg `atempo` / `rubberband` trong khoảng an toàn (0.75x - 1.35x) không làm đổi cao độ.
   - Tự động hạ âm lượng BGM (Audio Ducking) khi nhân vật nói và đẩy âm lượng BGM lên ở các đoạn chuyển cảnh.

4. **Tự Tạo Shorts / TikTok / Reels 9:16 (Auto Highlights & Smart Crop)**
   - Tự động phân tích kịch bản tìm các đoạn cao trào (Hook 3s đầu, Climax, Virality Score).
   - OpenCV Face-Tracking: Tự động theo dõi khuôn mặt người nói và crop khung hình 9:16 vào giữa khung hình mượt mà.
   - Phụ đề động Karaoke (.ass): Kiểu chữ to in hoa, viền đen, hiệu ứng đổi màu vàng/xanh neon chuẩn phong cách CapCut & MrBeast.

5. **1 Video → 10 Content Multiplier**
   - 10 Tiêu đề Video tối ưu CTR (gây tò mò, đặt câu hỏi, hướng dẫn, bí quyết).
   - 10 Đoạn Caption ngắn cho TikTok / Shorts / Reels.
   - 30 Hashtags phân loại theo xu hướng.
   - Ý tưởng thiết kế Thumbnail (Headline chữ to + Mô tả hình ảnh trực quan).
   - Bài viết tóm tắt Blog / Facebook hoàn chỉnh chuẩn SEO.

6. **AI Content Generator Command Bar**
   - Nhập câu lệnh tùy biến bằng ngôn ngữ tự nhiên (VD: *"Biến video này thành 5 clip TikTok hài hước"*, *"Dịch và lồng tiếng sang tiếng Việt"*).

7. **Hệ Thống Quản Lý Credit & Gói Cước SaaS**
   - Sẵn sàng mô hình kiếm tiền với các gói: **FREE** (3 video/tháng), **PRO 99K** (60 phút), **PRO+ 199K** (180 phút), **BUSINESS 499K** (600 phút, batch API).

---

## 🚀 Hướng Dẫn Sử Dụng

### Cách 1: Khởi chạy nhanh bằng 1 click
Nhấp đúp chuột vào file:
```
start.bat
```
Hệ thống sẽ tự động:
1. Chạy Backend FastAPI tại `http://localhost:8000`
2. Chạy Frontend Studio tại `http://localhost:5173`
3. Tự động mở trình duyệt web.

### Cách 2: Chạy thủ công bằng dòng lệnh

**1. Khởi chạy Backend:**
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**2. Khởi chạy Frontend:**
```bash
cd frontend
npm run dev
```

---

## 🏗️ Cấu Trúc Mã Nguồn

```
ai-video-factory/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes_video.py        # Upload, URL download (yt-dlp), lấy tiến trình
│   │   │   ├── routes_voices.py       # Danh sách giọng & nghe thử preview
│   │   │   └── routes_credits.py      # Quản lý số dư credit & gói cước
│   │   ├── services/
│   │   │   ├── audio_extractor.py     # Tách Vocals & BGM bằng FFmpeg/Demucs
│   │   │   ├── transcriber.py         # Whisper ASR & Word timestamps
│   │   │   ├── diarizer.py            # Nhận diện Speaker 1, Speaker 2,...
│   │   │   ├── translator.py          # Dịch thông minh giữ độ dài câu
│   │   │   ├── tts_engine.py          # Edge-TTS sinh giọng Việt tự nhiên
│   │   │   ├── timing_aligner.py      # Co giãn tốc độ atempo & Audio Ducking
│   │   │   ├── highlight_detector.py  # Chấm điểm Viral Score & chọn clip
│   │   │   ├── smart_cropper.py       # OpenCV Face Tracking 9:16
│   │   │   ├── subtitle_generator.py  # Tạo file .ass phụ đề Karaoke động
│   │   │   ├── content_generator.py   # 1 Video -> 10 Content
│   │   │   └── pipeline.py            # Master Orchestrator toàn bộ luồng
│   │   ├── core/
│   │   │   ├── config.py              # Cấu hình storage, API keys, port
│   │   │   └── credit_manager.py      # Quản lý gói cước & trừ credit
│   │   └── main.py                    # Khởi tạo FastAPI Server
│   └── test_pipeline.py               # Script test tích hợp end-to-end
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx             # Thanh điều hướng, số dư credit & tier
│   │   │   ├── Dropzone.tsx           # Upload kéo thả, URL input & prompt bar
│   │   │   ├── PipelineProgress.tsx   # Thanh tiến trình real-time các bước
│   │   │   ├── DubbingStudio.tsx      # Nghe thử giọng, chỉnh transcript & tải video
│   │   │   ├── ShortsGallery.tsx      # Xem trước Shorts 9:16 & Virality Score
│   │   │   ├── ContentMultiplier.tsx  # Copy 10 tiêu đề, caption, hashtag, thumbnail
│   │   │   └── PricingModal.tsx       # Bảng giá Free / Pro / Business
│   │   ├── App.tsx
│   │   └── main.tsx
└── start.bat                          # File khởi chạy 1-click
```
