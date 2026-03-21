from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.playback import PlaybackEvent, PlaybackSession
    from app.db.models.risk import RiskEvent
    from app.db.models.notification import Notification
    from app.db.models.system import AuditLog


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    emby_user_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    username: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    hashed_password: Mapped[str | None] = mapped_column(String(256), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="user")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="local")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile: Mapped[UserProfile] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    playback_events: Mapped[list[PlaybackEvent]] = relationship(back_populates="user")
    playback_sessions: Mapped[list[PlaybackSession]] = relationship(back_populates="user")
    risk_events: Mapped[list[RiskEvent]] = relationship(back_populates="user")
    notifications: Mapped[list[Notification]] = relationship(back_populates="user")
    audit_logs: Mapped[list[AuditLog]] = relationship(back_populates="actor_user")

    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_status", "status"),
    )


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    expire_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_vip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_concurrent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tags_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")

    __table_args__ = (
        Index("ix_user_profiles_expire_at", "expire_at"),
        Index("ix_user_profiles_is_vip", "is_vip"),
    )
