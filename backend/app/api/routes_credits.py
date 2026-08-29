from fastapi import APIRouter
from pydantic import BaseModel
from app.core.credit_manager import credit_manager

router = APIRouter(prefix="/credits", tags=["Credits"])

class UpgradeRequest(BaseModel):
    tier: str

@router.get("/status")
async def get_credit_status():
    """Lấy số dư credit và thông tin gói hiện tại"""
    return credit_manager.get_status()

@router.post("/upgrade")
async def upgrade_tier(req: UpgradeRequest):
    """Mô phỏng nâng cấp gói cước"""
    if req.tier in credit_manager.TIERS:
        credit_manager.data["current_tier"] = req.tier
        credit_manager.data["remaining_credits"] += credit_manager.TIERS[req.tier]["credits"]
        credit_manager._save_data()
        return {"status": "success", "message": f"Nâng cấp thành công lên {credit_manager.TIERS[req.tier]['name']}!"}
    return {"status": "error", "message": "Gói không hợp lệ"}
