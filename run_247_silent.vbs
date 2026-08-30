Set WshShell = CreateObject("WScript.Shell")

' Set working directory to project root
WshShell.CurrentDirectory = "C:\Users\test01\.gemini\antigravity\scratch\ai-video-factory"

' 1. Start Python AI Video Factory Backend silently (WindowStyle 0 = Hidden)
WshShell.Run "python run.py", 0, False

WScript.Sleep 3000

' 2. Start Cloudflare Tunnel silently (WindowStyle 0 = Hidden)
WshShell.Run "C:\Users\test01\.gemini\antigravity\scratch\cloudflared.exe tunnel --url http://127.0.0.1:8000", 0, False
