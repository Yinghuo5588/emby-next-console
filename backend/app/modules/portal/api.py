from fastapi import APIRouter, Depends, HTTPException, Body
from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_portal_user
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/portal", tags=["portal"])


@router.post("/login")
async def portal_login(
    username: str = Body(...),
    password: str = Body(...),
    db: AsyncSessionDep = None,
):
    import logging
    logger = logging.getLogger("app.portal")
    from app.modules.portal.service import PortalService
    svc = PortalService(db)
    try:
        result = await svc.login(username, password)
        logger.info(f"Portal login success: {username}")
        return {"success": True, "data": result}
    except ValueError as e:
        logger.warning(f"Portal login rejected: {username} - {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Portal login error for {username}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"登录异常: {type(e).__name__}")


@router.get("/me")
async def portal_me(
    user_id: str = Depends(get_current_portal_user),
    db: AsyncSessionDep = None,
):
    from app.modules.portal.service import PortalService
    svc = PortalService(db)
    return {"success": True, "data": await svc.get_me(user_id)}


@router.get("/me/stats")
async def portal_stats(
    user_id: str = Depends(get_current_portal_user),
    db: AsyncSessionDep = None,
):
    from app.modules.portal.service import PortalService
    svc = PortalService(db)
    return {"success": True, "data": await svc.get_stats(user_id)}


@router.put("/me/profile")
async def update_portal_profile(
    user_id: str = Depends(get_current_portal_user),
    db: AsyncSessionDep = None,
    display_name: str | None = Body(None),
    avatar_url: str | None = Body(None),
):
    from app.modules.portal.service import PortalService
    svc = PortalService(db)
    await svc.update_profile(user_id, display_name=display_name, avatar_url=avatar_url)
    return {"success": True}


@router.post("/me/change-password")
async def change_portal_password(
    user_id: str = Depends(get_current_portal_user),
    old_password: str = Body(...),
    new_password: str = Body(...),
):
    from app.core.emby_users import EmbyUserService
    svc = EmbyUserService()
    try:
        await svc.change_password(user_id, old_password, new_password)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
