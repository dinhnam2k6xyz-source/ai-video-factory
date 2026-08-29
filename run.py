import sys
import os
import webbrowser
import threading
import time
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

import uvicorn

def open_browser():
    time.sleep(1.5)
    print("\n[AI Video Factory] Dang mo trinh duyet tai http://127.0.0.1:8000 ...")
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("=" * 60)
    print("        AI VIDEO FACTORY - KHOI CHAY HE THONG")
    print("   Multi-Speaker Dubbing + Auto Shorts + 10x Content")
    print("=" * 60)
    print(">> Backend & Frontend dang chay tai: http://127.0.0.1:8000")
    print(">> API Docs: http://127.0.0.1:8000/docs")
    print("=" * 60)
    
    # Auto open browser
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False, app_dir=str(backend_dir))
