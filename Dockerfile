# Dockerfile for AI Video Factory (Backend + Frontend)
FROM python:3.11-slim

# Install system dependencies & FFmpeg with full codec support
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install python packages
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application source code
COPY . /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Run Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
