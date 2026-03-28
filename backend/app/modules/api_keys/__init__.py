"""API 密钥管理"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.core.dependencies import get_current_admin
from app.db.models.api_key import ApiKey
from app.db.session import AsyncSessionDep
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class ApiKeyCreate(BaseModel):
    name: str
    scopes: str = "read"  # read, write, admin


@router.get("")
async def list_keys(db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    """获取所有 API Key（不返回完整 key）"""
    result = await db.execute(select(ApiKey).order_by(ApiKey.id.desc()))
    keys = result.scalars().all()
    return ApiResponse.ok(data=[{
        "id": k.id,
        "name": k.name,
        "key_prefix": k.key_prefix,
        "scopes": k.scopes,
        "is_active": k.is_active,
        "created_at": k.created_at.isoformat() if k.created_at else None,
        "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
    } for k in keys])


@router.post("")
async def create_key(body: ApiKeyCreate, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    """创建 API Key（只返回一次完整 key）"""
    raw_key = f"enc_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key = ApiKey(
        name=body.name,
        key_hash=key_hash,
        key_prefix=raw_key[:8],
        scopes=body.scopes,
        is_active=True,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return ApiResponse.ok(data={
        "id": key.id,
        "name": key.name,
        "key": raw_key,  # 只有创建时返回完整 key
        "key_prefix": key.key_prefix,
        "scopes": key.scopes,
    }, message="请妥善保存，密钥只显示一次")


@router.delete("/{key_id}")
async def delete_key(key_id: int, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    """删除 API Key"""
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        return ApiResponse.error("Not found", error_code="NOT_FOUND")
    await db.delete(key)
    await db.commit()
    return ApiResponse.ok(message="已删除")
