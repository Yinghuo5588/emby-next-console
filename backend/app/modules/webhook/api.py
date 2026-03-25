"""
Webhook 接收模块 — 接收 Emby Webhook 事件，存储并触发风控扫描
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, Query, Request
from pydantic import BaseModel
from sqlalchemy import select

from app.core.settings import settings
from app.db.models.webhook import EmbyWebhookEvent
from app.db.session import AsyncSessionDep
from app.shared.responses import ApiResponse

logger = logging.getLogger("app.webhook")

router = APIRouter(prefix="/webhook", tags=["webhook"])

# Emby playback event types that should trigger risk scan
PLAYBACK_EVENTS = {
    "playback.start",
    "playback.stop",
    "playback.pause",
    "playback.unpause",
    "session.start",
    "session.end",
}


def _verify_token(
    token_query: str | None = Query(None, alias="token"),
    token_header: str | None = Header(None, alias="X-Webhook-Token"),
) -> bool:
    """验证 webhook token（支持 query param 或 header）"""
    expected = settings.EMBY_WEBHOOK_TOKEN
    if not expected:
        return True  # 未设置 token 则不验证
    return token_query == expected or token_header == expected


@router.post("/emby")
async def receive_emby_webhook(
    request: Request,
    token_query: str | None = Query(None, alias="token"),
    token_header: str | None = Header(None, alias="X-Webhook-Token"),
):
    """
    接收 Emby Webhook 事件
    Emby 调用格式: POST /api/v1/webhook/emby?token=xxx
    Body 是 JSON 或 form data
    """
    # Token 验证
    if not _verify_token(token_query, token_header):
        return ApiResponse.error("Unauthorized", error_code="UNAUTHORIZED")

    # 解析 payload
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            payload = await request.json()
        elif "form" in content_type:
            form = await request.form()
            payload = dict(form)
        else:
            # 尝试 JSON
            body = await request.body()
            import json
            payload = json.loads(body) if body else {}
    except Exception as e:
        logger.warning(f"Failed to parse webhook payload: {e}")
        payload = {"_parse_error": str(e)}

    # 提取常用字段
    event_type = payload.get("Event", payload.get("event", payload.get("event_type", "unknown")))
    user_id = payload.get("UserId", payload.get("user_id", ""))
    user_name = payload.get("UserName", payload.get("user_name", ""))
    device_name = payload.get("DeviceName", payload.get("device_name", ""))
    session_id = payload.get("SessionId", payload.get("session_id", ""))

    # 从 Item 或 NotificationUsername 提取媒体信息
    item = payload.get("Item", {})
    media_name = item.get("Name", payload.get("Name", payload.get("media_name", ""))) if isinstance(item, dict) else str(item)
    media_type = item.get("Type", payload.get("Type", "")) if isinstance(item, dict) else ""

    # 存储到数据库
    try:
        from app.db.session import AsyncSessionFactory
        async with AsyncSessionFactory() as db:
            event = EmbyWebhookEvent(
                event_type=str(event_type),
                raw_payload=payload,
                processed=False,
                emby_user_id=str(user_id) if user_id else None,
                emby_user_name=str(user_name) if user_name else None,
                media_name=str(media_name) if media_name else None,
                media_type=str(media_type) if media_type else None,
                device_name=str(device_name) if device_name else None,
                session_id=str(session_id) if session_id else None,
            )
            db.add(event)
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to store webhook event: {e}")

    # 播放相关事件触发快速风控扫描
    if str(event_type).lower() in PLAYBACK_EVENTS:
        asyncio.create_task(_quick_risk_scan())

    return ApiResponse.ok(message="ok")


async def _quick_risk_scan():
    """延迟 3 秒后执行一次快速风控扫描"""
    try:
        await asyncio.sleep(3)
        from app.db.session import AsyncSessionFactory
        from app.modules.risk.api import _scan_logic
        async with AsyncSessionFactory() as db:
            result = await _scan_logic(db)
            blocked = len(result.get("blocked", []))
            violations = len(result.get("violations", []))
            if blocked or violations:
                logger.warning(f"Webhook triggered scan: {blocked} blocked, {violations} violations")
    except Exception as e:
        logger.error(f"Quick risk scan error: {e}")


@router.get("/info")
async def webhook_info():
    """获取 webhook 配置信息（供设置页展示）"""
    from app.core.settings import settings as s
    return ApiResponse.ok(data={
        "emby_webhook_url": "/api/v1/webhook/emby",
        "token_header": "X-Webhook-Token",
        "token_query": "token",
        "has_token": bool(s.EMBY_WEBHOOK_TOKEN),
    })


@router.get("/events")
async def list_events(
    page: int = 1,
    page_size: int = 20,
    event_type: str | None = None,
):
    """查看 webhook 事件记录"""
    from app.db.session import AsyncSessionFactory
    async with AsyncSessionFactory() as db:
        stmt = select(EmbyWebhookEvent)
        if event_type:
            stmt = stmt.where(EmbyWebhookEvent.event_type == event_type)
        stmt = stmt.order_by(EmbyWebhookEvent.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(stmt)
        events = result.scalars().all()

        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(EmbyWebhookEvent)
        if event_type:
            count_stmt = count_stmt.where(EmbyWebhookEvent.event_type == event_type)
        total = await db.scalar(count_stmt) or 0

    return ApiResponse.ok(data={
        "items": [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "emby_user_name": ev.emby_user_name,
                "media_name": ev.media_name,
                "media_type": ev.media_type,
                "device_name": ev.device_name,
                "processed": ev.processed,
                "created_at": ev.created_at,
            }
            for ev in events
        ],
        "total": int(total),
    })
