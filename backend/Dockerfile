FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Cài đặt FFmpeg và các thư viện hệ thống cần thiết cho audio/video AI
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Tạo cấu trúc thư mục lưu trữ
RUN mkdir -p storage/uploads storage/temp storage/outputs storage/models/sensevoice storage/models/piper

# Tải sẵn model Alibaba FunASR SenseVoice-Small ONNX
RUN python -c "import urllib.request, os; \
    os.makedirs('storage/models/sensevoice', exist_ok=True); \
    base = 'https://huggingface.co/csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/resolve/main/'; \
    urllib.request.urlretrieve(base + 'model.int8.onnx', 'storage/models/sensevoice/model.int8.onnx'); \
    urllib.request.urlretrieve(base + 'tokens.txt', 'storage/models/sensevoice/tokens.txt'); \
    print('SenseVoice model pre-installed!')"

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
