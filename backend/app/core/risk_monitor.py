"""
风控天眼 - 并发越界检测与执法
"""
import logging
import asyncio
import threading
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.event_bus import bus
from app.core.settings import settings
from app.core.emby import emby

logger = logging.getLogger("app.risk_monitor")

# 指纹记忆（防刷屏报警）
_alerted_fingerprints: set[str] = set()
_last_state: dict[str, int] = {}


def get_user_concurrent_limit(user_id: str, db) -> int:
    """获取用户的并发限额（从 user_profiles.max_concurrent 读取）"""
    from app.db.models.user import UserProfile, User

    # 查找本地用户
    stmt = select(User).where(User.emby_user_id == user_id)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return int(settings.DEFAULT_MAX_CONCURRENT or 2)

    stmt = select(UserProfile).where(UserProfile.user_id == user.id)
    result = db.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile and profile.max_concurrent is not None:
        return profile.max_concurrent
    return int(settings.DEFAULT_MAX_CONCURRENT or 2)


def kick_session(session_id: str) -> bool:
    """通过 Emby API 强制停止播放"""
    host = settings.EMBY_HOST.rstrip("/")
    key = settings.EMBY_API_KEY
    if not host or not key:
        return False
    try:
        import httpx
        with httpx.Client(timeout=5) as client:
            res = client.post(
                f"{host}/emby/Sessions/{session_id}/Playing/Stop",
                headers={"X-Emby-Token": key},
            )
        return res.status_code in (200, 204)
    except Exception as e:
        logger.error(f"踢会话失败: {e}")
        return False


def ban_user(emby_user_id: str) -> bool:
    """通过 Emby API 禁用用户"""
    host = settings.EMBY_HOST.rstrip("/")
    key = settings.EMBY_API_KEY
    if not host or not key:
        return False
    try:
        import httpx
        with httpx.Client(timeout=5) as client:
            res = client.get(f"{host}/emby/Users/{emby_user_id}", headers={"X-Emby-Token": key})
            if res.status_code != 200:
                return False
            user_data = res.json()
            policy = user_data.get("Policy", {})
            policy["IsDisabled"] = True
            res = client.post(
                f"{host}/emby/Users/{emby_user_id}/Policy",
                headers={"X-Emby-Token": key},
                json=policy,
            )
        return res.status_code in (200, 204)
    except Exception as e:
        logger.error(f"禁用用户失败: {e}")
        return False


async def scan_playbacks(session_factory: async_sessionmaker):
    """扫描当前播放会话，检测并发越界"""
    global _alerted_fingerprints, _last_state

    try:
        sessions = await emby.get_sessions(active_only=False)
    except Exception as e:
        logger.warning(f"风控扫描 - 获取会话失败: {e}")
        return

    # 按用户分组活跃播放
    active_playbacks: dict[str, list] = {}
    for s in sessions:
        now_playing = s.get("NowPlayingItem")
        if not now_playing or now_playing.get("MediaType") != "Video":
            continue
        uid = s.get("UserId")
        if not uid:
            continue
        active_playbacks.setdefault(uid, []).append(s)

    current_state = {uid: len(ss) for uid, ss in active_playbacks.items()}
    state_changed = current_state != _last_state

    if state_changed and active_playbacks:
        logger.info(f"📡 并发状态更新: {len(active_playbacks)} 用户在线")

    current_fingerprints: set[str] = set()

    async with session_factory() as db:
        for uid, user_sessions in active_playbacks.items():
            limit = get_user_concurrent_limit(uid, db)
            count = len(user_sessions)
            username = user_sessions[0].get("UserName", "未知")

            if count > limit:
                # 生成指纹（排序设备名 + session id）
                device_ids = sorted([s.get("Id", "") for s in user_sessions])
                fingerprint = f"{uid}-{'-'.join(device_ids)}"
                current_fingerprints.add(fingerprint)

                if fingerprint not in _alerted_fingerprints:
                    logger.warning(f"🚨 并发越界: {username} 当前 {count} / 限额 {limit}")

                    # 创建风控事件
                    from app.db.models.risk import RiskEvent
                    event = RiskEvent(
                        user_id=None,  # 需要查本地 user id，暂时留空
                        event_type="concurrent_limit",
                        severity="high",
                        status="open",
                        title=f"并发越界: {username}",
                        description=f"用户 {username} 当前 {count} 路播放，限额 {limit}",
                        context_json={"emby_user_id": uid, "current": count, "limit": limit},
                        detected_at=datetime.now(timezone.utc),
                    )
                    db.add(event)

                    # 创建通知
                    from app.db.models.notification import Notification
                    notif = Notification(
                        user_id=None,
                        type="risk_alert",
                        title=f"🚨 并发越界: {username}",
                        message=f"当前 {count} 路播放 / 限额 {limit}，请处理",
                        level="error",
                        source_type="risk_monitor",
                    )
                    db.add(notif)

                else:
                    if state_changed:
                        logger.info(f"⚠️ {username} 已报警，跳过重复")

    await db.commit()

    # 更新记忆
    _alerted_fingerprints = current_fingerprints
    _last_state = current_state


def _risk_monitor_loop(session_factory: async_sessionmaker):
    """后台轮询线程"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            loop.run_until_complete(scan_playbacks(session_factory))
        except Exception as e:
            logger.error(f"风控扫描异常: {e}")
        import time
        time.sleep(60)


def start_risk_monitor(session_factory: async_sessionmaker):
    """启动风控天眼"""
    # Webhook 事件触发（播放开始后延迟 3 秒扫描）
    def on_playback_start(event_type, data):
        import time
        time.sleep(3)
        asyncio.run(scan_playbacks(session_factory))

    bus.subscribe("webhook.received", on_playback_start)

    # 后台轮询兜底
    t = threading.Thread(target=_risk_monitor_loop, args=(session_factory,), daemon=True, name="RiskMonitor")
    t.start()
    logger.info("👁️ 风控天眼已启动（事件驱动 + 60s 轮询兜底）")
