import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.emby_data import data as emby_data
from app.core.exceptions import NotFoundError
from .schemas import UserDetail, UserListItem, UserListResponse, UserUpdateRequest
from app.db.models.user import User, UserProfile

logger = logging.getLogger("app.users")

tz_cn = timezone.utc


def _parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _emby_user_to_list_item(u: dict) -> UserListItem:
    policy = u.get("Policy", {})
    return UserListItem(
        user_id=u["Id"],
        username=u["Name"],
        display_name=u.get("Name"),
        role="admin" if policy.get("IsAdministrator") else "user",
        status="disabled" if policy.get("IsDisabled") else "active",
        expire_at=None,  # 需要本地 users_meta 表扩展
        is_vip=False,
        created_at=_parse_date(u.get("DateCreated")) or datetime.now(tz_cn),
    )


def _emby_user_to_detail(u: dict) -> UserDetail:
    policy = u.get("Policy", {})
    return UserDetail(
        user_id=u["Id"],
        username=u["Name"],
        display_name=u.get("Name"),
        role="admin" if policy.get("IsAdministrator") else "user",
        status="disabled" if policy.get("IsDisabled") else "active",
        expire_at=None,
        is_vip=False,
        created_at=_parse_date(u.get("DateCreated")) or datetime.now(tz_cn),
        note=None,
        max_concurrent=None,
        emby_user_id=u["Id"],
    )


class UsersService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(self, page: int = 1, page_size: int = 20) -> UserListResponse:
        try:
            emby_users = await emby_data.get_users()
            # 排序
            emby_users.sort(key=lambda u: u.get("Name", "").lower())
            total = len(emby_users)
            # 分页
            start = (page - 1) * page_size
            items = emby_users[start : start + page_size]
            return UserListResponse(
                items=[_emby_user_to_list_item(u) for u in items],
                total=total,
                page=page,
                page_size=page_size,
            )
        except Exception as e:
            logger.error("获取用户列表失败: %s", e)
            return UserListResponse(items=[], total=0, page=page, page_size=page_size)

    async def get_user(self, user_id: str) -> UserDetail:
        try:
            u = await emby_data.get_user(user_id)
            return _emby_user_to_detail(u)
        except Exception as e:
            logger.error("获取用户 %s 失败: %s", user_id, e)
            raise NotFoundError(f"User {user_id} not found")

    async def update_user(self, user_id: str, body: UserUpdateRequest) -> UserDetail:
        # 暂不支持写操作（需要扩展本地数据库）
        raise NotImplementedError("用户写操作待实现")

    async def create_user(self, username: str, password: str | None = None, note: str | None = None, 
                      expires_days: int | None = None, concurrent_limit: int | None = None,
                      template_emby_user_id: str | None = None) -> dict:
        """手动创建 Emby 用户 + 本地记录"""
        from app.core.emby_users import EmbyUserService
        from datetime import datetime, timedelta, timezone
        
        emby_svc = EmbyUserService()
        
        # 1. 创建 Emby 用户
        emby_user = await emby_svc.create_emby_user(username, password)
        emby_user_id = emby_user["Id"]
        
        # 2. 如果有模板用户，复制其权限
        if template_emby_user_id:
            template_policy = await emby_svc.get_user_policy(template_emby_user_id)
            await emby_svc.update_user_policy(emby_user_id, template_policy)
        
        # 3. 创建本地用户记录
        user = User(
            emby_user_id=emby_user_id,
            username=username,
            role="user",
            status="active",
            source="manual",
        )
        self.db.add(user)
        await self.db.flush()
        
        # 4. 创建 profile
        expire_at = None
        if expires_days and expires_days > 0:
            expire_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
        
        profile = UserProfile(
            user_id=user.id,
            expire_at=expire_at,
            note=note,
            max_concurrent=concurrent_limit,
        )
        self.db.add(profile)
        await self.db.commit()
        
        return {"user_id": user.id, "emby_user_id": emby_user_id, "username": username}
