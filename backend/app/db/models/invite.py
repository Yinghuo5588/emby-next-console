from __future__ import annotations
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class InviteCode(Base, TimestampMixin):
    __tablename__ = "invite_codes"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    template_emby_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="权限继承源Emby用户ID")
    permission_template_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("permission_templates.id", ondelete="SET NULL"), nullable=True)
    max_uses: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    concurrent_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")  # active/used/expired/disabled
    
    __table_args__ = (
        Index("ix_invite_codes_code", "code"),
        Index("ix_invite_codes_status", "status"),
        Index("ix_invite_codes_created_by", "created_by"),
    )


class InviteUsage(Base):
    __tablename__ = "invite_usages"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    invite_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("invite_codes.id", ondelete="CASCADE"), nullable=False)
    emby_user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    __table_args__ = (
        Index("ix_invite_usages_invite_id", "invite_id"),
    )


class PermissionTemplate(Base, TimestampMixin):
    __tablename__ = "permission_templates"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    library_access: Mapped[list | None] = mapped_column(JSONB, nullable=True, comment="允许的媒体库ID列表")
    policy_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="Emby Policy配置")
    configuration_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="Emby Configuration")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    __table_args__ = (
        Index("ix_permission_templates_name", "name"),
    )


class UserOverride(Base):
    __tablename__ = "user_overrides"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    emby_user_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    concurrent_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_bitrate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allow_transcode: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    client_blacklist: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    __table_args__ = (
        Index("ix_user_overrides_emby_user_id", "emby_user_id"),
    )