import sys
import os
import webbrowser
import threading
import time
import subprocess
from pathlib import Path

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

# Giải phóng cổng 8000 nếu đang bị chiếm dụng
def free_port_8000():
    if sys.platform == "win32":
        try:
            cmd = "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
            subprocess.run(["powershell", "-Command", cmd], capture_output=True)
            time.sleep(0.5)
        except Exception:
            pass

import uvicorn

def open_browser():
    time.sleep(1.8)
    print("\n[AI Video Factory] Đang mở trình duyệt tại http://127.0.0.1:8000 ...")
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    free_port_8000()

    print("=" * 60)
    print("        🎬 AI VIDEO FACTORY - KHỞI CHẠY HỆ THỐNG")
    print("   Multi-Speaker Dubbing + Auto Shorts + 10x Content")
    print("=" * 60)
    print(">> Backend & Frontend đang chạy tại: http://127.0.0.1:8000")
    print(">> API Docs: http://127.0.0.1:8000/docs")
    print("=" * 60)
    
    # Auto open browser
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False, app_dir=str(backend_dir))
