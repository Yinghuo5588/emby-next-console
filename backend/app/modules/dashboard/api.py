from fastapi import APIRouter, Depends

from app.shared.responses import ApiResponse
from . import service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_summary():
    data = await service.get_summary()
    return ApiResponse.ok(data=data)
