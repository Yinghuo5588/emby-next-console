import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus import bus
from app.core.settings import settings
from app.db.models.webhook import EmbyWebhookEvent
from .schemas import WebhookPayload

logger = logging.getLogger("app.webhook")

# 需要创建通知的事件
NOTIFY_EVENTS = {
    "user.authenticatedfailed": ("登录失败", "warning"),
    "system.serverrestart": ("服务器重启", "warning"),
    "library.new": ("新内容入库", "info"),
}

PLAYBACK_START = {"playback.start", "playback.unpause"}
PLAYBACK_STOP = {"playback.stop", "playback.pause"}


class WebhookService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def receive(self, payload: WebhookPayload) -> str:
        """接收 Emby Webhook 事件，存储后通过 Event Bus 分发"""
        event_type = payload.Event or "unknown"
        raw = payload.model_dump(exclude_none=True)

        user_info = payload.User or {}
        item_info = payload.Item or {}
        session_info = payload.Session or {}

        # ① 违规客户端拦截
        if await self._intercept_illegal_client(session_info, payload):
            return event_type

        # ② 存储原始事件
        row = EmbyWebhookEvent(
            event_type=event_type,
            raw_payload=raw,
            emby_user_id=user_info.get("Id"),
            emby_user_name=user_info.get("Name"),
            media_name=item_info.get("Name"),
            media_type=item_info.get("Type"),
            device_name=session_info.get("DeviceName"),
            session_id=session_info.get("Id"),
        )
        self.db.add(row)
        await self.db.flush()

        # ③ 内联处理播放会话和通知
        if event_type in PLAYBACK_START:
            await self._handle_playback_start(user_info, item_info, session_info)
        elif event_type in PLAYBACK_STOP:
            await self._handle_playback_stop(session_info)
        elif event_type == "user.authenticated":
            await self._handle_user_login(user_info)
        elif event_type in NOTIFY_EVENTS:
            title, level = NOTIFY_EVENTS[event_type]
            await self._create_notification(user_info, event_type, title, level)

        # ④ 发布到事件总线（风控等异步消费）
        bus.publish("webhook.received", event_type, raw)

        logger.info(f"Webhook: {event_type} | user={user_info.get('Name')} | media={item_info.get('Name')}")

        row.processed = True
        row.processed_at = datetime.now(timezone.utc)
        return event_type

    async def _handle_playback_start(self, user_info: dict, item_info: dict, session_info: dict):
        """播放开始 → 创建/更新 PlaybackSession"""
        from app.db.models.playback import PlaybackSession

        session_id = session_info.get("Id")
        if not session_id:
            return

        stmt = select(PlaybackSession).where(PlaybackSession.emby_session_id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        user = await self._find_user_by_emby_id(user_info.get("Id"))

        if session:
            session.status = "active"
            session.media_name = item_info.get("Name", session.media_name)
            session.media_id = item_info.get("Id", session.media_id)
            session.last_seen_at = now
        else:
            session = PlaybackSession(
                user_id=user.id if user else None,
                emby_session_id=session_id,
                status="active",
                media_id=item_info.get("Id", ""),
                media_name=item_info.get("Name", "未知"),
                client_name=session_info.get("Client"),
                device_name=session_info.get("DeviceName"),
                device_id=session_info.get("DeviceId"),
                ip_address=session_info.get("RemoteEndPoint"),
                started_at=now,
                last_seen_at=now,
            )
            self.db.add(session)

    async def _handle_playback_stop(self, session_info: dict):
        """播放停止 → 标记会话结束"""
        from app.db.models.playback import PlaybackSession

        session_id = session_info.get("Id")
        if not session_id:
            return

        stmt = select(PlaybackSession).where(PlaybackSession.emby_session_id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session and session.status == "active":
            now = datetime.now(timezone.utc)
            session.status = "ended"
            session.ended_at = now
            session.last_seen_at = now

    async def _handle_user_login(self, user_info: dict):
        """用户登录 → 更新 last_login_at"""
        user = await self._find_user_by_emby_id(user_info.get("Id"))
        if user:
            user.last_login_at = datetime.now(timezone.utc)

    async def _create_notification(self, user_info: dict, event_type: str, title: str, level: str):
        """创建通知"""
        from app.db.models.notification import Notification

        user = await self._find_user_by_emby_id(user_info.get("Id"))
        notif = Notification(
            user_id=user.id if user else None,
            type=event_type,
            title=title,
            message=f"{user_info.get('Name', '系统')}: {title}",
            level=level,
            source_type="emby_webhook",
        )
        self.db.add(notif)

    async def _intercept_illegal_client(self, session_info: dict, payload: WebhookPayload) -> bool:
        """检查客户端是否在黑名单中"""
        from app.db.models.system import SystemSetting

        client = (session_info.get("Client") or "").lower()
        device_id = session_info.get("DeviceId") or ""
        session_id = session_info.get("Id") or ""

        if not client or not device_id:
            return False

        stmt = select(SystemSetting).where(SystemSetting.setting_key == "client_blacklist")
        result = await self.db.execute(stmt)
        setting = result.scalar_one_or_none()
        if not setting or not setting.value_json:
            return False

        blacklist = [str(x).lower() for x in setting.value_json] if isinstance(setting.value_json, list) else []
        if client not in blacklist:
            return False

        # 命中 → 踢会话 + 删设备
        host = settings.EMBY_HOST.rstrip("/")
        key = settings.EMBY_API_KEY
        if session_id and host and key:
            try:
                async with httpx.AsyncClient(timeout=3) as http:
                    await http.post(
                        f"{host}/emby/Sessions/{session_id}/Command?api_key={key}",
                        json={"Name": "DisplayMessage", "Arguments": {"Header": "🚫 违规拦截", "Text": f"客户端 {client} 已被禁止", "TimeoutMs": "10000"}},
                    )
                    await http.post(f"{host}/emby/Sessions/{session_id}/Playing/Stop?api_key={key}")
            except Exception:
                pass

        if device_id and host and key:
            try:
                async with httpx.AsyncClient(timeout=3) as http:
                    await http.delete(f"{host}/emby/Devices?Id={device_id}&api_key={key}")
            except Exception:
                pass

        logger.warning(f"🚫 客户端拦截: {client} (device={device_id})")

        from app.db.models.notification import Notification
        notif = Notification(
            user_id=None,
            type="client_blocked",
            title="违规客户端拦截",
            message=f"已拦截 {client}，会话已终止",
            level="warning",
            source_type="webhook_intercept",
        )
        self.db.add(notif)

        return True

    async def _find_user_by_emby_id(self, emby_user_id: str | None):
        """查找本地用户，不存在则自动同步"""
        from app.db.models.user import User, UserProfile

        if not emby_user_id:
            return None

        stmt = select(User).where(User.emby_user_id == emby_user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            try:
                from app.core.emby_data import data as emby_data
                emby_user = await emby_data.get_user(emby_user_id)
                policy = emby_user.get("Policy", {})
                user = User(
                    emby_user_id=emby_user_id,
                    username=emby_user.get("Name", f"emby_{emby_user_id}"),
                    display_name=emby_user.get("Name"),
                    role="admin" if policy.get("IsAdministrator") else "user",
                    status="disabled" if policy.get("IsDisabled") else "active",
                    source="emby",
                )
                self.db.add(user)
                await self.db.flush()
                profile = UserProfile(user_id=user.id)
                self.db.add(profile)
                logger.info(f"Auto-synced user: {user.username}")
            except Exception as e:
                logger.warning(f"User sync failed for {emby_user_id}: {e}")

        return user
