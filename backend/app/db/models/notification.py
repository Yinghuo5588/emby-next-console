from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False, default="info")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    action_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_is_read", "is_read"),
        Index("ix_notifications_created_at", "created_at"),
        Index("ix_notifications_user_is_read", "user_id", "is_read"),
    )


class NotificationChannel(Base):
    """通知通道配置 — webhook/email/bark 等"""
    __tablename__ = "notification_channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)  # webhook/email/bark/dingtalk/telegram
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {url, token, api_key, ...}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class NotificationTemplate(Base):
    """消息模板"""
    __tablename__ = "notification_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    template_type: Mapped[str] = mapped_column(String(32), nullable=False)  # risk_alert/new_content/system/welcome
    title_template: Mapped[str] = mapped_column(String(512), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["username", "series_name"]
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class NotificationRule(Base):
    """场景矩阵 — 哪些事件用哪些通道发哪些模板"""
    __tablename__ = "notification_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # risk_high/new_episode/login_new_ip/...
    channel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("notification_channels.id", ondelete="CASCADE"), nullable=False)
    template_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("notification_templates.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")

    __table_args__ = (
        Index("ix_notification_rules_event", "event_type"),
    )


class UserNotificationPref(Base):
    """用户通知偏好"""
    __tablename__ = "user_notification_prefs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)  # 哪类事件
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    quiet_hours_start: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 免打扰起始 (0-23)
    quiet_hours_end: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 免打扰结束
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")

    __table_args__ = (
        Index("ix_user_notif_prefs_user_event", "user_id", "event_type", unique=True),
    )


class NotificationLog(Base):
    """发送记录"""
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("notification_channels.id"), nullable=True)
    template_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("notification_templates.id"), nullable=True)
    recipient_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/sent/failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")

    __table_args__ = (
        Index("ix_notification_logs_event", "event_type"),
        Index("ix_notification_logs_status", "status"),
        Index("ix_notification_logs_created", "created_at"),
    )
