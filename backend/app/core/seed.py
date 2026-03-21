"""
启动时初始化数据
- 创建默认管理员账号（如果不存在）
"""
import logging
from sqlalchemy import select

from app.db.session import AsyncSessionFactory
from app.db.models.user import User
from app.core.security import get_password_hash

logger = logging.getLogger("app.seed")

DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin",
    "display_name": "Admin",
    "role": "admin",
}


async def seed_data():
    """启动时创建默认数据"""
    async with AsyncSessionFactory() as db:
        # 检查是否已有用户
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            logger.info("数据库已有用户，跳过 seed")
            return

        # 创建默认管理员
        admin = User(
            username=DEFAULT_ADMIN["username"],
            hashed_password=get_password_hash(DEFAULT_ADMIN["password"]),
            display_name=DEFAULT_ADMIN["display_name"],
            role=DEFAULT_ADMIN["role"],
            status="active",
            source="local",
        )
        db.add(admin)
        await db.commit()
        logger.info("✅ 已创建默认管理员账号: admin / admin")
