from fastapi import APIRouter, Depends, Query, HTTPException

from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from .schemas import NotificationsResponse, UnreadCountResponse
from .service import NotificationsService

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ========== 原有端点 ==========

@router.get("", response_model=ApiResponse[NotificationsResponse])
async def list_notifications(
    db: AsyncSessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
):
    return ApiResponse.ok(data=await NotificationsService(db).list_notifications(user_id, page, page_size))


@router.get("/unread-count", response_model=ApiResponse[UnreadCountResponse])
async def unread_count(
    db: AsyncSessionDep,
    user_id: str = Depends(get_current_user_id),
):
    return ApiResponse.ok(data=await NotificationsService(db).get_unread_count(user_id))


@router.post("/{notification_id}/read", response_model=ApiResponse)
async def mark_read(
    notification_id: str,
    db: AsyncSessionDep,
    user_id: str = Depends(get_current_user_id),
):
    await NotificationsService(db).mark_read(notification_id, user_id)
    return ApiResponse.ok()


@router.post("/read-all", response_model=ApiResponse)
async def mark_all_read(
    db: AsyncSessionDep,
    user_id: str = Depends(get_current_user_id),
):
    await NotificationsService(db).mark_all_read(user_id)
    return ApiResponse.ok()


# ========== 通道管理 ==========

@router.post("/channels", status_code=201)
async def create_channel(
    db: AsyncSessionDep,
    data: dict,
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    return {"success": True, "data": await NotificationExtService(db).create_channel(data)}


@router.get("/channels")
async def list_channels(
    db: AsyncSessionDep,
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    return {"success": True, "data": await NotificationExtService(db).list_channels()}


@router.put("/channels/{channel_id}")
async def update_channel(
    channel_id: int,
    db: AsyncSessionDep,
    data: dict,
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    return {"success": True, "data": await NotificationExtService(db).update_channel(channel_id, data)}


@router.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: int,
    db: AsyncSessionDep,
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    await NotificationExtService(db).delete_channel(channel_id)
    return {"success": True}


@router.post("/channels/{channel_id}/test")
async def test_channel(
    channel_id: int,
    db: AsyncSessionDep,
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    return {"success": True, "data": await NotificationExtService(db).test_channel(channel_id)}


# ========== 模板管理 ==========

@router.post("/templates", status_code=201)
async def create_template(
    db: AsyncSessionDep,
    data: dict,
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    return {"success": True, "data": await NotificationExtService(db).create_template(data)}


@router.get("/templates")
async def list_templates(
    db: AsyncSessionDep,
    template_type: str | None = Query(None),
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    return {"success": True, "data": await NotificationExtService(db).list_templates(template_type)}


@router.put("/templates/{template_id}")
async def update_template(
    template_id: int,
    db: AsyncSessionDep,
    data: dict,
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    return {"success": True, "data": await NotificationExtService(db).update_template(template_id, data)}


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSessionDep,
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    await NotificationExtService(db).delete_template(template_id)
    return {"success": True}


# ========== 场景矩阵 ==========

@router.post("/rules", status_code=201)
async def create_rule(
    db: AsyncSessionDep,
    data: dict,
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    return {"success": True, "data": await NotificationExtService(db).create_rule(data)}


@router.get("/rules")
async def list_rules(
    db: AsyncSessionDep,
    event_type: str | None = Query(None),
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    return {"success": True, "data": await NotificationExtService(db).list_rules(event_type)}


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    db: AsyncSessionDep,
    data: dict,
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    return {"success": True, "data": await NotificationExtService(db).update_rule(rule_id, data)}


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: AsyncSessionDep,
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    await NotificationExtService(db).delete_rule(rule_id)
    return {"success": True}


# ========== 发送记录 ==========

@router.get("/logs")
async def list_logs(
    db: AsyncSessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: str | None = Query(None),
    status: str | None = Query(None),
    admin=Depends(get_current_user_id),
):
    from app.modules.notifications.service_ext import NotificationExtService
    return {"success": True, "data": await NotificationExtService(db).list_logs(page, page_size, event_type, status)}
