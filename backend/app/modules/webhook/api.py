import logging

from fastapi import APIRouter, Request, Header

from app.db.session import AsyncSessionDep
from app.core.settings import settings
from app.shared.responses import ApiResponse
from .schemas import WebhookPayload, WebhookResponse
from .service import WebhookService

logger = logging.getLogger("app.webhook")

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/emby", response_model=ApiResponse[WebhookResponse])
async def receive_emby_webhook(
    payload: WebhookPayload,
    db: AsyncSessionDep,
    request: Request,
    x_emby_token: str | None = Header(None),
):
    """接收 Emby Webhook 推送"""
    # 验证 token（可选，Emby 会在 header 里带 token）
    if settings.EMBY_WEBHOOK_TOKEN and x_emby_token != settings.EMBY_WEBHOOK_TOKEN:
        logger.warning(f"Webhook token mismatch: got {x_emby_token}")
        # 不强制拒绝，只记录

    svc = WebhookService(db)
    event_type = await svc.receive(payload)

    logger.info(f"Webhook received: {event_type}")
    return ApiResponse.ok(data=WebhookResponse(event_type=event_type))


@router.post("/test", response_model=ApiResponse[WebhookResponse])
async def test_webhook(
    payload: WebhookPayload,
    db: AsyncSessionDep,
):
    """测试用端点 - 接收并存储事件但不触发下游逻辑"""
    svc = WebhookService(db)
    event_type = await svc.receive(payload)
    return ApiResponse.ok(data=WebhookResponse(event_type=event_type))
