from pydantic import BaseModel


class WebhookPayload(BaseModel):
    """Emby Webhook 推送的原始结构"""
    Event: str = ""
    User: dict | None = None
    Item: dict | None = None
    Server: dict | None = None
    Session: dict | None = None
    NotificationType: str | None = None
    Timestamp: str | None = None
    # Emby 可能还会推其他字段，用 model_config 放行
    model_config = {"extra": "allow"}


class WebhookResponse(BaseModel):
    received: bool = True
    event_type: str
