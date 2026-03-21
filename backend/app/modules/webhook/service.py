import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.webhook import EmbyWebhookEvent
from app.db.models.playback import PlaybackSession
from app.db.models.user import User
from .schemas import WebhookPayload

logger = logging.getLogger("app.webhook")

# 需要创建通知的事件类型
NOTIFY_EVENTS = {
    "user.authenticatedfailed": "登录失败",
    "system.serverrestart": "服务器重启",
    "library.new": "新内容入库",
}

# 播放类事件
PLAYBACK_START_EVENTS = {"playback.start", "playback.unpause"}
PLAYBACK_STOP_EVENTS = {"playback.stop", "playback.pause"}


class WebhookService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def receive(self, payload: WebhookPayload) -> str:
        """接收并处理一个 Emby Webhook 事件"""
        event_type = payload.Event or "unknown"
        raw = payload.model_dump(exclude_none=True)

        # 提取常用字段
        user_info = payload.User or {}
        item_info = payload.Item or {}
        session_info = payload.Session or {}

        # 存储原始事件
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

        # 分发处理
        if event_type in PLAYBACK_START_EVENTS:
            await self._handle_playback_start(payload)
        elif event_type in PLAYBACK_STOP_EVENTS:
            await self._handle_playback_stop(payload)
        elif event_type == "user.authenticated":
            await self._handle_user_login(payload)
        elif event_type in NOTIFY_EVENTS:
            await self._create_notification(payload, NOTIFY_EVENTS[event_type])

        # 标记已处理
        row.processed = True
        row.processed_at = datetime.now(timezone.utc)
        return event_type

    async def _handle_playback_start(self, payload: WebhookPayload):
        """播放开始 → 创建/更新 PlaybackSession"""
        session_info = payload.Session or {}
        user_info = payload.User or {}
        item_info = payload.Item or {}

        session_id = session_info.get("Id")
        if not session_id:
            return

        # 查找已有会话
        stmt = select(PlaybackSession).where(PlaybackSession.emby_session_id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        # 查找用户
        user = await self._find_user_by_emby_id(user_info.get("Id"))

        if session:
            session.status = "active"
            session.media_name = item_info.get("Name", session.media_name)
            session.media_id = item_info.get("Id", session.media_id)
            session.client_name = session_info.get("Client", session.client_name)
            session.device_name = session_info.get("DeviceName", session.device_name)
            session.ip_address = session_info.get("RemoteEndPoint", session.ip_address)
            session.last_seen_at = now
        else:
            session = PlaybackSession(
                user_id=user.id if user else None,
                emby_session_id=session_id,
                status="active",
                media_id=item_info.get("Id", ""),
                media_name=item_info.get("Name", "未知内容"),
                client_name=session_info.get("Client"),
                device_name=session_info.get("DeviceName"),
                device_id=session_info.get("DeviceId"),
                ip_address=session_info.get("RemoteEndPoint"),
                started_at=now,
                last_seen_at=now,
            )
            self.db.add(session)

        logger.info(f"Playback start: {user_info.get('Name')} → {item_info.get('Name')}")

    async def _handle_playback_stop(self, payload: WebhookPayload):
        """播放停止 → 标记会话结束"""
        session_info = payload.Session or {}
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
            logger.info(f"Playback stop: session {session_id}")

    async def _handle_user_login(self, payload: WebhookPayload):
        """用户登录 → 记录最后登录时间"""
        user_info = payload.User or {}
        user = await self._find_user_by_emby_id(user_info.get("Id"))
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            logger.info(f"User login: {user_info.get('Name')}")

    async def _create_notification(self, payload: WebhookPayload, description: str):
        """创建通知记录"""
        from app.db.models.notification import Notification

        user_info = payload.User or {}
        user = await self._find_user_by_emby_id(user_info.get("Id"))

        notif = Notification(
            user_id=user.id if user else None,
            type=payload.Event or "webhook",
            title=description,
            message=f"{user_info.get('Name', '系统')}: {description}",
            level="warning" if "failed" in (payload.Event or "") else "info",
            source_type="emby_webhook",
            source_id=payload.Event,
        )
        self.db.add(notif)
        logger.info(f"Notification created: {description}")

    async def _find_user_by_emby_id(self, emby_user_id: str | None) -> User | None:
        if not emby_user_id:
            return None
        stmt = select(User).where(User.emby_user_id == emby_user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        # 本地没有则从 Emby API 同步
        if not user:
            user = await self._sync_user_from_emby(emby_user_id)
        return user

    async def _sync_user_from_emby(self, emby_user_id: str) -> User | None:
        """从 Emby API 同步单个用户到本地数据库"""
        from app.core.emby_data import data as emby_data

        try:
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

            # 创建 profile
            from app.db.models.user import UserProfile
            profile = UserProfile(user_id=user.id)
            self.db.add(profile)

            logger.info(f"Auto-synced user: {user.username} (emby_id={emby_user_id})")
            return user
        except Exception as e:
            logger.warning(f"Failed to sync user {emby_user_id}: {e}")
            return None
