import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.api.routes_video import router as video_router
from app.api.routes_voices import router as voices_router
from app.api.routes_credits import router as credits_router
from app.api.routes_settings import router as settings_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Hệ thống AI Video Factory: Dịch thuật, Lồng tiếng tự căn timing, Cắt Shorts 9:16 & Nhân bản nội dung"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file mount để phục vụ video/audio stream cho Web UI
app.mount("/storage", StaticFiles(directory=str(settings.STORAGE_DIR)), name="storage")

# Đăng ký các API Routers
app.include_router(video_router, prefix=settings.API_V1_STR)
app.include_router(voices_router, prefix=settings.API_V1_STR)
app.include_router(credits_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=f"{settings.API_V1_STR}/settings")

# Mount Frontend Static Assets (Hỗ trợ cả root/frontend và backend/frontend_dist)
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend_dist"
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = settings.STORAGE_DIR.parent.parent / "frontend" / "dist"
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = Path("/app/frontend/dist")
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = Path("/app/backend/frontend_dist")

FRONTEND_ASSETS = FRONTEND_DIST / "assets"

if FRONTEND_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS)), name="assets")

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Phục vụ Single Page Application từ frontend/dist"""
    file_path = FRONTEND_DIST / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
