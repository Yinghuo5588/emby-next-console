from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from . import service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_summary(_: str = Depends(get_current_user_id)):
    data = await service.get_summary()
    return ApiResponse.ok(data=data)
