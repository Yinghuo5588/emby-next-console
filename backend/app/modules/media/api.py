from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/libraries")
async def list_libraries(admin=Depends(get_current_user_id)):
    """获取 Emby 媒体库列表"""
    from app.modules.media.service import MediaService
    svc = MediaService()
    return {"success": True, "data": await svc.get_libraries()}


@router.get("/missing-episodes")
async def find_missing_episodes(
    admin=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """扫描所有剧集，找出缺集的系列"""
    from app.modules.media.service import MediaService
    svc = MediaService(db)
    return {"success": True, "data": await svc.find_missing_episodes()}


@router.get("/duplicates")
async def find_duplicates(admin=Depends(get_current_user_id)):
    """检测重复媒体"""
    from app.modules.media.service import MediaService
    svc = MediaService()
    return {"success": True, "data": await svc.find_duplicates()}


@router.get("/tmdb/search")
async def tmdb_search(
    query: str = Query(..., min_length=1),
    type: str = Query("movie", pattern="^(movie|tv)$"),
    page: int = Query(1, ge=1),
    admin=Depends(get_current_user_id),
):
    """搜索 TMDB"""
    from app.modules.media.service import MediaService
    svc = MediaService()
    try:
        results = await svc.search_tmdb(query, type, page)
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tmdb/upcoming")
async def tmdb_upcoming(
    type: str = Query("movie", pattern="^(movie|tv)$"),
    page: int = Query(1, ge=1),
    admin=Depends(get_current_user_id),
):
    """TMDB 即将上映/正在播出"""
    from app.modules.media.service import MediaService
    svc = MediaService()
    try:
        results = await svc.get_upcoming(type, page)
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tmdb/detail/{tmdb_id}")
async def tmdb_detail(
    tmdb_id: int,
    type: str = Query("movie", pattern="^(movie|tv)$"),
    admin=Depends(get_current_user_id),
):
    """TMDB 详情"""
    from app.modules.media.service import MediaService
    svc = MediaService()
    try:
        result = await svc.get_tmdb_detail(tmdb_id, type)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))