from fastapi import APIRouter, Depends

from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from .schemas import DashboardSummary
from .service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=ApiResponse[DashboardSummary])
async def get_summary(db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    service = DashboardService(db)
    data = await service.get_summary()
    return ApiResponse.ok(data=data)
