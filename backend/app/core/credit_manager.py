from typing import Dict, Any
import json
from pathlib import Path
import time

class CreditManager:
    """
    Multi-Tenant Per-Device Isolated Cloud & Quota Manager:
    - Mỗi thiết bị / người dùng có không gian lưu trữ và số dư credit hoàn toàn riêng biệt.
    - Không tính chung dung lượng hay hạn mức vào máy chủ chính.
    """
    
    TIERS = {
        "FREE": {
            "name": "Gói Miễn Phí (FREE)",
            "price": "0đ",
            "credits": 30, # Tặng 30 phút cho mỗi thiết bị mới
            "max_resolution": "720p",
            "watermark": False,
            "features": ["30 phút video/tháng", "Độ phân giải HD", "Không Watermark", "Dung lượng Cloud riêng"]
        },
        "PRO": {
            "name": "Gói Pro Sáng Tạo (PRO)",
            "price": "99.000đ/tháng",
            "credits": 120,
            "max_resolution": "1080p",
            "watermark": False,
            "features": ["120 phút video/tháng", "Độ phân giải 1080p Full HD", "AI Subtitle & Dịch đa ngôn ngữ", "Cloud riêng biệt"]
        },
        "PRO_PLUS": {
            "name": "Gói Chuyên Nghiệp (PRO+)",
            "price": "199.000đ/tháng",
            "credits": 300,
            "max_resolution": "1080p",
            "watermark": False,
            "features": ["300 phút video/tháng", "AI Smart Dubbing Đa Vai", "Auto Căn Timing", "Auto Cắt Shorts 9:16"]
        },
        "BUSINESS": {
            "name": "Gói Doanh Nghiệp (BUSINESS)",
            "price": "499.000đ/tháng",
            "credits": 1000,
            "max_resolution": "4K / 1080p 60fps",
            "watermark": False,
            "features": ["1000 phút video/tháng", "Xử lý siêu tốc đa luồng", "Không gian lưu trữ Cloud độc quyền"]
        }
    }
    
    def __init__(self, storage_path: Path = None):
        self.storage_path = storage_path or Path(__file__).resolve().parent.parent.parent / "storage" / "user_credits.json"
        self.devices_data: Dict[str, Any] = {}
        self._load_data()
        
    def _load_data(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, dict):
                        # Nếu file cũ lưu dạng đơn thiết bị, chuyển đổi sang multi-device
                        if "remaining_credits" in content and "devices" not in content:
                            self.devices_data = {
                                "default": content
                            }
                        else:
                            self.devices_data = content.get("devices", {})
                        return
            except Exception:
                pass
        
        self.devices_data = {
            "default": {
                "current_tier": "PRO_PLUS",
                "remaining_credits": 300,
                "used_credits": 0,
                "total_videos_processed": 0,
                "total_shorts_generated": 0,
                "created_at": time.time()
            }
        }
        self._save_data()
        
    def _save_data(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"devices": self.devices_data}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CreditManager] Save error: {e}")

    def _get_device_record(self, device_id: str) -> Dict[str, Any]:
        dev_id = str(device_id or "default").strip()
        if not dev_id:
            dev_id = "default"
            
        if dev_id not in self.devices_data:
            # Cấp mới gói Cloud & Credit độc lập cho mỗi thiết bị truy cập
            self.devices_data[dev_id] = {
                "current_tier": "PRO_PLUS",
                "remaining_credits": 180, # Tặng 180 phút miễn phí cho mỗi máy
                "used_credits": 0,
                "total_videos_processed": 0,
                "total_shorts_generated": 0,
                "created_at": time.time()
            }
            self._save_data()
            
        return self.devices_data[dev_id]
            
    def get_status(self, device_id: str = "default") -> Dict[str, Any]:
        dev_record = self._get_device_record(device_id)
        tier_info = self.TIERS.get(dev_record["current_tier"], self.TIERS["FREE"])
        return {
            **dev_record,
            "device_id": device_id,
            "tier_info": tier_info,
            "all_tiers": self.TIERS,
            "cloud_storage_mode": "per_device_isolated"
        }
        
    def deduct_credits(self, minutes: float, device_id: str = "default") -> bool:
        dev_record = self._get_device_record(device_id)
        if dev_record["remaining_credits"] >= minutes:
            dev_record["remaining_credits"] = max(0.0, dev_record["remaining_credits"] - minutes)
            dev_record["used_credits"] += minutes
            dev_record["total_videos_processed"] += 1
            self._save_data()
            return True
        return False
        
    def add_shorts_count(self, count: int = 1, device_id: str = "default"):
        dev_record = self._get_device_record(device_id)
        dev_record["total_shorts_generated"] += count
        self._save_data()

    def upgrade_device_tier(self, device_id: str, tier: str) -> bool:
        if tier in self.TIERS:
            dev_record = self._get_device_record(device_id)
            dev_record["current_tier"] = tier
            dev_record["remaining_credits"] += self.TIERS[tier]["credits"]
            self._save_data()
            return True
        return False

credit_manager = CreditManager()
