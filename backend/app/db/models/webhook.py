from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class EmbyWebhookEvent(Base, TimestampMixin):
    """原始 Emby Webhook 事件存储"""
    __tablename__ = "emby_webhook_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    processed: Mapped[bool] = mapped_column(nullable=False, default=False, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 提取的常用字段（方便查询）
    emby_user_id: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    emby_user_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    media_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    media_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(256), nullable=True)

    __table_args__ = (
        Index("ix_webhook_events_event_type_created", "event_type", "created_at"),
        Index("ix_webhook_events_user_created", "emby_user_id", "created_at"),
    )
