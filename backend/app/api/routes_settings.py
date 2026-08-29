from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from pathlib import Path

from app.core.config import settings

router = APIRouter()

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ollama_url: Optional[str] = None
    custom_tts_url: Optional[str] = None
    capcut_tts_url: Optional[str] = None

@router.get("/")
async def get_settings():
    """Lấy trạng thái cấu hình hiện tại"""
    return {
        "status": "success",
        "has_gemini_key": bool(settings.GEMINI_API_KEY),
        "gemini_key_masked": f"{settings.GEMINI_API_KEY[:4]}...{settings.GEMINI_API_KEY[-4:]}" if len(settings.GEMINI_API_KEY) > 8 else ("Đã cấu hình" if settings.GEMINI_API_KEY else "Chưa cấu hình (Đang dùng Free RPC 100%)"),
        "has_openai_key": bool(settings.OPENAI_API_KEY),
        "custom_tts_url": settings.CUSTOM_TTS_URL,
        "capcut_tts_url": settings.CAPCUT_TTS_URL,
        "free_mode_active": True,
        "free_services": {
            "stt": "OpenAI Whisper Local CPU/GPU (Miễn phí 100% vĩnh viễn)",
            "translator": "Chrome Ext & MyMemory Free RPC (Miễn phí 100% vĩnh viễn)",
            "tts": "Edge-TTS + CapCut Styles + viPiper Local (Miễn phí 100% vĩnh viễn)",
            "video_render": "FFmpeg & OpenCV Local (Miễn phí 100% vĩnh viễn)"
        }
    }

@router.post("/")
async def update_settings(req: SettingsUpdateRequest):
    """Cập nhật API Key hoặc URL kết nối"""
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    
    if req.gemini_api_key is not None:
        settings.GEMINI_API_KEY = req.gemini_api_key.strip()
    if req.openai_api_key is not None:
        settings.OPENAI_API_KEY = req.openai_api_key.strip()
    if req.custom_tts_url is not None:
        settings.CUSTOM_TTS_URL = req.custom_tts_url.strip()
    if req.capcut_tts_url is not None:
        settings.CAPCUT_TTS_URL = req.capcut_tts_url.strip()

    # Ghi vào file .env
    lines = []
    lines.append(f"GEMINI_API_KEY={settings.GEMINI_API_KEY}\n")
    lines.append(f"OPENAI_API_KEY={settings.OPENAI_API_KEY}\n")
    lines.append(f"CUSTOM_TTS_URL={settings.CUSTOM_TTS_URL}\n")
    lines.append(f"CAPCUT_TTS_URL={settings.CAPCUT_TTS_URL}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return {
        "status": "success",
        "message": "Đã lưu cấu hình thành công!",
        "has_gemini_key": bool(settings.GEMINI_API_KEY)
    }
