from sqlalchemy import Column, String, Text, DateTime, Date, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.db.base import Base


class CalendarEntry(Base):
    """追剧日历条目 — 自动从 Emby 剧集入库生成"""
    __tablename__ = "calendar_entries"

    id = Column(Integer, primary_key=True)
    emby_item_id = Column(String(64), index=True)
    series_name = Column(String(256))
    season_number = Column(Integer)
    episode_number = Column(Integer)
    episode_title = Column(String(256))
    air_date = Column(Date, index=True)
    backdrop_url = Column(String(512))
    overview = Column(Text)
    has_file = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContentSubscription(Base):
    """内容订阅 — 用户订阅剧集/类型以接收通知"""
    __tablename__ = "content_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    emby_item_id = Column(String(64))
    series_name = Column(String(256))
    notification_methods = Column(JSONB, default=list)  # ["webhook", "email"]
    created_at = Column(DateTime, default=datetime.utcnow)