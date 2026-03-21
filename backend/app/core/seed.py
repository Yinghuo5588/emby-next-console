"""
启动时初始化数据
- 创建默认管理员账号（如果不存在）
"""
import logging
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import AsyncSessionFactory
from app.db.models.user import User
from app.core.security import hash_password

logger = logging.getLogger("app.seed")

DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin",
    "display_name": "Admin",
    "role": "admin",
}

_seed_done = False


async def seed_data():
    """启动时创建默认数据（幂等，全局只执行一次）"""
    global _seed_done
    if _seed_done:
        return

    async with AsyncSessionFactory() as db:
        # 检查是否已有 admin 用户
        result = await db.execute(
            select(User).where(User.username == DEFAULT_ADMIN["username"]).limit(1)
        )
        if result.scalar_one_or_none():
            logger.info("admin 用户已存在，跳过 seed")
            _seed_done = True
            return

        # 创建默认管理员（并发安全）
        admin = User(
            username=DEFAULT_ADMIN["username"],
            hashed_password=hash_password(DEFAULT_ADMIN["password"]),
            display_name=DEFAULT_ADMIN["display_name"],
            role=DEFAULT_ADMIN["role"],
            status="active",
            source="local",
        )
        db.add(admin)
        try:
            await db.commit()
            logger.info("✅ 已创建默认管理员账号: admin / admin")
        except IntegrityError:
            await db.rollback()
            logger.info("admin 用户已由其他进程创建，跳过")
        _seed_done = True
