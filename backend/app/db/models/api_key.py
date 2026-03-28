from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.db.base import Base


class ApiKey(Base):
    """API 密钥"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    key_hash = Column(String(128), nullable=False, unique=True, index=True)
    key_prefix = Column(String(8), nullable=False)  # 前8位，用于展示
    scopes = Column(String(512), nullable=False, default="read")  # read, write, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
