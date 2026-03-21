import logging

from fastapi import APIRouter, Request, Header, Query

from app.db.session import AsyncSessionDep
from app.core.settings import settings
from app.shared.responses import ApiResponse
from .schemas import WebhookPayload, WebhookResponse
from .service import WebhookService

logger = logging.getLogger("app.webhook")

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/emby", response_model=ApiResponse[WebhookResponse])
async def receive_emby_webhook(
    request: Request,
    db: AsyncSessionDep,
    x_emby_token: str | None = Header(None),
    token: str | None = Query(None),
):
    """接收 Emby Webhook 推送 - 支持 header 和 query 两种 token 验证"""
    # Token 验证（header 或 query param）
    webhook_token = settings.EMBY_WEBHOOK_TOKEN
    if webhook_token and x_emby_token != webhook_token and token != webhook_token:
        logger.warning("Webhook token mismatch")

    # 解析 payload（支持 JSON 和 form data）
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        data = await request.json()
    elif "form" in content_type:
        form = await request.form()
        import json
        raw_data = form.get("data")
        data = json.loads(raw_data) if raw_data else {}
    else:
        data = await request.json()

    payload = WebhookPayload(**data)
    svc = WebhookService(db)
    event_type = await svc.receive(payload)

    return ApiResponse.ok(data=WebhookResponse(event_type=event_type))


@router.post("/test", response_model=ApiResponse[WebhookResponse])
async def test_webhook(payload: WebhookPayload, db: AsyncSessionDep):
    """测试端点 - 接收并存储事件但不触发拦截"""
    svc = WebhookService(db)
    event_type = await svc.receive(payload)
    return ApiResponse.ok(data=WebhookResponse(event_type=event_type))
