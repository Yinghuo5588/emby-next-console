from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.db.base import Base


class NotifyDestination(Base):
    """Webhook 推送目标"""
    __tablename__ = "notify_destinations"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    url = Column(String(512), nullable=False)
    secret = Column(String(256), nullable=True)
    events = Column(JSONB, nullable=False, default=list)  # ["content.new", "risk.alert", ...]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_sent_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
