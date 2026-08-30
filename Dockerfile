# =========================================================
# Multi-Stage Dockerfile for AI Video Factory (24/7 Cloud)
# Tương thích 100%: Hugging Face Spaces (Port 7860), Railway, Render, Koyeb, VPS
# =========================================================

# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /build
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python 3.11 Backend with Full FFmpeg & AI Models
FROM python:3.11-slim

# Cài đặt FFmpeg và các thư viện xử lý media
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cài đặt các gói Python
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy source code backend và frontend đã build
COPY backend /app/backend
COPY --from=frontend-builder /build/dist /app/frontend/dist

# Cấu hình biến môi trường
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Tạo các thư mục lưu trữ cần thiết
RUN mkdir -p /app/backend/storage/uploads /app/backend/storage/outputs /app/backend/storage/temp /app/backend/storage/models

WORKDIR /app/backend

# Mở port mặc định của Hugging Face Spaces (7860) & Cloud
EXPOSE 7860

# Chạy Uvicorn Web Server
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
