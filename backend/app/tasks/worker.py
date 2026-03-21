"""
任务队列占位骨架。
第一阶段只预留接口，后续接入 Celery / Dramatiq / RQ 任选其一。
"""
import logging

logger = logging.getLogger("app.tasks")


async def dispatch_task(task_name: str, payload: dict) -> None:
    """
    统一任务派发入口，后续替换为真实队列 enqueue。
    """
    logger.info(f"[task] dispatch {task_name} payload={payload}")
