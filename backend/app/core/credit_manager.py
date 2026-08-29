from typing import Dict, Any
import json
from pathlib import Path

class CreditManager:
    """Quản lý hạn mức và gói cước (FREE, PRO, PRO+, BUSINESS)"""
    
    TIERS = {
        "FREE": {
            "name": "Gói Miễn Phí (FREE)",
            "price": "0đ",
            "credits": 3,
            "max_resolution": "720p",
            "watermark": True,
            "features": ["3 video/tháng", "Độ phân giải 720p", "Có Watermark", "Giới hạn thời lượng 2 phút/video"]
        },
        "PRO": {
            "name": "Gói Pro Sáng Tạo (PRO)",
            "price": "99.000đ/tháng",
            "credits": 60, # 60 phút
            "max_resolution": "1080p",
            "watermark": False,
            "features": ["60 phút video/tháng", "Độ phân giải 1080p Full HD", "Không Watermark", "AI Subtitle & Dịch thuật đa ngôn ngữ"]
        },
        "PRO_PLUS": {
            "name": "Gói Chuyên Nghiệp (PRO+)",
            "price": "199.000đ/tháng",
            "credits": 180, # 180 phút
            "max_resolution": "1080p",
            "watermark": False,
            "features": ["180 phút video/tháng", "AI Smart Dubbing Đa Vai", "Auto Căn Timing & Ducking", "Auto Cắt Shorts 9:16 Viral"]
        },
        "BUSINESS": {
            "name": "Gói Doanh Nghiệp (BUSINESS)",
            "price": "499.000đ/tháng",
            "credits": 600, # 600 phút
            "max_resolution": "4K / 1080p 60fps",
            "watermark": False,
            "features": ["600 phút video/tháng", "Xử lý hàng loạt (Batch Processing)", "API Tích hợp hệ thống", "Hỗ trợ Team & Tối ưu riêng"]
        }
    }
    
    def __init__(self, storage_path: Path = None):
        self.storage_path = storage_path or Path(__file__).resolve().parent.parent.parent / "storage" / "user_credits.json"
        self._load_data()
        
    def _load_data(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                    return
            except Exception:
                pass
        
        # Dữ liệu mặc định
        self.data = {
            "current_tier": "PRO_PLUS",
            "remaining_credits": 180, # phút
            "used_credits": 15,
            "total_videos_processed": 6,
            "total_shorts_generated": 24
        }
        self._save_data()
        
    def _save_data(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            
    def get_status(self) -> Dict[str, Any]:
        tier_info = self.TIERS.get(self.data["current_tier"], self.TIERS["FREE"])
        return {
            **self.data,
            "tier_info": tier_info,
            "all_tiers": self.TIERS
        }
        
    def deduct_credits(self, minutes: float) -> bool:
        if self.data["remaining_credits"] >= minutes:
            self.data["remaining_credits"] -= minutes
            self.data["used_credits"] += minutes
            self.data["total_videos_processed"] += 1
            self._save_data()
            return True
        return False
        
    def add_shorts_count(self, count: int = 1):
        self.data["total_shorts_generated"] += count
        self._save_data()

credit_manager = CreditManager()
