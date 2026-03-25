"""
风控后台监控 — 每 60 秒扫描一次活跃会话
"""
import asyncio
import logging

logger = logging.getLogger("app.risk_monitor")

_monitor_task: asyncio.Task | None = None


async def _monitor_loop():
    """后台循环扫描"""
    logger.info("Risk monitor started (60s interval)")
    while True:
        try:
            await asyncio.sleep(60)
            from app.db.session import AsyncSessionFactory
            from app.modules.risk.api import _scan_logic
            async with AsyncSessionFactory() as db:
                result = await _scan_logic(db)
            blocked = len(result.get("blocked", []))
            violations = len(result.get("violations", []))
            if blocked or violations:
                logger.warning(f"Risk scan: {blocked} blocked, {violations} violations out of {result['total_sessions']} sessions")
        except asyncio.CancelledError:
            logger.info("Risk monitor cancelled")
            break
        except Exception as e:
            logger.error(f"Risk monitor error: {e}")
            await asyncio.sleep(5)


def start_monitor():
    global _monitor_task
    if _monitor_task is None or _monitor_task.done():
        _monitor_task = asyncio.create_task(_monitor_loop())
        logger.info("Risk monitor task created")


def stop_monitor():
    global _monitor_task
    if _monitor_task and not _monitor_task.done():
        _monitor_task.cancel()
        logger.info("Risk monitor task cancelled")
