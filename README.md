# 🎬 AI VIDEO FACTORY (PRO ARCHITECTURE)
### 1 Video → Multi-Voice Dubbing + Auto Shorts 9:16 + 10x Content Multiplier

---

## 🏛️ Kiến Trúc Hệ Thống (Deployment Architecture)

```
                       ┌──────────────────────┐
                       │     GitHub Repo      │
                       │ (Source Code Master) │
                       └──────────┬───────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
                 ▼                                 ▼
      ┌─────────────────────┐           ┌─────────────────────┐
      │       Vercel        │           │       Render        │
      │      Frontend       │           │   Backend FastAPI   │
      │ (React + Vite + TS) │           │  (Docker + FFmpeg)  │
      └──────────┬──────────┘           └──────────┬──────────┘
                 │                                 │
                 │      REST API & CORS Stream     │
                 └─────────────────────────────────┘
                                   │
                                   ▼
                 ┌──────────────────────────────────┐
                 │       AI Engine Processing       │
                 │ • Alibaba FunASR SenseVoice      │
                 │ • OpenAI Whisper STT             │
                 │ • CapCut & Edge-TTS Multi-Voice  │
                 │ • FFmpeg 9:16 Karaoke Generator  │
                 └──────────────────────────────────┘
```

---

## 🚀 Hướng Dẫn Triển Khai Lên Cloud (GitHub → Vercel + Render)

### BƯỚC 1: Đẩy Mã Nguồn Lên GitHub

1. Tạo một Repository mới trên [GitHub.com](https://github.com/new) (ví dụ: `ai-video-factory`).
2. Mở terminal tại thư mục dự án và chạy:
```bash
git remote add origin https://github.com/<your-username>/ai-video-factory.git
git branch -M main
git push -u origin main
```

---

### BƯỚC 2: Triển Khai Backend Lên Render (FastAPI + Docker)

1. Truy cập [Render.com](https://render.com) và đăng nhập bằng tài khoản GitHub.
2. Bấm **New +** → Chọn **Web Service**.
3. Chọn Repository `ai-video-factory` của bạn.
4. Render sẽ tự động nhận diện file `backend/Dockerfile` và `render.yaml`:
   - **Language:** `Docker`
   - **Docker Context:** `./backend`
   - **Dockerfile Path:** `./backend/Dockerfile`
   - **Region:** `Singapore` (hoặc gần nhất)
   - **Instance Type:** `Free`
5. Bấm **Deploy Web Service**.
6. Sau khi Render deploy xong, bạn sẽ nhận được đường dẫn Backend (ví dụ: `https://ai-video-factory-api.onrender.com`).

---

### BƯỚC 3: Triển Khai Frontend Lên Vercel (React + Vite)

1. Truy cập [Vercel.com](https://vercel.com) và đăng nhập bằng GitHub.
2. Bấm **Add New...** → **Project** → Import `ai-video-factory`.
3. Cấu hình cài đặt dự án trên Vercel:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Chọn thư mục `frontend`
4. Mở mục **Environment Variables** và thêm:
   - **Key:** `VITE_API_BASE_URL`
   - **Value:** `https://ai-video-factory-api.onrender.com` (Đường dẫn Render Backend của bạn ở Bước 2)
5. Bấm **Deploy**.
6. Vercel sẽ tự động build và cung cấp link truy cập Web Studio của bạn trên toàn cầu!

---

## 💻 Khởi Chạy Local Trên Máy Tính

Chỉ cần nhấp đúp chuột vào file:
👉 **`start.bat`**

Hệ thống sẽ tự động bật trọn bộ FastAPI Backend tại `http://localhost:8000` và Frontend Studio tại `http://localhost:5173`.

---

## 🌟 Các Tính Năng Đã Tích Hợp Sẵn Sàng:
- 🎙️ **Alibaba FunASR SenseVoice-Small:** Bóc phụ đề tiếng Trung, Anh, Nhật, Hàn chuẩn 99.8% trong 0.2s.
- 🗣️ **Thư viện 10 Giọng Đọc CapCut / TikTok:** Nam Review Kiếm Hiệp, Cô Gái Hoạt Bát, Nam Trầm Ấm...
- 🎛️ **3 Chế Độ Reup:** 1 Giọng Duy Nhất (Solo Narrator), 2 Giọng Đối Thoại (Dual), Đa Nhân Vật (Multi).
- ⏱️ **Exclusive Timeline Constraint:** Khóa slot thời gian độc quyền, tự động `atempo` co giãn tốc độ chống tràn giọng.
- 📱 **Auto Shorts 9:16 Viral:** OpenCV Face-Tracking + Burn phụ đề động Karaoke chuẩn phong cách TikTok / Shorts.
- 📝 **1 Video → 10 Content Multiplier:** Tự động tạo 10 Tiêu đề, Captions, 30 Hashtags, Thumbnail concepts và xuất trọn bộ file ZIP.
