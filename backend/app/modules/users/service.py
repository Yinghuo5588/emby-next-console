import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.emby_data import data as emby_data
from app.core.exceptions import NotFoundError
from app.db.models.invite import UserOverride
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


def _emby_user_to_list_item(u: dict, override: dict | None = None) -> UserListItem:
    policy = u.get("Policy", {})
    return UserListItem(
        user_id=u["Id"],
        username=u["Name"],
        display_name=u.get("Name"),
        role="admin" if policy.get("IsAdministrator") else "user",
        status="disabled" if policy.get("IsDisabled") else "active",
        expire_at=override.get("expire_at") if override else None,
        is_vip=override.get("is_vip", False) if override else False,
        created_at=_parse_date(u.get("DateCreated")) or datetime.now(tz_cn),
        max_concurrent=override.get("max_concurrent") if override else None,
        note=override.get("note") if override else None,
    )


def _emby_user_to_detail(u: dict, override: dict | None = None) -> UserDetail:
    policy = u.get("Policy", {})
    return UserDetail(
        user_id=u["Id"],
        username=u["Name"],
        display_name=u.get("Name"),
        role="admin" if policy.get("IsAdministrator") else "user",
        status="disabled" if policy.get("IsDisabled") else "active",
        expire_at=override.get("expire_at") if override else None,
        is_vip=override.get("is_vip", False) if override else False,
        created_at=_parse_date(u.get("DateCreated")) or datetime.now(tz_cn),
        max_concurrent=override.get("max_concurrent") if override else None,
        note=override.get("note") if override else None,
        emby_user_id=u["Id"],
        concurrent_limit=override.get("concurrent_limit") if override else None,
        max_bitrate=override.get("max_bitrate") if override else None,
        allow_transcode=override.get("allow_transcode") if override else None,
        client_blacklist=override.get("client_blacklist") if override else None,
    )


class UsersService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_overrides_map(self) -> dict[str, dict]:
        """批量获取所有 UserOverride，返回 emby_user_id -> override dict"""
        result = await self.db.execute(select(UserOverride))
        overrides = {}
        for o in result.scalars().all():
            overrides[o.emby_user_id] = {
                "expire_at": o.expires_at,
                "concurrent_limit": o.concurrent_limit,
                "max_bitrate": o.max_bitrate,
                "allow_transcode": o.allow_transcode,
                "client_blacklist": o.client_blacklist,
                "note": o.note,
                "max_concurrent": o.concurrent_limit,  # 别名兼容
                "is_vip": False,  # UserOverride 暂无 is_vip，预留
            }
        return overrides

    async def _check_expired_users(self, overrides: dict[str, dict]) -> None:
        """检测并自动禁用过期用户"""
        now = datetime.now(timezone.utc)
        from app.core.emby_users import EmbyUserService
        emby_svc = EmbyUserService()
        for uid, ov in overrides.items():
            exp = ov.get("expire_at")
            if exp and isinstance(exp, datetime) and exp < now:
                try:
                    policy = await emby_svc.get_user_policy(uid)
                    if not policy.get("IsDisabled"):
                        policy["IsDisabled"] = True
                        await emby_svc.update_user_policy(uid, policy)
                        logger.info(f"用户 {uid} 已过期，自动禁用")
                except Exception as e:
                    logger.warning(f"自动禁用过期用户 {uid} 失败: {e}")

    async def list_users(self, page: int = 1, page_size: int = 20) -> UserListResponse:
        try:
            emby_users = await emby_data.get_users()
            overrides = await self._get_overrides_map()
            await self._check_expired_users(overrides)

            emby_users.sort(key=lambda u: u.get("Name", "").lower())
            total = len(emby_users)
            start = (page - 1) * page_size
            items = emby_users[start : start + page_size]
            return UserListResponse(
                items=[_emby_user_to_list_item(u, overrides.get(u["Id"])) for u in items],
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
            overrides = await self._get_overrides_map()
            return _emby_user_to_detail(u, overrides.get(user_id))
        except Exception as e:
            logger.error("获取用户 %s 失败: %s", user_id, e)
            raise NotFoundError(f"User {user_id} not found")

    async def update_user(self, user_id: str, body: UserUpdateRequest) -> UserDetail:
        # 更新 UserOverride
        result = await self.db.execute(select(UserOverride).where(UserOverride.emby_user_id == user_id))
        override = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if override:
            if body.expire_at is not None: override.expires_at = body.expire_at
            if body.max_concurrent is not None: override.concurrent_limit = body.max_concurrent
            if body.note is not None: override.note = body.note
            override.updated_at = now
        else:
            override = UserOverride(
                emby_user_id=user_id,
                expires_at=body.expire_at,
                concurrent_limit=body.max_concurrent,
                note=body.note,
                updated_at=now,
            )
            self.db.add(override)
        await self.db.commit()

        # 如果设了 is_vip，暂存在 override.note 前缀标记（后续可加字段）
        # 返回更新后的用户
        return await self.get_user(user_id)

    async def batch_operations(
        self,
        action: str,
        user_ids: list[str],
        **kwargs,
    ) -> dict:
        """批量操作：delete / enable / disable / renew / apply_template"""
        from app.core.emby_users import EmbyUserService
        from datetime import timedelta

        emby_svc = EmbyUserService()
        now = datetime.now(timezone.utc)
        results = {"success": [], "failed": []}

        if action == "delete":
            for uid in user_ids:
                try:
                    await emby_svc.delete_emby_user(uid)
                    # 删除本地 override
                    result = await self.db.execute(select(UserOverride).where(UserOverride.emby_user_id == uid))
                    ov = result.scalar_one_or_none()
                    if ov:
                        await self.db.delete(ov)
                    results["success"].append(uid)
                except Exception as e:
                    results["failed"].append({"user_id": uid, "error": str(e)})

        elif action in ("enable", "disable"):
            is_disabled = action == "disable"
            for uid in user_ids:
                try:
                    policy = await emby_svc.get_user_policy(uid)
                    policy["IsDisabled"] = is_disabled
                    await emby_svc.update_user_policy(uid, policy)
                    results["success"].append(uid)
                except Exception as e:
                    results["failed"].append({"user_id": uid, "error": str(e)})

        elif action == "renew":
            days = kwargs.get("days", 30)
            expires_at = kwargs.get("expires_at")
            for uid in user_ids:
                try:
                    result = await self.db.execute(select(UserOverride).where(UserOverride.emby_user_id == uid))
                    ov = result.scalar_one_or_none()
                    new_exp = expires_at or (now + timedelta(days=days))
                    if ov:
                        ov.expires_at = new_exp
                        ov.updated_at = now
                    else:
                        ov = UserOverride(emby_user_id=uid, expires_at=new_exp, updated_at=now)
                        self.db.add(ov)
                    # 如果用户被禁用且续期了未来时间，重新启用
                    if new_exp > now:
                        try:
                            policy = await emby_svc.get_user_policy(uid)
                            if policy.get("IsDisabled"):
                                policy["IsDisabled"] = False
                                await emby_svc.update_user_policy(uid, policy)
                        except Exception:
                            pass
                    results["success"].append(uid)
                except Exception as e:
                    results["failed"].append({"user_id": uid, "error": str(e)})

        elif action == "apply_template":
            template_id = kwargs.get("template_id")
            if not template_id:
                return {"success": [], "failed": [{"error": "缺少 template_id"}]}
            # 获取模板策略
            try:
                template_policy = await emby_svc.get_user_policy(template_id)
            except Exception as e:
                return {"success": [], "failed": [{"error": f"获取模板失败: {e}"}]}
            # 复制策略字段（排除危险字段）
            DANGEROUS = {"IsAdministrator", "IsDisabled", "IsHidden", "EnableLiveTvAccess", "EnableLiveTvManagement"}
            safe_policy = {k: v for k, v in template_policy.items() if k not in DANGEROUS}
            for uid in user_ids:
                try:
                    policy = await emby_svc.get_user_policy(uid)
                    policy.update(safe_policy)
                    await emby_svc.update_user_policy(uid, policy)
                    results["success"].append(uid)
                except Exception as e:
                    results["failed"].append({"user_id": uid, "error": str(e)})

        await self.db.commit()
        return results
