from datetime import datetime
from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.notification import (
    NotificationChannel, NotificationTemplate, NotificationRule,
    UserNotificationPref, NotificationLog
)


class NotificationExtService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== 通道 ==========

    async def create_channel(self, data: dict) -> dict:
        ch = NotificationChannel(
            name=data["name"],
            channel_type=data["channel_type"],
            config=data.get("config"),
            is_active=data.get("is_active", True),
        )
        self.db.add(ch)
        await self.db.commit()
        await self.db.refresh(ch)
        return self._channel_to_dict(ch)

    async def list_channels(self) -> list[dict]:
        stmt = select(NotificationChannel).order_by(NotificationChannel.created_at.desc())
        result = await self.db.execute(stmt)
        return [self._channel_to_dict(ch) for ch in result.scalars().all()]

    async def update_channel(self, channel_id: int, data: dict) -> dict:
        stmt = select(NotificationChannel).where(NotificationChannel.id == channel_id)
        result = await self.db.execute(stmt)
        ch = result.scalar_one_or_none()
        if not ch:
            raise ValueError(f"Channel {channel_id} not found")
        for k in ("name", "channel_type", "config", "is_active"):
            if k in data:
                setattr(ch, k, data[k])
        ch.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(ch)
        return self._channel_to_dict(ch)

    async def delete_channel(self, channel_id: int):
        await self.db.execute(delete(NotificationChannel).where(NotificationChannel.id == channel_id))
        await self.db.commit()

    async def test_channel(self, channel_id: int) -> dict:
        stmt = select(NotificationChannel).where(NotificationChannel.id == channel_id)
        result = await self.db.execute(stmt)
        ch = result.scalar_one_or_none()
        if not ch:
            raise ValueError(f"Channel {channel_id} not found")
        # 实际发送测试消息（简化：只做日志记录）
        import httpx
        config = ch.config or {}
        if ch.channel_type == "webhook" and config.get("url"):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.post(config["url"], json={"text": "Emby Next Console 测试通知"})
                    return {"success": resp.is_success, "status_code": resp.status_code}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": True, "message": f"Channel type '{ch.channel_type}' test not implemented"}

    # ========== 模板 ==========

    async def create_template(self, data: dict) -> dict:
        tpl = NotificationTemplate(
            name=data["name"],
            template_type=data["template_type"],
            title_template=data["title_template"],
            body_template=data["body_template"],
            variables=data.get("variables"),
            is_default=data.get("is_default", False),
        )
        self.db.add(tpl)
        await self.db.commit()
        await self.db.refresh(tpl)
        return self._template_to_dict(tpl)

    async def list_templates(self, template_type: str | None = None) -> list[dict]:
        stmt = select(NotificationTemplate)
        if template_type:
            stmt = stmt.where(NotificationTemplate.template_type == template_type)
        stmt = stmt.order_by(NotificationTemplate.created_at.desc())
        result = await self.db.execute(stmt)
        return [self._template_to_dict(t) for t in result.scalars().all()]

    async def update_template(self, template_id: int, data: dict) -> dict:
        stmt = select(NotificationTemplate).where(NotificationTemplate.id == template_id)
        result = await self.db.execute(stmt)
        tpl = result.scalar_one_or_none()
        if not tpl:
            raise ValueError(f"Template {template_id} not found")
        for k in ("name", "template_type", "title_template", "body_template", "variables", "is_default"):
            if k in data:
                setattr(tpl, k, data[k])
        await self.db.commit()
        await self.db.refresh(tpl)
        return self._template_to_dict(tpl)

    async def delete_template(self, template_id: int):
        await self.db.execute(delete(NotificationTemplate).where(NotificationTemplate.id == template_id))
        await self.db.commit()

    # ========== 规则 ==========

    async def create_rule(self, data: dict) -> dict:
        rule = NotificationRule(
            event_type=data["event_type"],
            channel_id=data["channel_id"],
            template_id=data.get("template_id"),
            is_active=data.get("is_active", True),
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return self._rule_to_dict(rule)

    async def list_rules(self, event_type: str | None = None) -> list[dict]:
        stmt = select(NotificationRule)
        if event_type:
            stmt = stmt.where(NotificationRule.event_type == event_type)
        stmt = stmt.order_by(NotificationRule.event_type)
        result = await self.db.execute(stmt)
        return [self._rule_to_dict(r) for r in result.scalars().all()]

    async def update_rule(self, rule_id: int, data: dict) -> dict:
        stmt = select(NotificationRule).where(NotificationRule.id == rule_id)
        result = await self.db.execute(stmt)
        rule = result.scalar_one_or_none()
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")
        for k in ("event_type", "channel_id", "template_id", "is_active"):
            if k in data:
                setattr(rule, k, data[k])
        await self.db.commit()
        await self.db.refresh(rule)
        return self._rule_to_dict(rule)

    async def delete_rule(self, rule_id: int):
        await self.db.execute(delete(NotificationRule).where(NotificationRule.id == rule_id))
        await self.db.commit()

    # ========== 日志 ==========

    async def list_logs(self, page: int = 1, page_size: int = 20,
                        event_type: str | None = None, status: str | None = None) -> dict:
        stmt = select(NotificationLog)
        if event_type:
            stmt = stmt.where(NotificationLog.event_type == event_type)
        if status:
            stmt = stmt.where(NotificationLog.status == status)
        stmt = stmt.order_by(NotificationLog.created_at.desc())

        # count
        count_stmt = select(func.count()).select_from(NotificationLog)
        if event_type:
            count_stmt = count_stmt.where(NotificationLog.event_type == event_type)
        if status:
            count_stmt = count_stmt.where(NotificationLog.status == status)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        logs = [self._log_to_dict(l) for l in result.scalars().all()]
        return {"items": logs, "total": total, "page": page, "page_size": page_size}

    # ========== 转换 ==========

    def _channel_to_dict(self, ch: NotificationChannel) -> dict:
        return {
            "id": ch.id, "name": ch.name, "channel_type": ch.channel_type,
            "config": ch.config, "is_active": ch.is_active,
            "created_at": ch.created_at.isoformat() if ch.created_at else None,
        }

    def _template_to_dict(self, tpl: NotificationTemplate) -> dict:
        return {
            "id": tpl.id, "name": tpl.name, "template_type": tpl.template_type,
            "title_template": tpl.title_template, "body_template": tpl.body_template,
            "variables": tpl.variables, "is_default": tpl.is_default,
        }

    def _rule_to_dict(self, rule: NotificationRule) -> dict:
        return {
            "id": rule.id, "event_type": rule.event_type,
            "channel_id": rule.channel_id, "template_id": rule.template_id,
            "is_active": rule.is_active,
        }

    def _log_to_dict(self, log: NotificationLog) -> dict:
        return {
            "id": log.id, "event_type": log.event_type,
            "channel_id": log.channel_id, "template_id": log.template_id,
            "recipient_user_id": log.recipient_user_id,
            "title": log.title, "body": log.body,
            "status": log.status, "error_message": log.error_message,
            "sent_at": log.sent_at.isoformat() if log.sent_at else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }