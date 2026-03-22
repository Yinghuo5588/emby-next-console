from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy import select

from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id, get_current_admin
from app.shared.responses import ApiResponse
from .schemas import UserDetail, UserListResponse, UserUpdateRequest
from .service import UsersService
from app.db.models.invite import UserOverride

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=ApiResponse[UserListResponse])
async def list_users(
    db: AsyncSessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: str = Depends(get_current_user_id),
):
    return ApiResponse.ok(data=await UsersService(db).list_users(page, page_size))


@router.get("/{user_id}", response_model=ApiResponse[UserDetail])
async def get_user(user_id: str, db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await UsersService(db).get_user(user_id))


@router.patch("/{user_id}", response_model=ApiResponse[UserDetail])
async def update_user(user_id: str, body: UserUpdateRequest, db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await UsersService(db).update_user(user_id, body))


# 添加到文件末尾（在现有路由之后）

@router.post("/create")
async def create_user(
    username: str = Body(...),
    password: str | None = Body(None),
    note: str | None = Body(None),
    expires_days: int | None = Body(None),
    concurrent_limit: int | None = Body(None),
    template_emby_user_id: str | None = Body(None),
    db: AsyncSessionDep,
    admin=Depends(get_current_admin),
):
    """手动创建 Emby 用户"""
    from app.modules.users.service import UsersService
    svc = UsersService(db)
    try:
        result = await svc.create_user(
            username=username,
            password=password,
            note=note,
            expires_days=expires_days,
            concurrent_limit=concurrent_limit,
            template_emby_user_id=template_emby_user_id,
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/permissions")
async def get_user_permissions(user_id: str, admin=Depends(get_current_admin)):
    """从 Emby 获取用户库权限"""
    from app.core.emby_users import EmbyUserService
    svc = EmbyUserService()
    try:
        policy = await svc.get_user_policy(user_id)
        config = await svc.get_user_configuration(user_id)
        return {"success": True, "data": {"policy": policy, "configuration": config}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}/permissions")
async def update_user_permissions(
    user_id: str,
    policy: dict = Body(...),
    admin=Depends(get_current_admin),
):
    """更新用户库权限（写入 Emby）"""
    from app.core.emby_users import EmbyUserService
    svc = EmbyUserService()
    try:
        await svc.update_user_policy(user_id, policy)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/override")
async def get_user_override(user_id: str, db: AsyncSessionDep, admin=Depends(get_current_admin)):
    """获取用户级覆盖配置"""
    result = await db.execute(select(UserOverride).where(UserOverride.emby_user_id == user_id))
    override = result.scalar_one_or_none()
    return {"success": True, "data": override}


@router.put("/{user_id}/override")
async def upsert_user_override(
    user_id: str,
    concurrent_limit: int | None = Body(None),
    max_bitrate: int | None = Body(None),
    allow_transcode: bool | None = Body(None),
    client_blacklist: list[str] | None = Body(None),
    note: str | None = Body(None),
    db: AsyncSessionDep,
    admin=Depends(get_current_admin),
):
    """更新用户级覆盖配置"""
    from app.db.models.invite import UserOverride
    from datetime import datetime, timezone
    
    result = await db.execute(select(UserOverride).where(UserOverride.emby_user_id == user_id))
    override = result.scalar_one_or_none()
    
    if override:
        if concurrent_limit is not None: override.concurrent_limit = concurrent_limit
        if max_bitrate is not None: override.max_bitrate = max_bitrate
        if allow_transcode is not None: override.allow_transcode = allow_transcode
        if client_blacklist is not None: override.client_blacklist = client_blacklist
        if note is not None: override.note = note
        override.updated_at = datetime.now(timezone.utc)
    else:
        override = UserOverride(
            emby_user_id=user_id,
            concurrent_limit=concurrent_limit,
            max_bitrate=max_bitrate,
            allow_transcode=allow_transcode,
            client_blacklist=client_blacklist,
            note=note,
            updated_at=datetime.now(timezone.utc),
        )
        db.add(override)
    
    await db.commit()
    return {"success": True}


@router.post("/{user_id}/force-logout")
async def force_logout_user(user_id: str, admin=Depends(get_current_admin)):
    """强制下线用户"""
    from app.core.emby_users import EmbyUserService
    svc = EmbyUserService()
    try:
        await svc.force_logout(user_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
