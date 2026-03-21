from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class PlaybackEvent(Base, TimestampMixin):
    __tablename__ = "playback_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    emby_session_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    media_id: Mapped[str] = mapped_column(String(256), nullable=False)
    media_type: Mapped[str] = mapped_column(String(64), nullable=False)
    media_name: Mapped[str] = mapped_column(String(512), nullable=False)
    series_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    season_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    episode_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    play_duration_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="playback_events")

    __table_args__ = (
        Index("ix_playback_events_user_id", "user_id"),
        Index("ix_playback_events_media_id", "media_id"),
        Index("ix_playback_events_started_at", "started_at"),
        Index("ix_playback_events_user_started", "user_id", "started_at"),
        Index("ix_playback_events_mediatype_started", "media_type", "started_at"),
    )


class PlaybackSession(Base, TimestampMixin):
    __tablename__ = "playback_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    emby_session_id: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    media_id: Mapped[str] = mapped_column(String(256), nullable=False)
    media_name: Mapped[str] = mapped_column(String(512), nullable=False)
    client_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="playback_sessions")

    __table_args__ = (
        Index("ix_playback_sessions_user_id", "user_id"),
        Index("ix_playback_sessions_status", "status"),
        Index("ix_playback_sessions_last_seen_at", "last_seen_at"),
    )
