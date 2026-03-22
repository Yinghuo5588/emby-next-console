import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# 内存任务存储（简化版）
_tasks: dict[str, dict] = {}


class TasksService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_tasks(self, status: str | None = None, page: int = 1, page_size: int = 20) -> dict:
        tasks = list(_tasks.values())
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        tasks.sort(key=lambda t: t.get("created_at", ""), reverse=True)
        total = len(tasks)
        start = (page - 1) * page_size
        return {"items": tasks[start:start + page_size], "total": total, "page": page}

    async def get_task(self, task_id: str) -> dict | None:
        return _tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> dict:
        task = _tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        if task["status"] in ("pending", "running"):
            task["status"] = "cancelled"
            task["finished_at"] = datetime.utcnow().isoformat()
        return task

    async def get_stats(self) -> dict:
        tasks = list(_tasks.values())
        return {
            "total": len(tasks),
            "pending": sum(1 for t in tasks if t["status"] == "pending"),
            "running": sum(1 for t in tasks if t["status"] == "running"),
            "completed": sum(1 for t in tasks if t["status"] == "completed"),
            "failed": sum(1 for t in tasks if t["status"] == "failed"),
            "cancelled": sum(1 for t in tasks if t["status"] == "cancelled"),
        }

    @staticmethod
    def create_task(task_type: str, params: dict | None = None) -> str:
        task_id = str(uuid.uuid4())[:8]
        _tasks[task_id] = {
            "id": task_id,
            "task_type": task_type,
            "status": "pending",
            "progress": 0,
            "params": params or {},
            "result": None,
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "finished_at": None,
        }
        return task_id

    @staticmethod
    def update_task(task_id: str, status: str | None = None, progress: int | None = None,
                    result: dict | None = None, error: str | None = None):
        task = _tasks.get(task_id)
        if not task:
            return
        if status:
            task["status"] = status
            if status == "running" and not task["started_at"]:
                task["started_at"] = datetime.utcnow().isoformat()
            if status in ("completed", "failed", "cancelled"):
                task["finished_at"] = datetime.utcnow().isoformat()
        if progress is not None:
            task["progress"] = progress
        if result is not None:
            task["result"] = result
        if error is not None:
            task["error"] = error
