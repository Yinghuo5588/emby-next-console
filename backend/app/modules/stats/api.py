"""
统计 API V3 — 每个端点只回答一个问题

端点:
  /api/v1/stats/overview        → 总览核心指标
  /api/v1/stats/trend           → 趋势（播放时长，按天/周/月）
  /api/v1/stats/top-content     → Top 内容
  /api/v1/stats/top-users       → Top 用户
  /api/v1/stats/content-rankings → 内容排行（筛选+分页）
  /api/v1/stats/content/{id}    → 单个内容详情
  /api/v1/stats/user-rankings   → 用户排行（分页）
  /api/v1/stats/users/{id}      → 单个用户画像
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional


from app.shared.responses import ApiResponse
from . import service

router = APIRouter(prefix="/stats", tags=["stats"])


# ════════════════════════════════════════════════════════════
# 总览页
# ════════════════════════════════════════════════════════════

@router.get("/overview")
async def overview(
    period: str = Query("30d", regex=r"^(7d|30d|90d|all)$"),
    
):
    """核心指标：媒体总量 / 播放总次数 / 活跃用户 / 总时长（按 period）"""
    data = await service.get_overview(period=period)
    return ApiResponse.ok(data=data)


@router.get("/trend")
async def trend(
    period: str = Query("30d", regex=r"^(7d|30d|90d|all)$"),
    
):
    """播放趋势：播放时长"""
    data = await service.get_trend_by_period(period)
    return ApiResponse.ok(data=data)


@router.get("/top-content")
async def top_content(
    limit: int = Query(5, ge=1, le=20),
    period: str = Query("7d", regex=r"^(7d|30d|90d|all)$"),
    
):
    """Top 内容（按时长排）"""
    data = await service.get_top_content(limit=limit, period=period)
    return ApiResponse.ok(data=data)


@router.get("/top-users")
async def top_users(
    limit: int = Query(5, ge=1, le=20),
    period: str = Query("7d", regex=r"^(7d|30d|90d|all)$"),
    
):
    """Top 用户（按时长排）"""
    data = await service.get_top_users_ranked(limit=limit, period=period)
    return ApiResponse.ok(data=data)


# ════════════════════════════════════════════════════════════
# 内容分析页
# ════════════════════════════════════════════════════════════

@router.get("/content-rankings")
async def content_rankings(
    type: str = Query("all", regex=r"^(all|movie|series)$"),
    period: str = Query("30d", regex=r"^(30d|90d|all)$"),
    sort: str = Query("duration", regex=r"^(duration|count)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user_id: str = Query(None),
    
):
    """内容排行榜（筛选+分页）"""
    data = await service.get_content_rankings(
        content_type=type, period=period, sort=sort, page=page, size=size, user_id=user_id
    )
    return ApiResponse.ok(data=data)


@router.get("/content/{item_id}")
async def content_detail(
    item_id: str,
    
):
    """单个内容详情：趋势 + 观看用户 + 分季"""
    data = await service.get_content_detail(item_id)
    return ApiResponse.ok(data=data)


# ════════════════════════════════════════════════════════════
# 用户分析页
# ════════════════════════════════════════════════════════════

@router.get("/user-rankings")
async def user_rankings(
    period: str = Query("30d", regex=r"^(30d|90d|all)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    
):
    """用户排行榜（分页）"""
    data = await service.get_user_rankings(period=period, page=page, size=size)
    return ApiResponse.ok(data=data)


@router.get("/users/{user_id}")
async def user_detail(
    user_id: str,
    period: str = Query("7d", regex=r"^(7d|30d|90d|all)$"),
    
):
    """单个用户画像：KPI + 偏好 + 趋势 + 热力图 + 设备（按 period 筛选）"""
    data = await service.get_user_detail(user_id, period=period)
    return ApiResponse.ok(data=data)


@router.get("/search-users")
async def search_users(
    q: str = Query(..., min_length=1),
    
):
    """搜索用户（按用户名模糊匹配）"""
    user_map = await service._get_user_map()
    results = [
        {"user_id": uid, "username": name}
        for uid, name in user_map.items()
        if q.lower() in name.lower()
    ]
    return ApiResponse.ok(data=results[:20])


# ════════════════════════════════════════════════════════════
# 总览页额外数据
# ════════════════════════════════════════════════════════════

@router.get("/heatmap")
async def heatmap(
    period: str = Query("30d", regex=r"^(30d|90d|all)$"),
    
):
    """24×7 热力图：观影生物钟"""
    data = await service.get_heatmap(period)
    return ApiResponse.ok(data=data)


@router.get("/device-dist")
async def device_dist(
    period: str = Query("30d", regex=r"^(30d|90d|all)$"),
    type: str = Query("client", regex=r"^(client|hardware)$"),
    
):
    """设备分布 — client=软件(客户端) / hardware=硬件(设备型号)"""
    data = await service.get_device_dist(period, type)
    return ApiResponse.ok(data=data)

