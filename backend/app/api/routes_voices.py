from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings
from app.services.tts_engine import tts_engine

router = APIRouter(prefix="/voices", tags=["Voices"])

class VoicePreviewRequest(BaseModel):
    text: str = "Xin chào, đây là giọng đọc AI chất lượng cao của hệ thống AI Video Factory."
    voice_id: str = "vi-VN-HoaiMyNeural"

@router.get("/list")
async def get_available_voices():
    """Lấy danh sách tất cả các giọng đọc AI được hỗ trợ"""
    return {
        "voices": settings.AVAILABLE_VOICES,
        "default_male": settings.DEFAULT_VOICE_MALE,
        "default_female": settings.DEFAULT_VOICE_FEMALE
    }

@router.post("/preview")
async def preview_voice(req: VoicePreviewRequest):
    """Sinh thử audio giọng đọc để người dùng nghe thử trên UI"""
    preview_file = settings.TEMP_DIR / f"preview_{req.voice_id}.mp3"
    success = await tts_engine.generate_speech(req.text, req.voice_id, str(preview_file))
    if success:
        return {
            "status": "success",
            "audio_url": f"/storage/temp/preview_{req.voice_id}.mp3"
        }
    return {"status": "error", "message": "Không thể sinh giọng đọc thử nghiệm"}
