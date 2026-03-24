from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class UsersMeta(Base, TimestampMixin):
    __tablename__ = "users_meta"

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    expire_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_concurrent: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    is_vip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
