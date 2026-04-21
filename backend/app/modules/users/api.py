"""
用户管理 API — Emby 管理员操作用户
"""
from fastapi import APIRouter, Depends, UploadFile, File
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


@router.get("/libraries")
async def list_library_folders(_: dict = Depends(get_current_admin)):
    """获取媒体库列表"""
    folders = await emby.get_library_virtual_folders()
    result = [{"value": f.get("Guid", f.get("Name", "")), "label": f.get("Name", "")} for f in folders]
    return ApiResponse.ok(data=result)


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
    )
    return ApiResponse.ok(data=data)


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
    # Emby 没有头像 → 返回 404，前端显示首字母 fallback
    return Response(status_code=404)


@router.post("/{user_id}/avatar")
async def upload_avatar(user_id: str, file: UploadFile = File(...), _: dict = Depends(get_current_admin)):
    """上传用户头像"""
    # 校验文件类型
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        return ApiResponse.error("仅支持 JPG/PNG/GIF/WEBP 格式")

    # 校验文件大小（最大 5MB）
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        return ApiResponse.error("图片大小不能超过 5MB")

    # 上传到 Emby
    ok = await emby.upload_user_image(user_id, data, file.content_type)
    if not ok:
        return ApiResponse.error("上传失败，请检查 Emby 连接")
    return ApiResponse.ok(message="头像上传成功")


@router.delete("/{user_id}/avatar")
async def delete_avatar(user_id: str, _: dict = Depends(get_current_admin)):
    """删除用户头像"""
    ok = await emby.delete_user_image(user_id)
    if not ok:
        return ApiResponse.error("删除失败")
    return ApiResponse.ok(message="头像已删除")
