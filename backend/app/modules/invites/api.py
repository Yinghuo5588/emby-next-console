from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_admin
from app.modules.invites.schemas import InviteCreateRequest, InviteCodeResponse, InviteStatsResponse, InviteListResponse
from app.modules.invites.service import InviteService

router = APIRouter(prefix="/admin/invites", tags=["invites"])


@router.post("", response_model=InviteCodeResponse)
async def create_invite(
    req: InviteCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    svc = InviteService(db)
    try:
        invite = await svc.create(req, creator_id=admin.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return invite


@router.get("", response_model=InviteListResponse)
async def list_invites(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    svc = InviteService(db)
    items, total = await svc.list(status=status, page=page, page_size=page_size)
    return InviteListResponse(items=items, total=total)


@router.get("/stats", response_model=InviteStatsResponse)
async def invite_stats(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    svc = InviteService(db)
    return await svc.stats()


@router.delete("/{invite_id}")
async def disable_invite(
    invite_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    svc = InviteService(db)
    await svc.disable(invite_id)
    return {"success": True}


@router.get("/public/validate/{code}")
async def validate_invite(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """注册页面调用，验证邀请码是否有效"""
    svc = InviteService(db)
    try:
        invite = await svc.validate(code)
        return {"valid": True, "code": invite.code}
    except ValueError as e:
        return {"valid": False, "message": str(e)}
