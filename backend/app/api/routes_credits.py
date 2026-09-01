from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.core.credit_manager import credit_manager

router = APIRouter(prefix="/credits", tags=["Credits"])

class UpgradeRequest(BaseModel):
    tier: str

@router.get("/status")
async def get_credit_status(request: Request):
    """Lấy số dư credit và thông tin gói cước riêng cho từng thiết bị"""
    device_id = request.headers.get("x-device-id") or request.query_params.get("device_id") or "default"
    return credit_manager.get_status(device_id)

@router.post("/upgrade")
async def upgrade_tier(req: UpgradeRequest, request: Request):
    """Nâng cấp gói cước cho thiết bị hiện tại"""
    device_id = request.headers.get("x-device-id") or request.query_params.get("device_id") or "default"
    ok = credit_manager.upgrade_device_tier(device_id, req.tier)
    if ok:
        tier_name = credit_manager.TIERS[req.tier]["name"]
        return {"status": "success", "message": f"Thiết bị của bạn đã nâng cấp thành công lên {tier_name}!"}
    return {"status": "error", "message": "Gói không hợp lệ"}
