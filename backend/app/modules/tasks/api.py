from fastapi import APIRouter, Depends, Query
from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/admin/tasks", tags=["tasks"])


@router.get("")
async def list_tasks(
    db: AsyncSessionDep,
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin=Depends(get_current_user_id),
):
    from app.modules.tasks.service import TasksService
    svc = TasksService(db)
    return {"success": True, "data": await svc.list_tasks(status, page, page_size)}


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    db: AsyncSessionDep,
    admin=Depends(get_current_user_id),
):
    from app.modules.tasks.service import TasksService
    svc = TasksService(db)
    return {"success": True, "data": await svc.get_task(task_id)}


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    db: AsyncSessionDep,
    admin=Depends(get_current_user_id),
):
    from app.modules.tasks.service import TasksService
    svc = TasksService(db)
    return {"success": True, "data": await svc.cancel_task(task_id)}


@router.get("/stats/overview")
async def task_stats(
    db: AsyncSessionDep,
    admin=Depends(get_current_user_id),
):
    from app.modules.tasks.service import TasksService
    svc = TasksService(db)
    return {"success": True, "data": await svc.get_stats()}
