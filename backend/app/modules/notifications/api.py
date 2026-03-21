from fastapi import APIRouter, Depends, Query

from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from .schemas import NotificationsResponse, UnreadCountResponse
from .service import NotificationsService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=ApiResponse[NotificationsResponse])
async def list_notifications(
    db: AsyncSessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
):
    return ApiResponse.ok(data=await NotificationsService(db).list_notifications(user_id, page, page_size))


@router.get("/unread-count", response_model=ApiResponse[UnreadCountResponse])
async def unread_count(db: AsyncSessionDep, user_id: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await NotificationsService(db).get_unread_count(user_id))


@router.post("/{notification_id}/read", response_model=ApiResponse)
async def mark_read(notification_id: str, db: AsyncSessionDep, user_id: str = Depends(get_current_user_id)):
    await NotificationsService(db).mark_read(notification_id, user_id)
    return ApiResponse.ok()


@router.post("/read-all", response_model=ApiResponse)
async def mark_all_read(db: AsyncSessionDep, user_id: str = Depends(get_current_user_id)):
    await NotificationsService(db).mark_all_read(user_id)
    return ApiResponse.ok()
