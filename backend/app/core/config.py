import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
OUTPUTS_DIR = STORAGE_DIR / "outputs"
TEMP_DIR = STORAGE_DIR / "temp"
MODELS_DIR = STORAGE_DIR / "models"
PIPER_MODELS_DIR = MODELS_DIR / "piper"

for directory in [STORAGE_DIR, UPLOADS_DIR, OUTPUTS_DIR, TEMP_DIR, MODELS_DIR, PIPER_MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "AI Video Factory"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    STORAGE_DIR: Path = STORAGE_DIR
    UPLOADS_DIR: Path = UPLOADS_DIR
    OUTPUTS_DIR: Path = OUTPUTS_DIR
    TEMP_DIR: Path = TEMP_DIR
    PIPER_MODELS_DIR: Path = PIPER_MODELS_DIR
    
    # CapCut TTS Server & Custom TTS Endpoint (Tương thích K07VN / kuwacom / Edge-TTS Server)
    CAPCUT_TTS_URL: str = os.getenv("CAPCUT_TTS_URL", "")
    CUSTOM_TTS_URL: str = os.getenv("CUSTOM_TTS_URL", "")
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    
    DEFAULT_VOICE_MALE: str = "capcut_serious_man"
    DEFAULT_VOICE_FEMALE: str = "capcut_young_girl"
    
    AVAILABLE_VOICES: dict = {
        "vi": [
            # 1. CapCut Voice Catalog (Phong cách thịnh hành trên CapCut & TikTok)
            {"id": "capcut_serious_man", "name": "CapCut - Nam Review Phim Kiếm Hiệp (🎬 Trầm sâu, Điện ảnh)", "gender": "Male", "engine": "CapCut Style", "tag": "🔥 CapCut Hot", "pitch": "-7Hz", "rate": "+5%"},
            {"id": "capcut_young_girl", "name": "CapCut - Cô Gái Hoạt Bát (✨ Trẻ trung, Vui vẻ)", "gender": "Female", "engine": "CapCut Style", "tag": "🔥 CapCut Hot", "pitch": "+6Hz", "rate": "+10%"},
            {"id": "capcut_calm_dubbing", "name": "CapCut - Kể Chuyện Trầm Lắng (📖 Nhẹ nhàng, Truyền cảm)", "gender": "Female", "engine": "CapCut Style", "tag": "🎬 CapCut Dub", "pitch": "+0Hz", "rate": "-6%"},
            {"id": "capcut_confident_man", "name": "CapCut - Thanh Niên Tự Tin (⚡ Dứt khoát, TikTok Trend)", "gender": "Male", "engine": "CapCut Style", "tag": "⚡ CapCut Trend", "pitch": "+2Hz", "rate": "+14%"},
            {"id": "capcut_little_sister", "name": "CapCut - Cô Bé Dễ Thương (👧 Trong trẻo, Ngọt ngào)", "gender": "Female", "engine": "CapCut Style", "tag": "👧 CapCut Cute", "pitch": "+14Hz", "rate": "+6%"},
            {"id": "capcut_radio_host", "name": "CapCut - Host Radio Đêm (📻 Ấm áp, Thủ thỉ)", "gender": "Female", "engine": "CapCut Style", "tag": "📻 CapCut Radio", "pitch": "-4Hz", "rate": "-5%"},
            {"id": "capcut_wise_old_man", "name": "CapCut - Ông Lão Trầm Khàn (👴 Cổ trang, Trải nghiệm)", "gender": "Male", "engine": "CapCut Style", "tag": "👴 CapCut Cổ Trang", "pitch": "-12Hz", "rate": "-10%"},
            {"id": "capcut_grandma", "name": "CapCut - Bà Lão Ấm Áp (👵 Chân thật, Mộc mạc)", "gender": "Female", "engine": "CapCut Style", "tag": "👵 CapCut Gia Đình", "pitch": "-9Hz", "rate": "-10%"},
            {"id": "capcut_energetic_boy", "name": "CapCut - Cậu Bé Tinh Nghịch (👦 Hài hước, Năng động)", "gender": "Male", "engine": "CapCut Style", "tag": "👦 CapCut Hài", "pitch": "+8Hz", "rate": "+12%"},
            {"id": "capcut_robot", "name": "CapCut - AI Robot / Biến Âm Sci-Fi (🤖 Viễn tưởng)", "gender": "Male", "engine": "CapCut Style", "tag": "🤖 CapCut SciFi", "pitch": "+4Hz", "rate": "+15%"},

            # 2. Edge-TTS Chuẩn Mặc Định
            {"id": "vi-VN-NamMinhNeural", "name": "Nam Minh - Chuẩn Bắc Trầm Ấm (Edge-TTS)", "gender": "Male", "engine": "Edge-TTS", "tag": "Chuẩn", "pitch": "+0Hz", "rate": "+0%"},
            {"id": "vi-VN-HoaiMyNeural", "name": "Hoài My - Chuẩn Bắc Truyền Cảm (Edge-TTS)", "gender": "Female", "engine": "Edge-TTS", "tag": "Chuẩn", "pitch": "+0Hz", "rate": "+0%"},

            # 3. viPiper Local Offline Engines (Chạy Offline 100% trên CPU)
            {"id": "piper:vi_VN-25hours_single-low", "name": "viPiper 25Hours Single (Local Offline CPU - Nữ)", "gender": "Female", "engine": "viPiper Local", "tag": "💻 Local Offline", "pitch": "+0Hz", "rate": "+0%"},
            {"id": "piper:vi_VN-vivos-x_low", "name": "viPiper Vivos Multi-Speaker (Local Offline CPU - Nam/Nữ)", "gender": "Male", "engine": "viPiper Local", "tag": "💻 Local Offline", "pitch": "+0Hz", "rate": "+0%"},
        ],
        "en": [
            {"id": "en-US-AndrewMultilingualNeural", "name": "Andrew - Male US (Đa ngôn ngữ cao cấp)", "gender": "Male", "engine": "Edge-TTS", "tag": "Natural"},
            {"id": "en-US-AvaMultilingualNeural", "name": "Ava - Female US (Đa ngôn ngữ cao cấp)", "gender": "Female", "engine": "Edge-TTS", "tag": "Natural"},
            {"id": "en-US-BrianMultilingualNeural", "name": "Brian - Male US (Trầm ấm)", "gender": "Male", "engine": "Edge-TTS", "tag": "Narrator"},
            {"id": "en-US-EmmaNeural", "name": "Emma - Female US (Rõ ràng, Tự nhiên)", "gender": "Female", "engine": "Edge-TTS", "tag": "Natural"},
            {"id": "en-US-GuyNeural", "name": "Guy - Male US (Năng động)", "gender": "Male", "engine": "Edge-TTS", "tag": "Casual"},
            {"id": "en-US-JennyNeural", "name": "Jenny - Female US (Thân thiện)", "gender": "Female", "engine": "Edge-TTS", "tag": "Casual"},
            {"id": "en-US-AriaNeural", "name": "Aria - Female US (Tin tức)", "gender": "Female", "engine": "Edge-TTS", "tag": "News"},
            {"id": "en-US-ChristopherNeural", "name": "Christopher - Male US (Điện ảnh)", "gender": "Male", "engine": "Edge-TTS", "tag": "Cinema"},
        ],
        "zh": [
            {"id": "zh-CN-YunjianNeural", "name": "Yunjian - Nam Review Phim Kiếm Hiệp Trung Quốc", "gender": "Male", "engine": "CapCut/Edge", "tag": "🎬 Review Phim"},
            {"id": "zh-CN-YunxiNeural", "name": "Yunxi - Nam Kể Chuyện Hiện Đại", "gender": "Male", "engine": "CapCut/Edge", "tag": "Story"},
            {"id": "zh-CN-XiaoxiaoNeural", "name": "Xiaoxiao - Nữ Truyền Cảm Chuẩn Bắc Kinh", "gender": "Female", "engine": "CapCut/Edge", "tag": "Natural"},
            {"id": "zh-CN-YunyangNeural", "name": "Yunyang - Nam Tin Tức / Phim Tài Liệu", "gender": "Male", "engine": "CapCut/Edge", "tag": "Documentary"},
            {"id": "zh-CN-XiaoyiNeural", "name": "Xiaoyi - Nữ Tình Cảm / Đọc Sách", "gender": "Female", "engine": "CapCut/Edge", "tag": "Warm"},
        ],
        "ja": [
            {"id": "ja-JP-NanamiNeural", "name": "Nanami - Nữ Nhật Bản Chuẩn Tokyo", "gender": "Female", "engine": "Edge-TTS", "tag": "Anime/Natural"},
            {"id": "ja-JP-KeitaNeural", "name": "Keita - Nam Nhật Bản Trẻ Trung", "gender": "Male", "engine": "Edge-TTS", "tag": "Natural"},
            {"id": "ja-JP-DaichiNeural", "name": "Daichi - Nam Nhật Bản Trầm Ấm", "gender": "Male", "engine": "Edge-TTS", "tag": "Narrator"},
            {"id": "ja-JP-AoiNeural", "name": "Aoi - Nữ Anime Trong Sáng", "gender": "Female", "engine": "Edge-TTS", "tag": "Anime"},
        ],
        "ko": [
            {"id": "ko-KR-SunHiNeural", "name": "SunHi - Nữ Hàn Quốc Ngọt Ngào", "gender": "Female", "engine": "Edge-TTS", "tag": "K-Drama"},
            {"id": "ko-KR-InJoonNeural", "name": "InJoon - Nam Hàn Quốc Cuốn Hút", "gender": "Male", "engine": "Edge-TTS", "tag": "K-Drama"},
            {"id": "ko-KR-BongJinNeural", "name": "BongJin - Nam Hàn Quốc Trầm", "gender": "Male", "engine": "Edge-TTS", "tag": "Narrator"},
            {"id": "ko-KR-YuJinNeural", "name": "YuJin - Nữ Hàn Quốc Tin Tức", "gender": "Female", "engine": "Edge-TTS", "tag": "News"},
        ]
    }

settings = Settings()
