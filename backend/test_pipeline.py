import asyncio
import os
import subprocess
from pathlib import Path

# Đảm bảo import được app modules
import sys
sys.path.insert(0, str(Path(__file__).parent))
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from app.core.config import settings
from app.services.pipeline import pipeline

def create_dummy_sample_video(output_video_path: str):
    """Tạo một file video mẫu 15 giây có âm thanh để test toàn bộ pipeline"""
    print(f"Creating sample test video at: {output_video_path}")
    # Sử dụng FFmpeg lavfi tạo video có hình và âm thanh test
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=12:size=1280x720:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=12",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        output_video_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    print("Sample video created successfully!")

async def test_full_pipeline():
    print("=== STARTING AI VIDEO FACTORY PIPELINE TEST ===")
    sample_video = str(settings.TEMP_DIR / "test_sample_video.mp4")
    create_dummy_sample_video(sample_video)
    
    task_id = "test_001"
    print(f"Running pipeline for task_id: {task_id}")
    
    result = await pipeline.run_pipeline(
        task_id=task_id,
        video_path=sample_video,
        target_lang="vi",
        source_lang="auto",
        custom_prompt="Tạo 2 video Shorts hấp dẫn"
    )
    
    print("\n=== PIPELINE EXECUTION SUMMARY ===")
    print("Full Dubbed Video URL:", result.get("full_video_url"))
    print(f"Shorts Generated ({len(result.get('shorts', []))} clips):")
    for s in result.get("shorts", []):
        print(f" - [{s['viral_score']}/100] {s['title']} -> {s.get('video_url')}")
    print("Titles:", len(result.get("content_pack", {}).get("titles", [])))
    print("ZIP Export URL:", result.get("zip_download_url"))
    print("=== TEST COMPLETED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
