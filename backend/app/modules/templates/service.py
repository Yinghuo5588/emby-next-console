from __future__ import annotations
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.invite import PermissionTemplate


class TemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, req) -> PermissionTemplate:
        tpl = PermissionTemplate(
            name=req.name,
            description=req.description,
            library_access=req.library_access,
            policy_json=req.policy_json,
            configuration_json=req.configuration_json,
            is_default=req.is_default,
        )
        self.db.add(tpl)
        await self.db.commit()
        await self.db.refresh(tpl)
        return tpl

    async def list(self, page: int = 1, page_size: int = 50):
        query = select(PermissionTemplate).order_by(PermissionTemplate.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        total = (await self.db.execute(select(func.count()).select_from(PermissionTemplate))).scalar()
        return result.scalars().all(), total

    async def get(self, template_id: int) -> PermissionTemplate | None:
        result = await self.db.execute(select(PermissionTemplate).where(PermissionTemplate.id == template_id))
        return result.scalar_one_or_none()

    async def update(self, template_id: int, req):
        values = {k: v for k, v in req.model_dump(exclude_unset=True).items() if v is not None}
        if values:
            await self.db.execute(update(PermissionTemplate).where(PermissionTemplate.id == template_id).values(**values))
            await self.db.commit()

    async def delete(self, template_id: int):
        tpl = await self.get(template_id)
        if tpl:
            await self.db.delete(tpl)
            await self.db.commit()