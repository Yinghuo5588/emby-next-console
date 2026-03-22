from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
from app.core.emby import emby
from app.core.security import create_access_token
from datetime import timedelta


class PortalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, username: str, password: str) -> dict:
        """通过 Emby 认证，返回 JWT token"""
        # 1. 调用 Emby 登录接口
        auth_result = await emby.auth_with_password(username, password)
        if not auth_result:
            raise ValueError("用户名或密码错误")

        emby_user_id = auth_result.get("User", {}).get("Id")
        if not emby_user_id:
            raise ValueError("Emby 认证失败")

        # 2. 查找本地用户记录
        result = await self.db.execute(
            select(User).where(User.emby_user_id == emby_user_id)
        )
        user = result.scalar_one_or_none()

        # 3. 如果本地没有记录，同步创建
        if not user:
            user = User(
                emby_user_id=emby_user_id,
                username=username,
                role="user",  # 默认用户角色
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

        # 4. 生成 portal token（使用 emby_user_id 作为 sub）
        token = create_access_token(
            subject=emby_user_id,
            expires_delta=timedelta(days=7),
            type="portal"
        )

        return {
            "token": token,
            "user": {
                "emby_user_id": emby_user_id,
                "username": username,
                "is_admin": user.role == "admin",  # 根据角色判断是否为管理员
            },
        }

    async def get_me(self, emby_user_id: str) -> dict:
        """获取用户信息（合并本地 + Emby）"""
        # 本地信息
        result = await self.db.execute(
            select(User).where(User.emby_user_id == emby_user_id)
        )
        user = result.scalar_one_or_none()

        # Emby 信息
        emby_user = await emby.get_user(emby_user_id)

        return {
            "emby_user_id": emby_user_id,
            "username": user.username if user else (emby_user or {}).get("Name", ""),
            "display_name": (emby_user or {}).get("Name", ""),
            "is_admin": user.role == "admin" if user else False,
            "avatar": emby.get_user_image_url(emby_user_id) if emby_user else None,
        }

    async def get_stats(self, emby_user_id: str) -> dict:
        """获取用户观看统计"""
        try:
            sessions = await emby.get_sessions()
            # 筛选该用户的活跃会话
            user_sessions = [s for s in sessions if s.get("UserId") == emby_user_id]
            
            return {
                "active_sessions": len(user_sessions),
                "now_playing": [
                    {
                        "device": s.get("Client", ""),
                        "item": s.get("NowPlayingItem", {}).get("Name", ""),
                    }
                    for s in user_sessions
                    if s.get("NowPlayingItem")
                ],
            }
        except Exception:
            return {"active_sessions": 0, "now_playing": []}

    async def update_profile(self, emby_user_id: str, **kwargs):
        """更新用户资料"""
        from app.db.models.user import UserProfile
        
        result = await self.db.execute(
            select(User).where(User.emby_user_id == emby_user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            # 获取或创建用户资料
            profile_result = await self.db.execute(
                select(UserProfile).where(UserProfile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()
            
            if not profile:
                profile = UserProfile(user_id=user.id)
                self.db.add(profile)
            
            if kwargs.get("display_name"):
                user.display_name = kwargs["display_name"]
            if kwargs.get("avatar_url"):
                profile.avatar_url = kwargs["avatar_url"]
            
            await self.db.commit()