from __future__ import annotations
import string
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.invite import InviteCode, InviteUsage


def _generate_code(length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


class InviteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, req, creator_id: int) -> InviteCode:
        code = req.custom_code or _generate_code()
        # 检查重复
        existing = await self.db.execute(select(InviteCode).where(InviteCode.code == code))
        if existing.scalar_one_or_none():
            if req.custom_code:
                raise ValueError("邀请码已存在")
            code = _generate_code(10)  # 重新生成更长的
        
        expires_at = None
        if req.expires_days and req.expires_days > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(days=req.expires_days)
        
        invite = InviteCode(
            code=code,
            template_emby_user_id=req.template_emby_user_id,
            permission_template_id=req.permission_template_id,
            max_uses=req.max_uses,
            expires_at=expires_at,
            concurrent_limit=req.concurrent_limit,
            created_by=creator_id,
            status="active",
        )
        self.db.add(invite)
        await self.db.commit()
        await self.db.refresh(invite)
        return invite

    async def list(self, status: str | None = None, page: int = 1, page_size: int = 20):
        query = select(InviteCode)
        count_query = select(func.count()).select_from(InviteCode)
        if status:
            query = query.where(InviteCode.status == status)
            count_query = count_query.where(InviteCode.status == status)
        
        query = query.order_by(InviteCode.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        total = (await self.db.execute(count_query)).scalar()
        return result.scalars().all(), total

    async def get_by_code(self, code: str) -> InviteCode | None:
        result = await self.db.execute(select(InviteCode).where(InviteCode.code == code))
        return result.scalar_one_or_none()

    async def validate(self, code: str) -> InviteCode:
        invite = await self.get_by_code(code)
        if not invite:
            raise ValueError("邀请码不存在")
        if invite.status != "active":
            raise ValueError("邀请码已失效")
        if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
            invite.status = "expired"
            await self.db.commit()
            raise ValueError("邀请码已过期")
        if invite.used_count >= invite.max_uses:
            invite.status = "used"
            await self.db.commit()
            raise ValueError("邀请码已用完")
        return invite

    async def use(self, code: str, emby_user_id: str) -> InviteCode:
        invite = await self.validate(code)
        invite.used_count += 1
        if invite.used_count >= invite.max_uses:
            invite.status = "used"
        
        usage = InviteUsage(
            invite_id=invite.id,
            emby_user_id=emby_user_id,
            used_at=datetime.now(timezone.utc),
        )
        self.db.add(usage)
        await self.db.commit()
        await self.db.refresh(invite)
        return invite

    async def disable(self, invite_id: int):
        await self.db.execute(
            update(InviteCode).where(InviteCode.id == invite_id).values(status="disabled")
        )
        await self.db.commit()

    async def stats(self):
        result = await self.db.execute(
            select(
                func.count().label("total"),
                func.count().filter(InviteCode.status == "active").label("active"),
                func.count().filter(InviteCode.status == "used").label("used"),
                func.count().filter(InviteCode.status == "expired").label("expired"),
                func.count().filter(InviteCode.status == "disabled").label("disabled"),
            ).select_from(InviteCode)
        )
        row = result.one()
        return {"total": row.total, "active": row.active, "used": row.used, "expired": row.expired, "disabled": row.disabled}