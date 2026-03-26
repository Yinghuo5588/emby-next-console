"""质量盘点 API"""
import asyncio

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_admin
from app.shared.responses import ApiResponse
from . import service

router = APIRouter(prefix="/quality", tags=["quality"])


@router.post("/scan")
async def start_scan(_: dict = Depends(get_current_admin)):
    """触发扫描（异步后台任务）"""
    status = service.get_scan_status()
    if status["running"]:
        return ApiResponse.ok(data=status, message="扫描已在进行中")
    asyncio.create_task(service.scan_all_items())
    return ApiResponse.ok(data={"running": True}, message="扫描已启动")


@router.get("/scan-status")
async def scan_status(_: dict = Depends(get_current_admin)):
    """扫描进度"""
    return ApiResponse.ok(data=service.get_scan_status())


@router.get("/overview")
async def overview(_: dict = Depends(get_current_admin)):
    """聚合统计"""
    data = await service.get_overview()
    return ApiResponse.ok(data=data)


@router.get("/items")
async def items(
    resolution: str | None = Query(None),
    video_range: str | None = Query(None),
    is_ignored: bool | None = Query(None),
    sort: str = Query("name", regex=r"^(name|resolution|video_range|type)$"),
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    _: dict = Depends(get_current_admin),
):
    """媒体列表（分页筛选）"""
    data = await service.get_items(
        resolution=resolution, video_range=video_range,
        is_ignored=is_ignored, sort=sort, page=page, size=size,
    )
    return ApiResponse.ok(data=data)


@router.post("/{item_id}/ignore")
async def ignore_item(item_id: str, _: dict = Depends(get_current_admin)):
    """忽略媒体"""
    await service.set_ignored(item_id, True)
    return ApiResponse.ok(message="已忽略")


@router.delete("/{item_id}/ignore")
async def unignore_item(item_id: str, _: dict = Depends(get_current_admin)):
    """取消忽略"""
    await service.set_ignored(item_id, False)
    return ApiResponse.ok(message="已取消忽略")
