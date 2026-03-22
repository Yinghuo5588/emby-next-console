from fastapi import APIRouter, Depends, Query
from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/admin/poster", tags=["poster"])


@router.get("/templates")
async def list_templates(
    db: AsyncSessionDep,
    admin=Depends(get_current_user_id),
):
    from app.modules.poster.service import PosterService
    return {"success": True, "data": await PosterService(db).list_templates()}


@router.post("/templates")
async def create_template(
    db: AsyncSessionDep,
    data: dict,
    admin=Depends(get_current_user_id),
):
    from app.modules.poster.service import PosterService
    return {"success": True, "data": await PosterService(db).create_template(data)}


@router.post("/generate")
async def generate_poster(
    db: AsyncSessionDep,
    data: dict,
    admin=Depends(get_current_user_id),
):
    from app.modules.poster.service import PosterService
    return {"success": True, "data": await PosterService(db).generate_poster(data)}


@router.get("/generated")
async def list_generated(
    db: AsyncSessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin=Depends(get_current_user_id),
):
    from app.modules.poster.service import PosterService
    return {"success": True, "data": await PosterService(db).list_generated(page, page_size)}


@router.get("/generated/{poster_id}/html")
async def get_poster_html(
    poster_id: int,
    db: AsyncSessionDep,
    admin=Depends(get_current_user_id),
):
    from app.modules.poster.service import PosterService
    poster = await PosterService(db).get_poster(poster_id)
    if not poster or not poster.get("html_content"):
        return {"success": False, "data": None}
    return {"success": True, "data": {"html": poster["html_content"]}}
