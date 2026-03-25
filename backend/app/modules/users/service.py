"""
用户管理 Service — Emby 用户 CRUD + 策略管理 + 模板克隆 + 过期检测
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.emby import emby
from app.core.config import settings
from app.db.models.users_meta import UsersMeta
from app.db.session import AsyncSessionFactory

logger = logging.getLogger("app.users")


# ════════════════════════════════════════════════════════════
# Meta 缓存（内存版，启动后懒加载）
# ════════════════════════════════════════════════════════════
_meta_cache: dict[str, dict] = {}  # user_id -> {expire_date, max_concurrent, is_vip, note, template_name}
_meta_loaded = False


async def _ensure_meta_loaded():
    global _meta_loaded
    if _meta_loaded:
        return
    try:
        async with AsyncSessionFactory() as session:
            from sqlalchemy import select
            result = await session.execute(select(UsersMeta))
            for row in result.scalars().all():
                _meta_cache[row.user_id] = {
                    "expire_date": row.expire_date.isoformat() if row.expire_date else None,
                    "max_concurrent": row.max_concurrent,
                    "is_vip": row.is_vip,
                    "note": row.note or "",
                    "template_name": row.template_name or "",
                }
    except Exception as e:
        logger.warning(f"Failed to load users_meta from DB: {e}")
    _meta_loaded = True


async def _save_meta(user_id: str, data: dict):
    await _ensure_meta_loaded()
    _meta_cache[user_id] = data
    # 异步写 DB
    try:
        async with AsyncSessionFactory() as session:
            from sqlalchemy import select
            result = await session.execute(select(UsersMeta).where(UsersMeta.user_id == user_id))
            row = result.scalar_one_or_none()
            if row is None:
                row = UsersMeta(user_id=user_id)
                session.add(row)
            row.expire_date = datetime.fromisoformat(data["expire_date"]) if data.get("expire_date") else None
            row.max_concurrent = data.get("max_concurrent", 2)
            row.is_vip = data.get("is_vip", False)
            row.note = data.get("note", "")
            row.template_name = data.get("template_name", "")
            await session.commit()
    except Exception as e:
        logger.warning(f"Failed to save meta for {user_id}: {e}")


# ════════════════════════════════════════════════════════════
# 核心函数
# ════════════════════════════════════════════════════════════

async def list_users() -> list[dict]:
    """获取所有用户，合并 meta，自动检测过期"""
    await _ensure_meta_loaded()
    emby_users = await emby.get_users()
    now = datetime.now(timezone.utc)
    result = []

    for u in emby_users:
        uid = u.get("Id", "")
        policy = u.get("Policy", {}) or {}
        meta = _meta_cache.get(uid, {})

        # 过期检测
        expire_str = meta.get("expire_date")
        if expire_str:
            try:
                expire_dt = datetime.fromisoformat(expire_str)
                if expire_dt.tzinfo is None:
                    expire_dt = expire_dt.replace(tzinfo=timezone.utc)
                if expire_dt < now and not policy.get("IsDisabled", False):
                    # 过期了，自动禁用
                    await emby.post(f"/Users/{uid}/Policy", json={"IsDisabled": True})
                    policy["IsDisabled"] = True
                    logger.info(f"Auto-disabled expired user: {u.get('Name', uid)} (expired {expire_str})")
            except Exception as e:
                logger.warning(f"Expire check failed for {uid}: {e}")

        result.append({
            "user_id": uid,
            "name": u.get("Name", ""),
            "is_disabled": policy.get("IsDisabled", False),
            "is_admin": policy.get("IsAdministrator", False),
            "last_login_date": u.get("LastLoginDate", ""),
            "create_date": u.get("DateCreated", ""),
            "primary_image_tag": u.get("PrimaryImageTag", ""),
            "has_password": u.get("HasPassword", True),
            "policy": {
                "enable_all_folders": policy.get("EnableAllFolders", True),
                "enabled_folders": policy.get("EnabledFolders", []),
                "simultaneous_stream_limit": policy.get("SimultaneousStreamLimit", 0),
                "max_parental_rating": policy.get("MaxParentalRating"),
                "enable_content_downloading": policy.get("EnableContentDownloading", True),
                "enable_video_playback_transcoding": policy.get("EnableVideoPlaybackTranscoding", True),
                "enable_remote_access": policy.get("EnableRemoteAccess", True),
            },
            # Meta
            "expire_date": expire_str,
            "max_concurrent": meta.get("max_concurrent", 2),
            "is_vip": meta.get("is_vip", False),
            "note": meta.get("note", ""),
            "template_name": meta.get("template_name", ""),
        })

    # 按最后登录排序（最近的在前）
    result.sort(key=lambda x: x.get("last_login_date", ""), reverse=True)
    return result


async def get_user(user_id: str) -> dict | None:
    """获取单个用户详情"""
    u = await emby.get_user(user_id)
    if not u:
        return None
    await _ensure_meta_loaded()
    policy = u.get("Policy", {}) or {}
    meta = _meta_cache.get(user_id, {})
    return {
        "user_id": u.get("Id", ""),
        "name": u.get("Name", ""),
        "is_disabled": policy.get("IsDisabled", False),
        "is_admin": policy.get("IsAdministrator", False),
        "last_login_date": u.get("LastLoginDate", ""),
        "create_date": u.get("DateCreated", ""),
        "primary_image_tag": u.get("PrimaryImageTag", ""),
        "has_password": u.get("HasPassword", True),
        "policy": policy,
        "expire_date": meta.get("expire_date"),
        "max_concurrent": meta.get("max_concurrent", 2),
        "is_vip": meta.get("is_vip", False),
        "note": meta.get("note", ""),
        "template_name": meta.get("template_name", ""),
    }


async def create_user(
    name: str,
    password: str,
    template_user_id: str | None = None,
    expire_days: int | None = None,
    max_concurrent: int = 2,
    is_vip: bool = False,
    note: str = "",
) -> dict:
    """创建用户，支持模板策略克隆"""
    # 1. 创建基础用户
    resp = await emby.post("/Users/New", json={"Name": name})
    resp.raise_for_status()
    new_user = resp.json()
    user_id = new_user.get("Id", "")

    # 2. 设置密码（管理员直接设置，无需 ResetPassword）
    try:
        pwd_resp = await emby.post(f"/Users/{user_id}/Password", json={
            "Id": user_id,
            "NewPw": password,
        })
        logger.info(f"Password set for {user_id}: status={pwd_resp.status_code}")
    except Exception as e:
        logger.error(f"Set password failed for {user_id}: {e}", exc_info=True)

    # 3. 克隆模板策略（手动复制安全字段，不依赖 CopyFromUserId）
    if template_user_id:
        try:
            tpl = await emby.get_user(template_user_id)
            tpl_policy = tpl.get("Policy", {}) or {}
            tpl_config = tpl.get("Configuration", {}) or {}
            # 复制 Policy 安全字段
            safe_fields = [
                "EnableAllFolders", "EnabledFolders", "EnableLiveTvAccess",
                "EnableContentDownloading", "EnableMediaPlayback",
                "EnableVideoPlaybackTranscoding", "EnableAudioPlaybackTranscoding",
                "EnablePlaybackRemuxing", "EnableContentDeletion",
                "MaxParentalRating", "BlockUnratedItems", "BlockedTags",
                "AccessSchedules", "EnableRemoteAccess", "EnableSharedDeviceControl",
                "EnableSyncTranscoding", "EnableConversionTranscoding",
                "SimultaneousStreamLimit", "AuthenticationProviderId",
            ]
            clone_policy = {}
            for k in safe_fields:
                if k in tpl_policy:
                    clone_policy[k] = tpl_policy[k]
            # 复制 Configuration
            clone_config = {
                "EnableAutoLogin": tpl_config.get("EnableAutoLogin", False),
                "HidePlayedInLatest": tpl_config.get("HidePlayedInLatest", False),
                "RememberAudioSelections": tpl_config.get("RememberAudioSelections", True),
                "RememberSubtitleSelections": tpl_config.get("RememberSubtitleSelections", True),
                "PlayDefaultAudioTrack": tpl_config.get("PlayDefaultAudioTrack", True),
                "SubtitleMode": tpl_config.get("SubtitleMode", "Default"),
                "DisplayMissingEpisodes": tpl_config.get("DisplayMissingEpisodes", False),
            }
            # 排除管理员和禁用
            clone_policy.pop("IsAdministrator", None)
            clone_policy.pop("IsDisabled", None)
            if clone_policy:
                await emby.post(f"/Users/{user_id}/Policy", json=clone_policy)
            if clone_config:
                await emby.post(f"/Users/{user_id}/Policy", json=clone_config)
            logger.info(f"Cloned policy+config from {template_user_id} to {user_id}")
        except Exception as e:
            logger.warning(f"Clone policy failed: {e}", exc_info=True)

    # 4. 设置并发限制（覆盖模板的值）
    if max_concurrent != 0:
        try:
            current_policy = (await emby.get_user(user_id)).get("Policy", {}) or {}
            current_policy["SimultaneousStreamLimit"] = max_concurrent
            await emby.post(f"/Users/{user_id}/Policy", json=current_policy)
        except Exception as e:
            logger.warning(f"Set concurrent limit failed: {e}")

    # 5. 保存 meta
    expire_date = None
    if expire_days and expire_days > 0:
        expire_date = (datetime.now(timezone.utc) + timedelta(days=expire_days)).isoformat()

    template_name = ""
    if template_user_id:
        try:
            tpl = await emby.get_user(template_user_id)
            template_name = tpl.get("Name", "")
        except:
            pass

    await _save_meta(user_id, {
        "expire_date": expire_date,
        "max_concurrent": max_concurrent,
        "is_vip": is_vip,
        "note": note,
        "template_name": template_name,
    })

    return {"user_id": user_id, "name": name}


async def update_user(user_id: str, **kwargs) -> dict:
    """更新用户信息"""
    # 1. 更新基本用户名
    if "name" in kwargs:
        user = await emby.get_user(user_id)
        user["Name"] = kwargs["name"]
        await emby.post(f"/Users/{user_id}", json=user)

    # 2. 更新密码
    if "password" in kwargs and kwargs["password"]:
        try:
            resp = await emby.post(f"/Users/{user_id}/Password", json={
                "Id": user_id,
                "NewPw": kwargs["password"],
            })
            logger.info(f"Password update for {user_id}: status={resp.status_code}")
        except Exception as e:
            logger.error(f"Update password failed for {user_id}: {e}", exc_info=True)

    # 3. 更新策略
    policy_fields = {}
    if "is_disabled" in kwargs:
        policy_fields["IsDisabled"] = kwargs["is_disabled"]
    if "simultaneous_stream_limit" in kwargs:
        policy_fields["SimultaneousStreamLimit"] = kwargs["simultaneous_stream_limit"]
    if "enable_content_downloading" in kwargs:
        policy_fields["EnableContentDownloading"] = kwargs["enable_content_downloading"]
    if "enable_video_transcoding" in kwargs:
        policy_fields["EnableVideoPlaybackTranscoding"] = kwargs["enable_video_transcoding"]
    if "max_parental_rating" in kwargs:
        policy_fields["MaxParentalRating"] = kwargs["max_parental_rating"]
    if "enable_remote_access" in kwargs:
        policy_fields["EnableRemoteAccess"] = kwargs["enable_remote_access"]
    if "enable_all_folders" in kwargs:
        policy_fields["EnableAllFolders"] = kwargs["enable_all_folders"]
    if "enabled_folders" in kwargs:
        policy_fields["EnabledFolders"] = kwargs["enabled_folders"]
    if "block_unrated_items" in kwargs:
        policy_fields["BlockUnratedItems"] = kwargs["block_unrated_items"]

    if policy_fields:
        current = await emby.get_user(user_id)
        current_policy = current.get("Policy", {}) or {}
        current_policy.update(policy_fields)
        await emby.post(f"/Users/{user_id}/Policy", json=current_policy)

    # 4. 更新 meta
    await _ensure_meta_loaded()
    meta = _meta_cache.get(user_id, {}).copy()
    for key in ["expire_date", "max_concurrent", "is_vip", "note"]:
        if key in kwargs and kwargs[key] is not None:
            meta[key] = kwargs[key]
    await _save_meta(user_id, meta)

    return await get_user(user_id)


async def delete_user(user_id: str) -> bool:
    """删除用户"""
    try:
        resp = await emby.delete(f"/Users/{user_id}")
        resp.raise_for_status()
        # 清理 meta
        await _ensure_meta_loaded()
        _meta_cache.pop(user_id, None)
        return True
    except Exception as e:
        logger.warning(f"Delete user {user_id} failed: {e}")
        return False


async def batch_ops(operation: str, user_ids: list[str], **kwargs) -> dict:
    """批量操作"""
    results = {"success": [], "failed": []}

    for uid in user_ids:
        try:
            if operation == "delete":
                await delete_user(uid)
            elif operation == "enable":
                await update_user(uid, is_disabled=False)
            elif operation == "disable":
                await update_user(uid, is_disabled=True)
            elif operation == "renew":
                days = kwargs.get("days", 30)
                new_expire = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
                await update_user(uid, expire_date=new_expire)
            results["success"].append(uid)
        except Exception as e:
            results["failed"].append({"user_id": uid, "error": str(e)})

    return results
