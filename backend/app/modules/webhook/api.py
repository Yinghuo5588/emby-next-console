"""
Emby Webhook 接收端点
接收 Emby 推送的播放事件。
"""
import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request, HTTPException

from app.core.settings import settings
from app.shared.responses import ApiResponse

logger = logging.getLogger("app.webhook")
router = APIRouter(prefix="/webhook", tags=["webhook"])

tz_cn = timezone(timedelta(hours=8))


@router.post("/emby")
async def emby_webhook(request: Request):
    """接收 Emby Webhook 事件"""
    # Token 验证
    query_token = request.query_params.get("token", "")
    if query_token != settings.EMBY_WEBHOOK_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

    try:
        content_type = request.headers.get("content-type", "")
        data: dict = {}
        if "application/json" in content_type:
            data = await request.json()
        elif "form" in content_type:
            form = await request.form()
            raw = form.get("data")
            if raw:
                data = json.loads(raw)

        if not data:
            return ApiResponse.ok(message="Empty payload")

        event = data.get("Event", "")
        session = data.get("Session", {})
        item = data.get("Item", {})

        logger.info(
            "🔔 Emby Webhook: event=%s user=%s media=%s client=%s",
            event,
            session.get("UserName", "?"),
            item.get("Name", "?"),
            session.get("Client", "?"),
        )

        # TODO: 写入 playback_events 表 + 通知系统
        # 这里先只记录日志，后续对接数据库和通知

        return ApiResponse.ok(message="Received")

    except Exception as e:
        logger.error("Webhook 处理异常: %s", e)
        return ApiResponse.error(message=str(e))


@router.get("/status")
async def webhook_status():
    """Webhook 状态检查"""
    return ApiResponse.ok(data={
        "webhook_url": f"/api/v1/webhook/emby?token={settings.EMBY_WEBHOOK_TOKEN[:4]}***",
        "hint": "在 Emby 后台 → 设置 → Webhook 添加此 URL",
    })
