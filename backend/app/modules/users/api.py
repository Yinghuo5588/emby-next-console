"""
用户管理 API — Emby 管理员操作用户
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.dependencies import get_current_admin
from app.core.emby import emby
from app.shared.responses import ApiResponse
from . import service

router = APIRouter(prefix="/manage/users", tags=["users"])


class CreateUserRequest(BaseModel):
    name: str
    password: str
    template_user_id: str | None = None
    expire_days: int | None = None
    max_concurrent: int = 2
    is_vip: bool = False
    note: str = ""


class UpdateUserRequest(BaseModel):
    name: str | None = None
    password: str | None = None
    is_disabled: bool | None = None
    simultaneous_stream_limit: int | None = None
    enable_content_downloading: bool | None = None
    enable_video_transcoding: bool | None = None
    max_parental_rating: int | None = None
    enable_remote_access: bool | None = None
    enable_all_folders: bool | None = None
    enabled_folders: list[str] | None = None
    block_unrated_items: list[str] | None = None
    expire_date: str | None = None
    max_concurrent: int | None = None
    is_vip: bool | None = None
    note: str | None = None


class BatchRequest(BaseModel):
    operation: str  # delete | enable | disable | renew
    user_ids: list[str]
    days: int | None = 30


@router.get("")
async def list_users(_: dict = Depends(get_current_admin)):
    """用户列表（合并 Emby + meta，自动检测过期）"""
    data = await service.list_users()
    return ApiResponse.ok(data=data)


@router.get("/{user_id}")
async def get_user(user_id: str, _: dict = Depends(get_current_admin)):
    """单个用户详情"""
    data = await service.get_user(user_id)
    if not data:
        return ApiResponse.error("用户不存在")
    return ApiResponse.ok(data=data)


@router.post("")
async def create_user(body: CreateUserRequest, _: dict = Depends(get_current_admin)):
    """创建用户（支持模板克隆）"""
    data = await service.create_user(
        name=body.name,
        password=body.password,
        template_user_id=body.template_user_id,
        expire_days=body.expire_days,
        max_concurrent=body.max_concurrent,
        is_vip=body.is_vip,
        note=body.note,
    )
    return ApiResponse.ok(data=data, message="创建成功")


@router.put("/{user_id}")
async def update_user(user_id: str, body: UpdateUserRequest, _: dict = Depends(get_current_admin)):
    """更新用户"""
    data = await service.update_user(user_id, **body.model_dump(exclude_none=True))
    return ApiResponse.ok(data=data, message="更新成功")


@router.delete("/{user_id}")
async def delete_user(user_id: str, _: dict = Depends(get_current_admin)):
    """删除用户"""
    ok = await service.delete_user(user_id)
    if not ok:
        return ApiResponse.error("删除失败")
    return ApiResponse.ok(message="删除成功")


@router.post("/batch")
async def batch_ops(body: BatchRequest, _: dict = Depends(get_current_admin)):
    """批量操作"""
    data = await service.batch_ops(
        operation=body.operation,
        user_ids=body.user_ids,
        days=body.days,
        template_user_id=body.template_user_id,
    )
    return ApiResponse.ok(data=data)


@router.get("/libraries")
async def list_library_folders(_: dict = Depends(get_current_admin)):
    """获取媒体库列表"""
    folders = await emby.get_library_virtual_folders()
    result = [{"value": f.get("Guid", f.get("Name", "")), "label": f.get("Name", "")} for f in folders]
    return ApiResponse.ok(data=result)


@router.get("/{user_id}/avatar")
async def get_avatar(user_id: str):
    """代理用户头像"""
    from fastapi.responses import Response
    import httpx

    host = emby._host
    api_key = emby._api_key
    url = f"{host}/emby/Users/{user_id}/Images/Primary?quality=90"
    headers = {"X-Emby-Token": api_key}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return Response(content=resp.content, media_type=resp.headers.get("content-type", "image/jpeg"))
    except Exception:
        pass
    # 默认返回空 1x1 透明 PNG
    import base64
    empty_png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    return Response(content=empty_png, media_type="image/png")
