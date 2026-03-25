"""
风控后台监控 — 仅负责自动解封到期封禁（每30分钟）
实时扫描由 webhook 事件触发，不再定时轮询
"""
import asyncio
import logging

logger = logging.getLogger("app.risk_monitor")

_monitor_task: asyncio.Task | None = None


async def _auto_unban_expired():
    """检查到期封禁，自动解封"""
    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.db.session import AsyncSessionFactory
    from app.db.models.risk import RiskViolation
    from app.core.emby import emby

    now = datetime.now(timezone.utc)
    async with AsyncSessionFactory() as db:
        stmt = select(RiskViolation).where(
            RiskViolation.locked_until.isnot(None),
            RiskViolation.locked_until <= now,
            RiskViolation.last_action == "ban",
        )
        result = await db.execute(stmt)
        expired = result.scalars().all()

        for v in expired:
            try:
                resp = await emby.get(f"/Users/{v.user_id}")
                if resp.status_code == 200:
                    policy = resp.json().get("Policy", {})
                    if policy.get("IsDisabled"):
                        policy["IsDisabled"] = False
                        await emby.post(f"/Users/{v.user_id}/Policy", json=policy)
                        logger.info(f"自动解封: user={v.user_id} (封禁到期)")
                        v.locked_until = None
                        v.last_action = "unban_auto"
            except Exception as e:
                logger.error(f"自动解封失败 user={v.user_id}: {e}")

        if expired:
            await db.commit()
            logger.info(f"自动解封完成: 解封{len(expired)}个用户")


async def _monitor_loop():
    """后台循环：仅自动解封，不做全量扫描"""
    logger.info("Risk monitor started (30min auto-unban only)")
    while True:
        try:
            await asyncio.sleep(1800)  # 30 分钟
            await _auto_unban_expired()
        except asyncio.CancelledError:
            logger.info("Risk monitor cancelled")
            break
        except Exception as e:
            logger.error(f"Risk monitor error: {e}")
            await asyncio.sleep(60)


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
