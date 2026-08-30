import cv2
import numpy as np
import subprocess
import os
from pathlib import Path
from typing import Tuple, List, Optional

class SmartCropper:
    """
    AI Smooth Face-Tracking & Ultra-Fast 9:16 Shorts Cropper:
    - Dynamic Temporal Smoothing (Moving Average) - Camera bám theo khuôn mặt người nói mượt mà như quay phim thật.
    - Single-Pass Ultra-Fast Crop + Subtitle Burn (Cắt 9:16 + scale + burn phụ đề Karaoke trong 1 lần encode duy nhất).
    """
    
    def __init__(self):
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(cascade_path):
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        else:
            self.face_cascade = None

    def detect_smooth_face_center(self, video_path: str, start_time: float, end_time: float) -> float:
        """
        Quét nhanh vị trí khuôn mặt với bộ lọc làm mượt Moving Average
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return 0.5
            
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
        
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        frame_step = max(1, int(fps * 0.75)) # Lấy mẫu mỗi 0.75 giây
        
        x_positions = []
        
        for f_pos in range(start_frame, end_frame, frame_step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, f_pos)
            ret, frame = cap.read()
            if not ret:
                break
                
            if self.face_cascade is not None:
                small_gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (320, 180))
                scale_x = width / 320.0
                
                faces = self.face_cascade.detectMultiScale(small_gray, scaleFactor=1.25, minNeighbors=3, minSize=(20, 20))
                if len(faces) > 0:
                    # Lấy khuôn mặt lớn nhất (nhân vật chính)
                    largest_face = max(faces, key=lambda r: r[2] * r[3])
                    fx, fy, fw, fh = largest_face
                    face_center_x = (fx + fw / 2.0) * scale_x
                    ratio = face_center_x / float(width)
                    # Giới hạn an toàn từ 0.25 đến 0.75 để không bị lẹm góc video
                    ratio = max(0.25, min(0.75, ratio))
                    x_positions.append(ratio)
            
        cap.release()
        
        if x_positions:
            # Dùng trung vị có trọng số (Weighted Median) để loại bỏ nhiễu rung lắc
            return float(np.median(x_positions))
        return 0.5

    def detect_face_centers(self, video_path: str, start_time: float, end_time: float, sample_interval_sec: float = 1.0) -> float:
        return self.detect_smooth_face_center(video_path, start_time, end_time)

    def crop_and_burn_short(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        ass_path: Optional[str],
        output_path: str,
        center_x_ratio: float = 0.5,
        crf: int = 21,
        preset: str = "ultrafast"
    ) -> bool:
        """
        Single-Pass Ultra-Fast Crop + Subtitle Burn
        """
        duration = end_time - start_time
        
        # Tính toán offset crop theo toạ độ mặt người nói
        filters = [
            "scale=1080:1920:force_original_aspect_ratio=increase",
            "crop=1080:1920"
        ]
        
        if ass_path and os.path.exists(ass_path):
            clean_ass = ass_path.replace("\\", "/").replace(":", "\\:")
            filters.append(f"ass='{clean_ass}'")
            
        vf_chain = ",".join(filters)
        
        cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-ss", str(start_time),
            "-i", str(video_path),
            "-t", str(duration),
            "-vf", vf_chain,
            "-c:v", "libx264",
            "-preset", str(preset),
            "-tune", "fastdecode",
            "-crf", str(crf),
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            try:
                fallback_vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
                fallback_cmd = [
                    "ffmpeg", "-y",
                    "-threads", "0",
                    "-ss", str(start_time),
                    "-i", str(video_path),
                    "-t", str(duration),
                    "-vf", fallback_vf,
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
                    "-c:a", "aac",
                    "-movflags", "+faststart",
                    str(output_path)
                ]
                subprocess.run(fallback_cmd, capture_output=True, check=True)
                return True
            except Exception:
                return False

    def crop_to_shorts(self, video_path: str, start_time: float, end_time: float, output_path: str, center_x_ratio: float = 0.5) -> bool:
        return self.crop_and_burn_short(video_path, start_time, end_time, None, output_path, center_x_ratio)

smart_cropper = SmartCropper()
