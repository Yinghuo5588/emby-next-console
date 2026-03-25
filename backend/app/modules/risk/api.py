"""
风控管控 API — 客户端黑名单 + 并发管控 + 事件 + 执法日志
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.dependencies import get_current_admin
from app.core.emby import emby
from app.db.models.risk import RiskActionLog, RiskEvent
from app.db.models.system import SystemSetting
from app.db.session import AsyncSessionDep
from app.modules.users import service as users_service
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/risk", tags=["risk"])

BLACKLIST_KEY = "client_blacklist"


# ── Schemas ──────────────────────────────────────────────

class BlacklistRequest(BaseModel):
    name: str


class RiskEventActionRequest(BaseModel):
    action: str  # resolve / ignore


class KickRequest(BaseModel):
    session_id: str
    device_id: str = ""
    level: str = "soft"  # soft=仅停止, hard=停止+删设备(对302有效)


class BanRequest(BaseModel):
    user_id: str
    reason: str | None = None


# ── Internal helpers ─────────────────────────────────────

async def _get_blacklist(db) -> list[str]:
    stmt = select(SystemSetting).where(SystemSetting.setting_key == BLACKLIST_KEY)
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()
    items = setting.value_json if setting and isinstance(setting.value_json, list) else []
    return [str(x).strip().lower() for x in items if str(x).strip()]


async def _set_blacklist(db, items: list[str]) -> list[str]:
    normalized = sorted({x.strip().lower() for x in items if x and x.strip()})
    stmt = select(SystemSetting).where(SystemSetting.setting_key == BLACKLIST_KEY)
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if setting:
        setting.value_json = normalized
        setting.updated_at = now
    else:
        setting = SystemSetting(
            setting_key=BLACKLIST_KEY,
            setting_group="risk",
            value_json=normalized,
            description="客户端黑名单（小写去重）",
            updated_at=now,
        )
        db.add(setting)
    await db.commit()
    return normalized


async def _log_action(db, action: str, target: str, reason: str | None = None):
    db.add(RiskActionLog(action=action, target=target, reason=reason))
    await db.commit()


async def _upsert_risk_event(
    db,
    *,
    event_type: str,
    title: str,
    description: str | None,
    severity: str = "medium",
    context_json: dict[str, Any] | None = None,
) -> RiskEvent:
    existing_stmt = (
        select(RiskEvent)
        .where(
            RiskEvent.status == "open",
            RiskEvent.event_type == event_type,
            RiskEvent.title == title,
        )
        .order_by(RiskEvent.detected_at.desc())
        .limit(1)
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        existing.description = description
        existing.severity = severity
        existing.context_json = context_json
        return existing

    event = RiskEvent(
        user_id=None,
        rule_id=None,
        event_type=event_type,
        severity=severity,
        status="open",
        title=title,
        description=description,
        context_json=context_json,
        detected_at=datetime.now(timezone.utc),
    )
    db.add(event)
    return event


async def _record_scan_events(db, blocked: list[dict], violations: list[dict]):
    for item in blocked:
        await _upsert_risk_event(
            db,
            event_type="client_blocked",
            severity="high",
            title=f"违规客户端拦截：{item.get('user_name') or '未知用户'}",
            description=f"客户端 {item.get('client') or '-'} 播放《{item.get('title') or '未知内容'}》已被拦截，设备已下线。",
            context_json=item,
        )
    for item in violations:
        await _upsert_risk_event(
            db,
            event_type="concurrent_exceeded",
            severity="medium",
            title=f"并发越界：{item.get('user_name') or item.get('user_id') or '未知用户'}",
            description=f"当前并发 {item.get('current', 0)} / 限额 {item.get('max', 0)}",
            context_json=item,
        )
    await db.commit()


async def _scan_logic(db) -> dict[str, Any]:
    """核心扫描：黑名单拦截 + 并发越界检测"""
    import logging
    logger = logging.getLogger("app.risk")

    blacklist = set(await _get_blacklist(db))
    sessions = await emby.get_sessions(active_only=True)
    await users_service._ensure_meta_loaded()

    blocked: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    concurrent_map: dict[str, list[dict[str, Any]]] = {}

    logger.info(f"扫描开始: {len(sessions)}个会话, {len(blacklist)}个黑名单客户端")

    for s in sessions:
        session_id = s.get("Id", "")
        user_id = s.get("UserId", "")
        user_name = s.get("UserName", "")
        client = (s.get("Client") or s.get("AppName") or "").strip()
        client_l = client.lower()
        device_id = s.get("DeviceId", "")
        device_name = s.get("DeviceName", "")
        now_playing = s.get("NowPlayingItem") or {}
        title = now_playing.get("Name", "")

        # 并发统计：只统计有播放内容的会话
        if now_playing and user_id:
            concurrent_map.setdefault(user_id, []).append({
                "session_id": session_id,
                "user_id": user_id,
                "user_name": user_name,
                "client": client,
                "device_id": device_id,
                "device_name": device_name,
                "title": title,
            })

        # 黑名单拦截：正在播放且客户端命中黑名单
        if now_playing and client_l and client_l in blacklist:
            logger.warning(f"黑名单命中: {user_name} 使用 {client} (device={device_id})")
            await emby.send_session_message(
                session_id,
                text=f"当前客户端「{client}」已被管理员禁用，播放已停止，请更换受支持客户端后重新登录。",
                header="客户端管控",
                timeout_ms=5000,
            )
            kick_result = await emby.force_kick(session_id, device_id)
            logger.info(f"强踢结果: {kick_result}")
            blocked.append({
                "session_id": session_id,
                "user_id": user_id,
                "user_name": user_name,
                "client": client,
                "device_id": device_id,
                "device_name": device_name,
                "title": title,
            })

    meta_cache = users_service._meta_cache
    for user_id, items in concurrent_map.items():
        current = len(items)
        meta = meta_cache.get(user_id, {})
        max_concurrent = int(meta.get("max_concurrent", 2) or 2)
        if current > max_concurrent:
            violations.append({
                "user_id": user_id,
                "user_name": items[0].get("user_name", ""),
                "current": current,
                "max": max_concurrent,
                "sessions": items,
            })

    if blocked or violations:
        await _record_scan_events(db, blocked, violations)

    logger.info(f"扫描完成: 拦截{len(blocked)}个违规, {len(violations)}个越界, 总会话{len(sessions)}")

    return {
        "blocked": blocked,
        "violations": violations,
        "total_sessions": len(sessions),
        "blacklist_count": len(blacklist),
    }


# ── API endpoints ────────────────────────────────────────

@router.get("/summary")
async def summary(db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    open_count = await db.scalar(select(func.count()).select_from(RiskEvent).where(RiskEvent.status == "open")) or 0
    high_count = await db.scalar(
        select(func.count()).select_from(RiskEvent).where(RiskEvent.status == "open", RiskEvent.severity == "high")
    ) or 0
    recent = (await db.execute(select(RiskEvent).order_by(RiskEvent.detected_at.desc()).limit(5))).scalars().all()
    return ApiResponse.ok(data={
        "open_count": int(open_count),
        "high_count": int(high_count),
        "recent_events": [
            {
                "event_id": str(ev.id),
                "user_id": "",
                "event_type": ev.event_type,
                "severity": ev.severity,
                "status": ev.status,
                "title": ev.title,
                "description": ev.description,
                "detected_at": ev.detected_at,
            }
            for ev in recent
        ],
    })


@router.get("/events")
async def events(
    db: AsyncSessionDep,
    _: dict = Depends(get_current_admin),
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    severity: str | None = None,
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    stmt = select(RiskEvent)
    count_stmt = select(func.count()).select_from(RiskEvent)
    if status:
        stmt = stmt.where(RiskEvent.status == status)
        count_stmt = count_stmt.where(RiskEvent.status == status)
    if severity:
        stmt = stmt.where(RiskEvent.severity == severity)
        count_stmt = count_stmt.where(RiskEvent.severity == severity)
    total = await db.scalar(count_stmt) or 0
    items = (await db.execute(
        stmt.order_by(RiskEvent.detected_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return ApiResponse.ok(data={
        "items": [
            {
                "event_id": str(ev.id),
                "user_id": "",
                "event_type": ev.event_type,
                "severity": ev.severity,
                "status": ev.status,
                "title": ev.title,
                "description": ev.description,
                "detected_at": ev.detected_at,
            }
            for ev in items
        ],
        "total": int(total),
    })


@router.post("/events/{event_id}/action")
async def event_action(event_id: str, body: RiskEventActionRequest, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    ev = await db.get(RiskEvent, int(event_id))
    if not ev:
        return ApiResponse.error("事件不存在")
    if body.action not in {"resolve", "ignore"}:
        return ApiResponse.error("不支持的操作")
    ev.status = "resolved" if body.action == "resolve" else "ignored"
    ev.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    return ApiResponse.ok(message="操作成功")


@router.get("/logs")
async def logs(db: AsyncSessionDep, _: dict = Depends(get_current_admin), page: int = 1, page_size: int = 20):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    total = await db.scalar(select(func.count()).select_from(RiskActionLog)) or 0
    rows = (await db.execute(
        select(RiskActionLog).order_by(RiskActionLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return ApiResponse.ok(data={
        "items": [
            {"id": row.id, "action": row.action, "target": row.target, "reason": row.reason, "created_at": row.created_at}
            for row in rows
        ],
        "total": int(total),
    })


@router.post("/kick")
async def kick(body: KickRequest, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    if body.level == "hard":
        result = await emby.force_kick(body.session_id, body.device_id)
        ok = result["stopped"] or result["device_deleted"]
        reason = f"强制踢出(停止={result['stopped']},删设备={result['device_deleted']})"
    else:
        ok = await emby.kick_session(body.session_id)
        reason = "停止播放"
    if ok:
        await _log_action(db, "kick", body.session_id, reason)
    return ApiResponse.ok(data={"success": ok, "level": body.level})


@router.post("/ban")
async def ban(body: BanRequest, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    ok = await emby.ban_user(body.user_id)
    if ok:
        await _log_action(db, "ban", body.user_id, body.reason or "管理员封禁")
    return ApiResponse.ok(data={"success": ok})


@router.post("/unban")
async def unban(body: BanRequest, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    ok = await emby.unban_user(body.user_id)
    if ok:
        await _log_action(db, "unban", body.user_id, body.reason or "管理员解封")
    return ApiResponse.ok(data={"success": ok})


@router.get("/blacklist")
async def list_blacklist(db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    return ApiResponse.ok(data=await _get_blacklist(db))


@router.post("/blacklist")
async def add_blacklist(body: BlacklistRequest, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    items = await _get_blacklist(db)
    items.append(body.name)
    items = await _set_blacklist(db, items)
    return ApiResponse.ok(data=items, message=f"已加入黑名单: {body.name}")


@router.delete("/blacklist/{name}")
async def remove_blacklist(name: str, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    items = [x for x in await _get_blacklist(db) if x != name.strip().lower()]
    items = await _set_blacklist(db, items)
    return ApiResponse.ok(data=items, message=f"已移除: {name}")


@router.post("/sweep")
async def sweep(db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    blacklist = set(await _get_blacklist(db))
    if not blacklist:
        return ApiResponse.ok(data={"deleted": [], "deleted_count": 0, "total_devices": 0}, message="黑名单为空")

    devices = await emby.get_devices()
    if not devices:
        return ApiResponse.ok(data={"deleted": [], "deleted_count": 0, "total_devices": 0}, message="获取设备列表失败或无设备")

    deleted = []
    skipped = []
    for d in devices:
        app_name = str(d.get("AppName") or "").strip().lower()
        device_id = str(d.get("Id") or "")
        if not device_id or not app_name:
            continue
        if app_name in blacklist:
            ok = await emby.delete_device(device_id)
            if ok:
                deleted.append({"device_id": device_id, "app_name": app_name, "user": d.get("LastUserName", "")})
                await _log_action(db, "device_sweep", device_id, f"删除黑名单客户端 {app_name}")
            else:
                skipped.append({"device_id": device_id, "app_name": app_name, "reason": "删除失败"})

    return ApiResponse.ok(data={
        "deleted": deleted,
        "deleted_count": len(deleted),
        "skipped": skipped,
        "total_devices": len(devices),
    })


@router.post("/scan")
async def scan(db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    return ApiResponse.ok(data=await _scan_logic(db))


@router.get("/status")
async def concurrent_status(db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    sessions = await emby.get_sessions(active_only=True)
    await users_service._ensure_meta_loaded()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for s in sessions:
        if not s.get("NowPlayingItem"):
            continue
        uid = str(s.get("UserId") or "")
        grouped.setdefault(uid, []).append({
            "session_id": s.get("Id", ""),
            "client": s.get("Client", ""),
            "device_name": s.get("DeviceName", ""),
            "title": (s.get("NowPlayingItem") or {}).get("Name", ""),
            "user_name": s.get("UserName", ""),
        })
    rows = []
    for uid, items in grouped.items():
        meta = users_service._meta_cache.get(uid, {})
        max_c = int(meta.get("max_concurrent", 2) or 2)
        rows.append({
            "user_id": uid,
            "user_name": items[0].get("user_name", "") if items else "",
            "current": len(items),
            "max": max_c,
            "exceeded": len(items) > max_c,
            "sessions": items,
        })
    rows.sort(key=lambda x: (not x["exceeded"], -x["current"]))
    return ApiResponse.ok(data=rows)
