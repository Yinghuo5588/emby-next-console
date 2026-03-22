from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_admin
from app.modules.templates.schemas import TemplateCreateRequest, TemplateResponse, TemplateListResponse
from app.modules.templates.service import TemplateService

router = APIRouter(prefix="/admin/templates", tags=["templates"])


@router.post("", response_model=TemplateResponse)
async def create_template(
    req: TemplateCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    svc = TemplateService(db)
    return await svc.create(req)


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    svc = TemplateService(db)
    items, total = await svc.list(page=page, page_size=page_size)
    return TemplateListResponse(items=items, total=total)


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    svc = TemplateService(db)
    tpl = await svc.get(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    return tpl


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    req: TemplateCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    svc = TemplateService(db)
    await svc.update(template_id, req)
    tpl = await svc.get(template_id)
    return tpl


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    svc = TemplateService(db)
    await svc.delete(template_id)
    return {"success": True}
