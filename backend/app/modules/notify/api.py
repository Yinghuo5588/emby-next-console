"""Webhook 推送通知模块"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.db.models.notify import NotifyDestination
from app.db.session import AsyncSessionDep, AsyncSessionFactory
from app.shared.responses import ApiResponse

logger = logging.getLogger("app.notify")

router = APIRouter(prefix="/notify", tags=["notify"])

# 支持的事件类型
EVENT_TYPES = {
    "risk.alert": "风控告警",
    "user.created": "创建用户",
    "user.deleted": "删除用户",
    "user.expired": "用户过期",
    "vip.changed": "VIP 变更",
    "scan.complete": "扫描完成",
}


# ── Schemas ──

class DestinationCreate(BaseModel):
    name: str
    url: str
    secret: str | None = None
    events: list[str] = []
    is_active: bool = True


class DestinationUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    secret: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None


# ── API ──

@router.get("/destinations")
async def list_destinations(db: AsyncSessionDep):
    """获取所有推送目标"""
    result = await db.execute(select(NotifyDestination).order_by(NotifyDestination.id.desc()))
    items = result.scalars().all()
    return ApiResponse.ok(data=[_serialize(d) for d in items])


@router.get("/events")
async def list_events():
    """获取支持的事件类型"""
    return ApiResponse.ok(data=[{"key": k, "label": v} for k, v in EVENT_TYPES.items()])


@router.post("/destinations")
async def create_destination(body: DestinationCreate, db: AsyncSessionDep):
    """创建推送目标"""
    dest = NotifyDestination(
        name=body.name,
        url=body.url,
        secret=body.secret,
        events=body.events,
        is_active=body.is_active,
    )
    db.add(dest)
    await db.commit()
    await db.refresh(dest)
    return ApiResponse.ok(data=_serialize(dest))


@router.patch("/destinations/{dest_id}")
async def update_destination(dest_id: int, body: DestinationUpdate, db: AsyncSessionDep):
    """更新推送目标"""
    result = await db.execute(select(NotifyDestination).where(NotifyDestination.id == dest_id))
    dest = result.scalar_one_or_none()
    if not dest:
        return ApiResponse.error("Not found", error_code="NOT_FOUND")
    if body.name is not None:
        dest.name = body.name
    if body.url is not None:
        dest.url = body.url
    if body.secret is not None:
        dest.secret = body.secret
    if body.events is not None:
        dest.events = body.events
    if body.is_active is not None:
        dest.is_active = body.is_active
    await db.commit()
    await db.refresh(dest)
    return ApiResponse.ok(data=_serialize(dest))


@router.delete("/destinations/{dest_id}")
async def delete_destination(dest_id: int, db: AsyncSessionDep):
    """删除推送目标"""
    result = await db.execute(select(NotifyDestination).where(NotifyDestination.id == dest_id))
    dest = result.scalar_one_or_none()
    if not dest:
        return ApiResponse.error("Not found", error_code="NOT_FOUND")
    await db.delete(dest)
    await db.commit()
    return ApiResponse.ok(message="已删除")


@router.post("/destinations/{dest_id}/test")
async def test_destination(dest_id: int, db: AsyncSessionDep):
    """发送测试通知"""
    result = await db.execute(select(NotifyDestination).where(NotifyDestination.id == dest_id))
    dest = result.scalar_one_or_none()
    if not dest:
        return ApiResponse.error("Not found", error_code="NOT_FOUND")

    payload = {
        "event": "test",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "emby-next-console",
        "data": {"message": "这是一条测试通知"},
    }
    ok, error = await _send_one(dest, payload)
    if ok:
        dest.last_sent_at = datetime.now(timezone.utc)
        dest.last_error = None
        await db.commit()
        return ApiResponse.ok(message="发送成功")
    else:
        dest.last_error = error
        await db.commit()
        return ApiResponse.error(f"发送失败: {error}", error_code="SEND_FAILED")


# ── 发送逻辑 ──

async def dispatch(event_type: str, data: dict[str, Any]):
    """分发事件到所有订阅了该事件的活跃目标"""
    try:
        async with AsyncSessionFactory() as db:
            result = await db.execute(
                select(NotifyDestination).where(
                    NotifyDestination.is_active == True,
                )
            )
            destinations = result.scalars().all()

            payload = {
                "event": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "emby-next-console",
                "data": data,
            }

            tasks = []
            for dest in destinations:
                if event_type in (dest.events or []):
                    tasks.append(_send_and_update(dest, payload))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"通知分发失败: {e}")


async def _send_and_update(dest: NotifyDestination, payload: dict):
    """发送并更新状态"""
    ok, error = await _send_one(dest, payload)
    try:
        async with AsyncSessionFactory() as db:
            result = await db.execute(select(NotifyDestination).where(NotifyDestination.id == dest.id))
            d = result.scalar_one_or_none()
            if d:
                d.last_sent_at = datetime.now(timezone.utc)
                d.last_error = None if ok else error
                await db.commit()
    except Exception:
        pass


async def _send_one(dest: NotifyDestination, payload: dict) -> tuple[bool, str | None]:
    """发送单条通知，返回 (成功, 错误信息)"""
    body_str = json.dumps(payload, ensure_ascii=False)
    headers = {"Content-Type": "application/json"}

    # HMAC 签名
    if dest.secret:
        sig = hmac.new(dest.secret.encode(), body_str.encode(), hashlib.sha256).hexdigest()
        headers["X-Signature"] = f"sha256={sig}"

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(dest.url, content=body_str, headers=headers)
                if resp.status_code < 300:
                    return True, None
                error = f"HTTP {resp.status_code}"
        except Exception as e:
            error = str(e)

        if attempt < 2:
            await asyncio.sleep(2 ** attempt)

    logger.warning(f"通知发送失败 [{dest.name}]: {error}")
    return False, error


def _serialize(dest: NotifyDestination) -> dict:
    return {
        "id": dest.id,
        "name": dest.name,
        "url": dest.url,
        "secret_masked": "***" if dest.secret else None,
        "events": dest.events or [],
        "is_active": dest.is_active,
        "created_at": dest.created_at.isoformat() if dest.created_at else None,
        "last_sent_at": dest.last_sent_at.isoformat() if dest.last_sent_at else None,
        "last_error": dest.last_error,
    }
