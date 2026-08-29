import cv2
import numpy as np
import subprocess
import os
from pathlib import Path
from typing import Tuple, List

class SmartCropper:
    """Tự động nhận diện khuôn mặt người nói và crop 9:16 siêu tốc cho Shorts/TikTok"""
    
    def __init__(self):
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(cascade_path):
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        else:
            self.face_cascade = None

    def detect_face_centers(self, video_path: str, start_time: float, end_time: float, sample_rate: int = 15) -> float:
        """
        Lấy mẫu khung hình nhanh để tính toạ độ X trung tâm.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return 0.5
            
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
        
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        current_frame = start_frame
        
        x_positions = []
        
        while current_frame <= end_frame and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            if (current_frame - start_frame) % sample_rate == 0 and self.face_cascade is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                small_gray = cv2.resize(gray, (640, 360))
                scale_x = width / 640.0
                
                faces = self.face_cascade.detectMultiScale(small_gray, scaleFactor=1.2, minNeighbors=4, minSize=(30, 30))
                if len(faces) > 0:
                    largest_face = max(faces, key=lambda r: r[2] * r[3])
                    fx, fy, fw, fh = largest_face
                    face_center_x = (fx + fw / 2.0) * scale_x
                    x_positions.append(face_center_x / width)
                    
            current_frame += 1
            
        cap.release()
        
        if x_positions:
            return float(np.median(x_positions))
        return 0.5

    def crop_to_shorts(self, video_path: str, start_time: float, end_time: float, output_path: str, center_x_ratio: float = 0.5) -> bool:
        """
        Cắt video thành kích thước dọc 9:16 (1080x1920) với preset ultrafast + faststart stream.
        """
        duration = end_time - start_time
        
        crop_filter = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-ss", str(start_time),
            "-i", video_path,
            "-t", str(duration),
            "-vf", crop_filter,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception as e:
            print(f"[SmartCropper] Crop error: {e}")
            return False

smart_cropper = SmartCropper()
